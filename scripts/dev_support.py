"""Configuração e proteção dos recursos de desenvolvimento."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]

def run(args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)

def docker_json(*args):
    return json.loads(subprocess.check_output(["docker", *args]))

class Environment:
    def __init__(self):
        path = ROOT / ".env"
        if not path.is_file():
            raise ValueError("Copie .env.example para .env e configure seus segredos.")
        if path.stat().st_mode & 0o077:
            raise ValueError("Proteja as credenciais com chmod 600 .env.")
        self.values = {}
        for line in path.read_text().splitlines():
            if line.strip() and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                self.values[key.strip()] = value.strip()
        for key in ["POSTGRES_PASSWORD", "SECRET_KEY"]:
            value = self.values.get(key, "")
            if len(value) < 24 or value.upper().startswith(("CHANGE", "INSECURE")):
                raise ValueError(f"Configure {key} com segredo local de pelo menos 24 caracteres.")
            if not re.fullmatch(r"[A-Za-z0-9_-]+", value):
                raise ValueError(f"Use caracteres URL-safe em {key}, conforme o template.")
        for key in ["POSTGRES_DB", "POSTGRES_USER", "COMPOSE_PROJECT_NAME"]:
            if not re.fullmatch(r"[a-z][a-z0-9_]*", self.values.get(key, "")):
                raise ValueError(f"Configure {key} com letras minúsculas, números e sublinhado.")
        for key in ["DB_PORT", "API_PORT", "FRONTEND_PORT"]:
            if not self.values.get(key, "").isdigit() or not 1024 <= int(self.values[key]) <= 65535:
                raise ValueError(f"Configure uma porta local válida em {key}.")
        self.env = dict(os.environ)
        self.env.update(self.values)
        self.env["SOURCE_COMMIT"] = self.values.get("SOURCE_COMMIT") or subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"]).decode().strip()
        self.command = ["docker", "compose", "--env-file", str(path),
                        "-p", self.values["COMPOSE_PROJECT_NAME"], "-f", str(ROOT / "compose.yml")]
        if (ROOT / "compose.local.yml").is_file():
            self.command += ["-f", str(ROOT / "compose.local.yml")]
        self.config = json.loads(subprocess.check_output(
            self.command + ["config", "--format", "json"], env=self.env))
        self.volume = self.config["volumes"]["postgres_data"]["name"]
        self.external = self.config["volumes"]["postgres_data"].get("external", False)
        self.lock_file = open("/tmp/lumina-volume-" + hashlib.sha256(self.volume.encode()).hexdigest() + ".lock", "a")
        try:
            fcntl.flock(self.lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("Outra operação do helper já controla este volume.")

    def compose(self, *args, **kwargs):
        return run(self.command + list(args), env=self.env, **kwargs)

    def container(self, service):
        return subprocess.check_output(
            self.command + ["ps", "-aq", service], env=self.env).decode().strip()

    def check_volume(self, initialize=False):
        own = self.container("db")
        ids = subprocess.check_output(["docker", "ps", "-q"]).decode().split()
        if ids:
            for item in docker_json("inspect", *ids):
                if not (own and item["Id"].startswith(own)) and any(m.get("Name") == self.volume for m in item["Mounts"]):
                    raise ValueError("Volume já usado por outro contêiner em execução.")
        exists = subprocess.run(["docker", "volume", "inspect", self.volume],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
        if self.external and not exists:
            raise ValueError("Volume externo não existe. Nenhum volume substituto será criado.")
        if not initialize:
            if not exists:
                raise ValueError("Banco ainda não preparado. Execute init no seu ambiente vazio.")
            image = self.config["services"]["db"]["image"]
            result = subprocess.run([
                "docker", "run", "--rm", "--read-only", "--network", "none",
                "--mount", f"type=volume,src={self.volume},dst=/data,readonly",
                "--entrypoint", "sh", image, "-c", "test -f /data/PG_VERSION && test \"$(cat /data/PG_VERSION)\" = 16"
            ])
            if result.returncode:
                raise ValueError("Cluster PostgreSQL 16 não confirmado no volume. Início recusado.")

    def start_db(self, initialize=False):
        self.check_volume(initialize)
        self.compose("create", "db")
        container = self.container("db")
        info = docker_json("inspect", container)[0]
        mounts = [m for m in info["Mounts"] if m["Destination"] == "/var/lib/postgresql/data"]
        if len(mounts) != 1 or mounts[0].get("Name") != self.volume:
            raise ValueError("Mount do banco diverge do volume esperado.")
        run(["docker", "start", container], stdout=subprocess.DEVNULL)
        for _ in range(60):
            ready = subprocess.run([
                "docker", "exec", container, "pg_isready", "-h", "127.0.0.1",
                "-U", self.values["POSTGRES_USER"], "-d", self.values["POSTGRES_DB"]
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if ready.returncode == 0:
                return container
            time.sleep(1)
        raise ValueError("PostgreSQL não ficou disponível.")

    def database_check(self, mode="ready"):
        self.compose("run", "--rm", "--no-deps", "-T", "api",
                     "python", "scripts/check_database.py", mode)
