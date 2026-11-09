"""Persistência após reinício de processo, sem recriar o volume exclusivo QA.

Requer QA_TEST_PASSWORD. Reinicia apenas os contêineres nomeados abaixo.
"""

import json
import os
import subprocess
import time
from pathlib import Path

import httpx


ROOT = Path(__file__).resolve().parent
fixture = json.loads((ROOT / "fixture-ids.json").read_text())
http_result = json.loads((ROOT / "http-results.json").read_text())
API_CONTAINER = "lumina_qa_20261031_2f7dbfe-api-1"
DB_CONTAINER = "lumina_qa_20261031_2f7dbfe-db-1"
DB_NAME = "lumina_qa_20261031_2f7dbfe_db"
VOLUME = "lumina_qa_20261031_2f7dbfe_pg16_data"
BASE = "http://127.0.0.1:18128"


def command(*args):
    return subprocess.run(args, capture_output=True, text=True, timeout=20, check=True).stdout.strip()


def snapshot():
    query = """SELECT json_build_object(
      'clinics',(SELECT count(*) FROM clinics),
      'patients',(SELECT count(*) FROM patients),
      'appointments',(SELECT count(*) FROM appointments),
      'grants',(SELECT count(*) FROM clinical_access_grants),
      'records',(SELECT count(*) FROM medical_records),
      'evolutions',(SELECT count(*) FROM clinical_evolutions)
    )::text"""
    raw = command("docker", "exec", DB_CONTAINER, "psql", "-X", "-Atq", "-U", "qa_clinic", "-d", DB_NAME, "-c", query)
    return json.loads(raw)


def wait_pg():
    for _ in range(40):
        status = subprocess.run(["docker", "exec", DB_CONTAINER, "pg_isready", "-U", "qa_clinic", "-d", DB_NAME],
                                capture_output=True, timeout=3)
        if status.returncode == 0:
            return
        time.sleep(0.5)
    raise RuntimeError("PostgreSQL exclusivo não voltou em 20 segundos")


def check_http():
    for _ in range(40):
        try:
            with httpx.Client(base_url=BASE, timeout=3, trust_env=False) as client:
                if client.get("/health").status_code != 200:
                    raise RuntimeError("health não respondeu 200")
                login = client.post("/api/v1/auth/login", data={
                    "username": fixture["users"]["dentist1"]["email"],
                    "password": os.environ["QA_TEST_PASSWORD"],
                })
                if login.status_code != 200:
                    raise RuntimeError(f"login HTTP {login.status_code}")
                headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
                patient = fixture["patients"]["shared"]
                record = client.get(f"/api/v1/patients/{patient}/record", headers=headers)
                evolutions = client.get(f"/api/v1/patients/{patient}/evolutions", headers=headers)
                return {
                    "health": 200,
                    "record_http": record.status_code,
                    "record_id": record.json().get("id"),
                    "history_http": evolutions.status_code,
                    "finalized_visible": any(item["id"] == http_result["finalized_evolution_id"] and item["status"] == "FINALIZED" for item in evolutions.json()),
                }
        except (httpx.HTTPError, RuntimeError):
            time.sleep(0.5)
    raise RuntimeError("API ou fluxo clínico não voltou em 20 segundos")


volume_id_before = command("docker", "volume", "inspect", "-f", "{{.Name}}", VOLUME)
before = snapshot()
command("docker", "restart", API_CONTAINER)
after_api = check_http()
after_api_sql = snapshot()
command("docker", "restart", DB_CONTAINER)
wait_pg()
after_db = check_http()
after_db_sql = snapshot()
volume_id_after = command("docker", "volume", "inspect", "-f", "{{.Name}}", VOLUME)
all_ok = (
    before == after_api_sql == after_db_sql
    and volume_id_before == volume_id_after
    and all(item["record_http"] == 200 and item["history_http"] == 200
            and item["record_id"] == http_result["shared_record_id"]
            and item["finalized_visible"] for item in (after_api, after_db))
)
result = {
    "id": "PG-persistence-api-db-restart", "requirement": "RF-024-CA06",
    "layer": "PostgreSQL/HTTP", "expected": "mesmas contagens, IDs e evolução após reinício da API e do PostgreSQL no mesmo volume",
    "observed": {"before": before, "after_api": after_api_sql, "after_db": after_db_sql,
                 "http_after_api": after_api, "http_after_db": after_db,
                 "volume_preserved": volume_id_before == volume_id_after},
    "result": "aprovado" if all_ok else "reprovado",
    "note": "Reinício de processos; não testou recriação de contêiner com volume preservado",
}
(ROOT / "persistence-result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
print(json.dumps(result, ensure_ascii=False))
