#!/usr/bin/env python3
"""Opera somente o ambiente candidato da API clinica, preservando outros projetos."""
import argparse
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / ".env.integration"
COMPOSE_FILE = ROOT / "compose.integration.yml"
LABEL = "clinical-integration"


def setup(args):
    if not re.fullmatch(r"lumina_prontuario_[a-z0-9_]+", args.project):
        raise ValueError("Projeto deve iniciar com lumina_prontuario_.")
    ports = [args.api_port, args.db_port]
    if len(set(ports)) != 2 or any(not 1024 <= p <= 65535 for p in ports):
        raise ValueError("Escolha duas portas locais distintas entre 1024 e 65535.")
    values = dict(COMPOSE_PROJECT_NAME=args.project, POSTGRES_DB="lumina_prontuario_integracao",
                  POSTGRES_USER="lumina_app", POSTGRES_PASSWORD=secrets.token_urlsafe(40),
                  JWT_SECRET=secrets.token_urlsafe(48), API_PORT=args.api_port, DB_PORT=args.db_port,
                  CORS_ORIGINS="http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000")
    # Criacao exclusiva: uma segunda execucao nunca troca senhas do volume existente.
    fd = os.open(ENV_FILE, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as output:
        output.write("".join(f"{key}={value}\n" for key, value in values.items()))
    print("Configuracao privada criada em .env.integration; nenhum banco foi alterado.")


def configuration():
    if not ENV_FILE.exists():
        raise ValueError("Execute setup antes de operar este ambiente.")
    values = dict(line.split("=", 1) for line in ENV_FILE.read_text().splitlines()
                  if line.strip() and not line.lstrip().startswith("#"))
    if not re.fullmatch(r"lumina_prontuario_[a-z0-9_]+", values.get("COMPOSE_PROJECT_NAME", "")):
        raise ValueError("Projeto fora do escopo de integracao clinica.")
    for key in ["POSTGRES_PASSWORD", "JWT_SECRET"]:
        if not re.fullmatch(r"[A-Za-z0-9_-]{32,}", values.get(key, "")) or values[key].startswith("GERADO_"):
            raise ValueError(f"Segredo invalido em {key}; use setup para um ambiente novo.")
    if values.get("POSTGRES_DB") != "lumina_prontuario_integracao" or values.get("POSTGRES_USER") != "lumina_app":
        raise ValueError("Banco/usuario devem pertencer a esta preparacao exclusiva.")
    ports = [int(values.get(key, "0")) for key in ["API_PORT", "DB_PORT"]]
    if len(set(ports)) != 2 or any(not 1024 <= p <= 65535 for p in ports):
        raise ValueError("Portas invalidas na configuracao local.")
    return values


def command(values, *args, **kwargs):
    env = os.environ.copy()
    env.update(values)  # A configuracao deste ambiente prevalece sobre o shell.
    env["SOURCE_COMMIT"] = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    return subprocess.run(["docker", "compose", "--env-file", str(ENV_FILE), "-p",
                           values["COMPOSE_PROJECT_NAME"], "-f", str(COMPOSE_FILE), *args],
                          cwd=ROOT, env=env, check=True, **kwargs)


def check_ownership(values):
    project = values["COMPOSE_PROJECT_NAME"]
    ids = subprocess.check_output(["docker", "ps", "-aq", "--filter",
                                   "label=com.docker.compose.project=" + project], text=True).split()
    if ids:
        for item in json.loads(subprocess.check_output(["docker", "inspect", *ids])):
            if item["Config"]["Labels"].get("lumina.delivery") != LABEL:
                raise ValueError("Projeto existente nao pertence a esta preparacao; preservado.")
    network = subprocess.run(["docker", "network", "inspect", project + "_default"],
                             capture_output=True, text=True)
    if network.returncode == 0:
        labels = json.loads(network.stdout)[0].get("Labels") or {}
        if labels.get("com.docker.compose.project") != project:
            raise ValueError("Rede existente sem propriedade reconhecida; preservada.")
    volume = project + "_integration_data"
    result = subprocess.run(["docker", "volume", "inspect", volume], capture_output=True, text=True)
    if result.returncode == 0:
        labels = json.loads(result.stdout)[0].get("Labels") or {}
        if labels.get("com.docker.compose.project") != project:
            raise ValueError("Volume existente sem propriedade reconhecida; preservado.")
        users = subprocess.check_output(["docker", "ps", "-aq", "--filter", "volume=" + volume], text=True).split()
        if set(users) - set(ids):
            raise ValueError("Volume usado por outro projeto; operacao recusada.")


def status(values):
    command(values, "ps")
    # Nao imprime tokens, credenciais nem o conteudo clinico do banco.
    for path in ["/health", "/openapi.json"]:
        with urllib.request.urlopen(f"http://127.0.0.1:{values['API_PORT']}{path}", timeout=10) as response:
            body = json.load(response)
            if path == "/health" and body.get("database") != "connected":
                raise ValueError("API sem conexao com o banco.")
            if path == "/openapi.json" and "/api/v1/clinical/patients" not in body.get("paths", {}):
                raise ValueError("A porta nao esta servindo a API clinica esperada.")
            print(f"HTTP {path}: {response.status}")
    print(f"API clinica: http://localhost:{values['API_PORT']}/docs")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["setup", "up", "status", "seed", "stop"])
    parser.add_argument("--project", default="lumina_prontuario_integracao")
    parser.add_argument("--api-port", type=int, default=18100)
    parser.add_argument("--db-port", type=int, default=55450)
    args = parser.parse_args()
    if args.action == "setup":
        setup(args)
        return
    values = configuration()
    check_ownership(values)
    if args.action == "up":
        # Schema SQL e aplicado pelo PostgreSQL somente ao volume NOVO e vazio.
        command(values, "up", "-d", "--build", "--wait", "--wait-timeout", "150")
        status(values)
    elif args.action == "status":
        status(values)
    elif args.action == "seed":
        # O SQL publicado exige banco sem cadastros e recusa reaplicacao.
        with (ROOT / "sql/seed_demo.sql").open("rb") as source:
            command(values, "exec", "-T", "db", "psql", "-X", "-v", "ON_ERROR_STOP=1",
                    "-U", values["POSTGRES_USER"], "-d", values["POSTGRES_DB"], stdin=source)
    else:
        command(values, "stop")  # Preserva os dados e nao possui comando de remocao.


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))
