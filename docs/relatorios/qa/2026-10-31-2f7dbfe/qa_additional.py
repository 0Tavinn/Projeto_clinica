"""Sondagens adicionais na API e no banco exclusivos da execução QA.

Requer QA_TEST_PASSWORD. Usa apenas IDs de qa_fixture.py e dados fictícios.
"""

import datetime as dt
import json
import os
import subprocess
from pathlib import Path

import httpx


ROOT = Path(__file__).resolve().parent
fixture = json.loads((ROOT / "fixture-ids.json").read_text())
API = "http://127.0.0.1:18128"
DB_CONTAINER = "lumina_qa_20261031_2f7dbfe-db-1"
DB_NAME = "lumina_qa_20261031_2f7dbfe_db"
PASSWORD = os.environ["QA_TEST_PASSWORD"]
results = []


def sql(statement):
    return subprocess.run(
        ["docker", "exec", DB_CONTAINER, "psql", "-X", "-Atq", "-U", "qa_clinic", "-d", DB_NAME, "-c", statement],
        capture_output=True, text=True, check=True, timeout=8,
    ).stdout.strip()


def record(case, requirement, layer, expected, observed, passed, note=""):
    results.append({"id": case, "requirement": requirement, "layer": layer,
                    "expected": expected, "observed": observed,
                    "result": "aprovado" if passed else "reprovado", "note": note})


def token(client, key):
    response = client.post("/api/v1/auth/login", data={
        "username": fixture["users"][key]["email"], "password": PASSWORD,
    })
    if response.status_code != 200:
        raise RuntimeError(f"login {key}: HTTP {response.status_code}")
    return response.json()


def call(client, method, path, access, payload=None):
    return client.request(method, path, headers={"Authorization": f"Bearer {access}"}, json=payload)


with httpx.Client(base_url=API, timeout=8, trust_env=False) as client:
    d1 = token(client, "dentist1")["access_token"]
    reception = token(client, "reception")["access_token"]

    # Ambos os pacientes são acessíveis; o appointment_id pertence ao outro.
    continuity = fixture["patients"]["continuity"]
    shared_appointment = fixture["appointments"]["shared_d1"]
    mismatch = call(client, "POST", "/api/v1/patients/evolutions", d1, {
        "patient_id": continuity, "appointment_id": shared_appointment,
        "description": "Vínculo incompatível fictício",
    })
    record("HTTP-cross-patient-appointment", "RF-024-CA02", "HTTP", "404 por vínculo incompatível", f"HTTP {mismatch.status_code}", mismatch.status_code == 404)

    other_appointment = fixture["appointments"]["other_clinic"]
    cross_clinic = call(client, "POST", "/api/v1/patients/evolutions", d1, {
        "patient_id": fixture["patients"]["shared"],
        "appointment_id": other_appointment,
        "description": "Outra clínica fictícia",
    })
    record("HTTP-cross-clinic-appointment", "RF-024-CA02", "HTTP", "404 por consulta de outra clínica", f"HTTP {cross_clinic.status_code}", cross_clinic.status_code == 404)

    start = (dt.datetime.fromisoformat(fixture["fixture_utc"]) - dt.timedelta(days=3)).isoformat()
    end = (dt.datetime.fromisoformat(fixture["fixture_utc"]) + dt.timedelta(days=1)).isoformat()
    filters = client.get("/api/v1/appointments", headers={"Authorization": f"Bearer {reception}"}, params={
        "start_date": start, "end_date": end,
        "patient_id": fixture["patients"]["shared"],
        "dentist_id": fixture["dentists"]["dentist1"],
        "status": "COMPLETED",
    })
    returned = [item["id"] for item in filters.json()] if filters.status_code == 200 else []
    record("HTTP-combined-filters", "RF-017", "HTTP", "apenas shared_d1 concluída", f"HTTP {filters.status_code}, IDs {returned}", filters.status_code == 200 and returned == [shared_appointment])

    # Recebe token ativo e inativa a mesma conta no banco de QA.
    inactive_id = fixture["users"]["inactive"]["id"]
    sql(f"UPDATE users SET is_active=true WHERE id={inactive_id}")
    inactive_login = token(client, "inactive")
    sql(f"UPDATE users SET is_active=false WHERE id={inactive_id}")
    after_inactive = call(client, "GET", "/api/v1/auth/me", inactive_login["access_token"])
    refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": inactive_login["refresh_token"]})
    record("HTTP-inactive-existing-token", "segurança", "HTTP", "401 após inativação", f"HTTP {after_inactive.status_code}", after_inactive.status_code == 401)
    record("HTTP-inactive-refresh", "segurança", "HTTP", "401 após inativação", f"HTTP {refresh.status_code}", refresh.status_code == 401)

    # Ausência com atendimento anterior válido da mesma dupla.
    clinic = fixture["clinics"]["a"]
    patient = fixture["patients"]["continuity"]
    dentist = fixture["dentists"]["dentist1"]
    no_show_id = int(sql(
        f"INSERT INTO appointments (clinic_id,patient_id,dentist_id,scheduled_at,duration_minutes,status,notes) "
        f"VALUES ({clinic},{patient},{dentist},now()-interval '4 days',30,'SCHEDULED','QA continuity no-show') RETURNING id"
    ))
    confirm = call(client, "PATCH", f"/api/v1/appointments/{no_show_id}/status", reception, {"status": "CONFIRMED"})
    absent = call(client, "PATCH", f"/api/v1/appointments/{no_show_id}/status", d1, {"status": "NO_SHOW"})
    access = call(client, "GET", f"/api/v1/patients/{patient}/record", d1)
    record("HTTP-no-show-with-continuity", "RN-031", "HTTP", "200 confirmado, 200 ausência, 200 leitura mantida", f"HTTP {confirm.status_code}/{absent.status_code}/{access.status_code}", (confirm.status_code, absent.status_code, access.status_code) == (200,200,200))

    audit_count = int(sql("SELECT count(*) FROM audit_logs"))
    record("SPRINT-audit-events", "RN-034/Sprint 7", "SQL/HTTP", "eventos registrados para operações essenciais", f"audit_logs={audit_count} após operações de Agenda e prontuário", audit_count > 0, "A tabela existe no esquema; nenhuma rota de auditoria no OpenAPI")

    # Evidência da confirmação/conclusão verificada diretamente no banco.
    grant = sql(f"SELECT (confirmed_by_user_id IS NOT NULL)::int || '|' || (care_occurred_at IS NOT NULL)::int || '|' || (care_recorded_at IS NOT NULL)::int || '|' || (care_recorded_by_user_id IS NOT NULL)::int FROM clinical_access_grants WHERE appointment_id={shared_appointment}")
    record("PG-confirm-care-evidence", "RN-031", "SQL", "quatro campos de procedência presentes", grant, grant == "1|1|1|1")

(ROOT / "additional-results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
print(f"additional cases={len(results)} approved={sum(r['result']=='aprovado' for r in results)} failed={sum(r['result']=='reprovado' for r in results)}")
for result in results:
    print(result["id"], result["observed"], result["result"])
