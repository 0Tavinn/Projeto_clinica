#!/usr/bin/env python3
"""Ponto único de operação do ambiente local, sem comandos de remoção de dados."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import urllib.request

from dev_support import Environment, ROOT
from dev_backup import backup, restore_test

def status(env):
    env.compose("ps", "-a")
    api = env.container("api")
    if not api:
        raise ValueError("API não está criada.")
    info = json.loads(subprocess.check_output(["docker", "inspect", api]))[0]
    if not info["State"]["Running"]:
        raise ValueError("API parada. Execute up.")
    subprocess.run(["docker", "exec", api, "python", "scripts/check_database.py"], check=True)
    for port, path in [(env.values["API_PORT"], "/health"), (env.values["FRONTEND_PORT"], "/")]:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=5) as response:
            print(f"HTTP {port}{path}: {response.status}")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["init", "up", "status", "stop", "seed-demo", "backup", "restore-test"])
    parser.add_argument("backup_file", nargs="?")
    args = parser.parse_args()
    env = Environment()
    if args.command in {"init", "up"}:
        if args.command == "init" and env.external:
            raise ValueError("init recusado em volume externo. Use up para banco preparado.")
        env.compose("build", "api", "frontend")
        env.start_db(initialize=args.command == "init")
        if args.command == "init":
            env.database_check("empty")
            env.compose("run", "--rm", "--no-deps", "-T", "api", "alembic", "upgrade", "a6e8f0b2c4d6")
        env.database_check()
        env.compose("up", "-d", "--no-deps", "--wait", "--wait-timeout", "120", "api", "frontend")
        status(env)
    elif args.command == "status":
        status(env)
    elif args.command == "stop":
        env.compose("stop", "frontend", "api", "db")
    elif args.command == "seed-demo":
        env.start_db()
        env.database_check()
        container = env.container("db")
        # O seed SQL publicado contém a proteção transacional contra banco preenchido.
        with (ROOT / "backend/database/seed_demo.sql").open("rb") as source:
            env_run_sql(env, container, source)
    elif args.command == "backup":
        env.start_db()
        env.database_check()
        active = []
        for service in ["frontend", "api"]:
            container = env.container(service)
            if container and json.loads(subprocess.check_output(["docker", "inspect", container]))[0]["State"]["Running"]:
                active.append(service)
        if active:
            env.compose("stop", *active)
        try:
            print(backup(env))
        finally:
            if active:
                env.compose("start", *active)
    else:
        if not args.backup_file:
            raise ValueError("Informe o caminho do backup produzido pelo helper.")
        restore_test(env, Path(args.backup_file).resolve())

def env_run_sql(env, container, source):
    subprocess.run(["docker", "exec", "-i", container, "psql", "-X", "-v", "ON_ERROR_STOP=1",
                    "-U", env.values["POSTGRES_USER"], "-d", env.values["POSTGRES_DB"]],
                   stdin=source, check=True)

if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError) as error:
        sys.exit(str(error))
    except subprocess.CalledProcessError as error:
        sys.exit(f"Operação interrompida (código {error.returncode}). Consulte a etapa que falhou.")
