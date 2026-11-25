"""Backup protegido e restauração de teste em destino exclusivo."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import time

from dev_support import ROOT, run

TABLES = ["clinics", "users", "patients", "dentists", "appointments", "medical_records",
          "clinical_evolutions", "clinical_access_links", "clinical_access_events", "audit_logs"]

def query(container, user, database, sql):
    return subprocess.check_output(["docker", "exec", container, "psql", "-X", "-At",
                                   "-v", "ON_ERROR_STOP=1", "-U", user, "-d", database, "-c", sql])

def data_digest(container, user, database):
    result = subprocess.check_output(["docker", "exec", container, "pg_dump", "-U", user, "-d",
                                      database, "--data-only", "--no-owner", "--no-privileges"])
    result = b"\n".join(line for line in result.splitlines()
                        if not line.startswith((b"\\restrict ", b"\\unrestrict ")))
    return hashlib.sha256(result).hexdigest()

def counts(container, user, database):
    sql = "BEGIN READ ONLY; " + " UNION ALL ".join(
        "SELECT '" + table + "',count(*) FROM public." + table for table in TABLES) + "; COMMIT;"
    return query(container, user, database, sql).decode()

def backup(env):
    container, user, database = env.container("db"), env.values["POSTGRES_USER"], env.values["POSTGRES_DB"]
    directory = ROOT / ".local/backups" / (datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + secrets.token_hex(3))
    directory.mkdir(parents=True, mode=0o700)
    os.chmod(directory.parent, 0o700)
    target = directory / "reference.dump"
    before = data_digest(container, user, database)
    with target.open("wb") as output:
        os.chmod(target, 0o600)
        run(["docker", "exec", container, "pg_dump", "-U", user, "-d", database, "-Fc"], stdout=output)
    globals_file = directory / "roles-without-passwords.sql"
    with globals_file.open("wb") as output:
        os.chmod(globals_file, 0o600)
        run(["docker", "exec", container, "pg_dumpall", "-U", user,
             "--globals-only", "--no-role-passwords"], stdout=output)
    after = data_digest(container, user, database)
    if before != after:
        raise ValueError("Houve escrita durante a conferência. Repita sem outros escritores.")
    info = json.loads(subprocess.check_output(["docker", "inspect", container]))[0]
    manifest = dict(sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                    data_sequence_sha256=after, counts=counts(container, user, database),
                    database=database, user=user, image=info["Image"],
                    revision=query(container, user, database, "SELECT version_num FROM alembic_version").decode().strip(),
                    restore_tested=False)
    path = directory / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2)); os.chmod(path, 0o600)
    return target

def restore_test(env, target):
    manifest_path = target.parent / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if hashlib.sha256(target.read_bytes()).hexdigest() != manifest["sha256"]:
        raise ValueError("Hash do backup diverge do manifesto.")
    name, user = "lumina_restore_" + secrets.token_hex(8), manifest["user"]
    # Destino sem volume do usuário, sem rede e sem porta.
    run(["docker", "run", "-d", "--name", name, "--network", "none",
         "-e", "POSTGRES_USER=" + user, "-e", "POSTGRES_DB=restore_test",
         "-e", "POSTGRES_PASSWORD=" + secrets.token_urlsafe(32), manifest["image"]],
        stdout=subprocess.DEVNULL)
    try:
        for _ in range(60):
            if subprocess.run(["docker", "exec", name, "pg_isready", "-h", "127.0.0.1", "-U", user],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
                break
            time.sleep(1)
        else:
            raise ValueError("Restauração descartável não ficou disponível.")
        with target.open("rb") as source:
            run(["docker", "exec", "-i", name, "pg_restore", "-U", user, "-d", "restore_test",
                 "--exit-on-error"], stdin=source)
        if data_digest(name, user, "restore_test") != manifest["data_sequence_sha256"]:
            raise ValueError("Dados/sequências restaurados divergem.")
        if counts(name, user, "restore_test") != manifest["counts"]:
            raise ValueError("Contagens restauradas divergem.")
        revision = query(name, user, "restore_test", "SELECT version_num FROM alembic_version").decode().strip()
        if revision != manifest["revision"]:
            raise ValueError("Revisão restaurada diverge.")
        with (ROOT / "backend/database/check_clinical_schema.sql").open("rb") as source:
            result = subprocess.run(["docker", "exec", "-i", name, "psql", "-X", "-v", "ON_ERROR_STOP=1",
                                     "-U", user, "-d", "restore_test"], stdin=source,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (target.parent / "restore-checks.log").write_bytes(result.stdout)
        result.check_returncode()
        manifest["restore_tested"] = True
        manifest["restore_container_removed"] = name
        manifest["restore_time"] = datetime.datetime.now().isoformat()
        manifest_path.write_text(json.dumps(manifest, indent=2))
        print("OK: restauração conferida por dados, sequências, contagens, revisão e garantias SQL.")
    finally:
        run(["docker", "rm", "-f", "-v", name], stdout=subprocess.DEVNULL)
