#!/usr/bin/env python3
"""Cria configuração local isolada, sem escrever no banco."""
import argparse
import os
from pathlib import Path
import re
import secrets

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--project", default="lumina_dev_" + secrets.token_hex(4))
parser.add_argument("--api-port", type=int, default=8000)
parser.add_argument("--frontend-port", type=int, default=8080)
parser.add_argument("--db-port", type=int, default=55432)
args = parser.parse_args()
if not re.fullmatch(r"[a-z][a-z0-9_]*", args.project):
    parser.error("Use letras minúsculas, números e sublinhado no projeto.")
ports = [args.api_port, args.frontend_port, args.db_port]
if len(set(ports)) != 3 or any(not 1024 <= p <= 65535 for p in ports):
    parser.error("Escolha três portas locais distintas, entre 1024 e 65535.")
# Configura somente um ambiente novo; o O_EXCL abaixo preserva .env existente.
values = dict(APPOINTMENT_CONFLICT_ENGINE="sequential", COMPOSE_PROJECT_NAME=args.project, POSTGRES_DB="lumina_dev", POSTGRES_USER="lumina_app",
              POSTGRES_PASSWORD=secrets.token_urlsafe(48), SECRET_KEY=secrets.token_urlsafe(48),
              API_PORT=args.api_port, FRONTEND_PORT=args.frontend_port, DB_PORT=args.db_port)
try:
    fd = os.open(ROOT / ".env", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
except FileExistsError:
    parser.exit(1, ".env já existe e foi preservado.\n")
with os.fdopen(fd, "w") as output:
    output.write("\n".join(f"{k}={v}" for k, v in values.items()) + "\n")
print(f"Configuração local criada para {args.project}. Segredos protegidos em .env.")
