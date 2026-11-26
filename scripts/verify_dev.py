#!/usr/bin/env python3
"""Reproduz a operação compartilhável em cópia limpa e recursos descartáveis."""
import io
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
OVERLAY = [
    "compose.yml", ".env.example", ".gitignore", "README.md",
    "backend/Dockerfile", "backend/.dockerignore", "backend/scripts/check_database.py",
    "frontend/Dockerfile", "frontend/.dockerignore", "frontend/nginx.conf",
    "scripts/dev.py", "scripts/dev_support.py", "scripts/dev_backup.py", "scripts/setup_dev.py",
]
def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]

def main():
    project = "lumina_devcheck_" + secrets.token_hex(6)
    output = ROOT / ".local/test-runs" / project
    output.mkdir(parents=True, mode=0o700)
    existing = subprocess.check_output(["docker", "ps", "-aq", "--filter", "label=com.docker.compose.project=" + project]).strip()
    if existing or subprocess.run(["docker", "volume", "inspect", project + "_postgres_data"],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
        raise RuntimeError("Nome descartável já existe.")
    with tempfile.TemporaryDirectory(prefix="lumina-dev-clean-") as tmp:
        target = Path(tmp)
        archive = subprocess.check_output(["git", "-C", str(ROOT), "archive", "HEAD", "backend", "frontend", "README.md", ".gitignore"])
        with tarfile.open(fileobj=io.BytesIO(archive)) as data:
            data.extractall(target, filter="data")
        for name in OVERLAY:
            dest = target / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, dest)
        values = dict(COMPOSE_PROJECT_NAME=project, POSTGRES_DB="lumina_dev", POSTGRES_USER="lumina_app",
                      POSTGRES_PASSWORD=secrets.token_urlsafe(40), SECRET_KEY=secrets.token_urlsafe(48),
                      API_PORT=str(free_port()), FRONTEND_PORT=str(free_port()), DB_PORT=str(free_port()),
                      SOURCE_COMMIT=subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"]).decode().strip())
        env_file = target / ".env"
        subprocess.run(["python3", str(target / "scripts/setup_dev.py"), "--project", project,
                        "--api-port", values["API_PORT"], "--frontend-port", values["FRONTEND_PORT"],
                        "--db-port", values["DB_PORT"]], check=True)
        # A cópia limpa é uma exportação sem .git. O SHA vem do checkout de origem.
        with env_file.open("a") as output_env:
            output_env.write("SOURCE_COMMIT=" + values["SOURCE_COMMIT"] + "\n")
        command = ["python3", str(target / "scripts/dev.py")]
        compose = ["docker", "compose", "--env-file", str(env_file), "-p", project, "-f", str(target / "compose.yml")]
        def execute(name, args, expected=0):
            result = subprocess.run(args, cwd=target, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            (output / (name + ".log")).write_bytes(result.stdout)
            if (result.returncode == 0) != (expected == 0):
                raise RuntimeError(f"Etapa {name} falhou. Consulte {output / (name + '.log')}")
            print("OK:", name, flush=True)
        try:
            # Template sem segredos deve falhar antes de criar recursos.
            real = env_file.read_text()
            env_file.write_text((ROOT / ".env.example").read_text())
            execute("reject-template", command + ["status"], expected=1)
            env_file.write_text(real)
            execute("reject-setup-overwrite", ["python3", str(target / "scripts/setup_dev.py")], expected=1)
            execute("init-empty", command + ["init"])
            execute("up", command + ["up"])
            execute("status", command + ["status"])
            execute("seed-demo", command + ["seed-demo"])
            execute("reject-seed-filled", command + ["seed-demo"], expected=1)
            execute("reject-init-filled", command + ["init"], expected=1)
            execute("backup", command + ["backup"])
            dump = next((target / ".local/backups").glob("*/reference.dump"))
            execute("restore-test", command + ["restore-test", str(dump)])
            # Os backups da cópia contêm somente o seed fictício e são descartados.
            execute("stop", command + ["stop"])
            execute("up-after-stop", command + ["up"])
            # Divergência criada exclusivamente no banco QA para verificar a recusa.
            db = subprocess.check_output(compose + ["ps", "-q", "db"], cwd=target).decode().strip()
            execute("corrupt-qa-revision", ["docker", "exec", db, "psql", "-X", "-v", "ON_ERROR_STOP=1",
                    "-U", values["POSTGRES_USER"], "-d", values["POSTGRES_DB"],
                    "-c", "UPDATE alembic_version SET version_num='unknown_qa'"])
            execute("reject-unknown-origin", command + ["status"], expected=1)
            (output / "result.json").write_text(json.dumps(dict(project=project,passed=True,
                source=values["SOURCE_COMMIT"],postgres="16",seed="fictício",resources_removed_on_exit=True),indent=2))
        finally:
            # O nome aleatório foi conferido livre e é exclusivo desta execução.
            subprocess.run(compose + ["down", "--remove-orphans"], cwd=target, check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["docker", "volume", "rm", project + "_postgres_data"], check=True,
                           stdout=subprocess.DEVNULL)
            for service in ["api", "frontend"]:
                subprocess.run(["docker", "image", "rm", project + "-" + service + ":latest"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("Evidências:", output)

if __name__ == "__main__":
    main()
