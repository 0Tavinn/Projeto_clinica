#!/usr/bin/env python3
"""Testa a sessão com PostgreSQL/Uvicorn exclusivos; não opera volumes da equipe."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import time
import urllib.request
from session_probe import SessionProbe

ROOT = Path(__file__).resolve().parents[1]
LABEL = "lumina.qa=session"


def run(*args, **kwargs):
    return subprocess.run(list(args), check=True, **kwargs)


def docker_inventory():
    # IDs permitem verificar que nenhum serviço alheio foi reiniciado ou removido.
    return sorted(subprocess.check_output(["docker", "ps", "-aq"], text=True).split())


def wait_until(check):
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        try:
            if check():
                return
        except (OSError, ValueError):
            pass
        time.sleep(0.3)
    raise RuntimeError("Ambiente exclusivo não ficou pronto no prazo.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    unique = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S") + secrets.token_hex(3)
    prefix = "lumina_qa_session_" + unique
    network, db_name, api_name = prefix + "_net", prefix + "_db", prefix + "_api"
    database = prefix
    image = "lumina-qa-session:" + unique
    env_file = output / ".runtime.env"
    password = secrets.token_urlsafe(32)
    before = docker_inventory()
    env_file.write_text("\n".join([
        "POSTGRES_USER=qa", "POSTGRES_DB=" + database, "POSTGRES_PASSWORD=" + password,
        "DATABASE_URL=postgresql+psycopg://qa:" + password + "@db:5432/" + database,
        "JWT_SECRET=" + secrets.token_urlsafe(48),
        "CORS_ORIGINS=http://localhost:5173,http://localhost:3000", "LUMINA_SESSION_PG=1", ""]))
    env_file.chmod(0o600)
    created, network_created, built = [], False, False
    results = {"base_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()}
    try:
        with (output / "build.log").open("w") as log:
            run("docker", "build", "-t", image, str(ROOT), stdout=log, stderr=subprocess.STDOUT)
        built = True
        print("Build da candidata concluído.", flush=True)
        run("docker", "network", "create", "--label", LABEL, network, stdout=subprocess.DEVNULL)
        network_created = True
        run("docker", "run", "-d", "--name", db_name, "--label", LABEL, "--network", network,
            "--network-alias", "db", "--env-file", str(env_file), "--tmpfs", "/var/lib/postgresql/data",
            "postgres:16-alpine", stdout=subprocess.DEVNULL)
        created.append(db_name)
        def ready_database():
            # Consultar também SQL evita confundir o servidor temporário do init com o definitivo.
            result = subprocess.run(["docker", "exec", db_name, "sh", "-c",
                'PGPASSWORD="$POSTGRES_PASSWORD" exec psql -h 127.0.0.1 '
                '-U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "SELECT 1"'],
                capture_output=True, text=True)
            return result.returncode == 0 and result.stdout.strip() == "1"
        wait_until(ready_database)
        for filename in ["schema.sql", "seed_demo.sql"]:
            with (ROOT / "sql" / filename).open("rb") as source, (output / (filename + ".log")).open("w") as log:
                run("docker", "exec", "-i", db_name, "psql", "-X", "-U", "qa", "-d", database,
                    "-v", "ON_ERROR_STOP=1", stdin=source, stdout=log, stderr=subprocess.STDOUT)
        print("PostgreSQL exclusivo preparado com dados fictícios.", flush=True)
        with (output / "pytest.log").open("w") as log:
            run("docker", "run", "--rm", "--label", LABEL, "--network", network, "--env-file", str(env_file),
                image, "python", "-m", "pytest", "-q", "-p", "no:cacheprovider", "--disable-warnings", "--tb=short",
                stdout=log, stderr=subprocess.STDOUT)
        print((output / "pytest.log").read_text()[-1200:], flush=True)
        run("docker", "run", "-d", "--name", api_name, "--label", LABEL, "--network", network,
            "--env-file", str(env_file), "-p", "127.0.0.1::8000", image, stdout=subprocess.DEVNULL)
        created.append(api_name)
        ports = json.loads(subprocess.check_output(["docker", "inspect", "--format", "{{json .NetworkSettings.Ports}}", api_name], text=True))
        base = "http://127.0.0.1:" + ports["8000/tcp"][0]["HostPort"]
        def health():
            with urllib.request.urlopen(base + "/health", timeout=2) as response:
                return response.status == 200
        wait_until(health)
        def restart():
            nonlocal base
            previous = base
            run("docker", "restart", api_name, stdout=subprocess.DEVNULL)
            # A publicação com porta aleatória pode mudar após docker restart.
            bindings = json.loads(subprocess.check_output([
                "docker", "inspect", "--format", "{{json .NetworkSettings.Ports}}", api_name], text=True))
            base = "http://127.0.0.1:" + bindings["8000/tcp"][0]["HostPort"]
            probe.base = base
            results["restart_changed_port"] = previous != base
            wait_until(health)
        probe = SessionProbe(base)
        results["http_cases"] = probe.exercise(restart)
        results["http_passed"] = len(results["http_cases"])
        with (output / "api.log").open("w") as log:
            run("docker", "logs", api_name, stdout=log, stderr=subprocess.STDOUT)
        results["postgres"] = subprocess.check_output([
            "docker", "exec", db_name, "psql", "-X", "-U", "qa", "-d", database,
            "-Atc", "SHOW server_version"], text=True).strip()
        results["result"] = "passed"
        print("Sondagens HTTP reais aprovadas:", results["http_passed"], flush=True)
    finally:
        # Remove somente os recursos com nomes únicos que esta execução criou.
        for container in reversed(created):
            run("docker", "rm", "-f", container, stdout=subprocess.DEVNULL)
        if network_created:
            run("docker", "network", "rm", network, stdout=subprocess.DEVNULL)
        if built:
            run("docker", "image", "rm", image, stdout=subprocess.DEVNULL)
        env_file.unlink(missing_ok=True)
        results["containers_preserved"] = docker_inventory() == before
        results["cleanup_complete"] = not any(prefix in name for name in subprocess.check_output(
            ["docker", "ps", "-a", "--format", "{{.Names}}"], text=True).splitlines())
        results["source_hashes"] = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for base in [ROOT / "app", ROOT / "tests", ROOT / "scripts"] for p in sorted(base.rglob("*.py"))}
        (output / "result.json").write_text(json.dumps(results, indent=2) + "\n")
        print("Recursos exclusivos removidos; serviços anteriores preservados:", results["containers_preserved"], flush=True)


if __name__ == "__main__":
    main()
