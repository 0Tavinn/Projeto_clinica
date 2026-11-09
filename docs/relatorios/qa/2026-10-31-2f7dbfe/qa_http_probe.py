"""Sondagens HTTP com dados fictícios para o Compose exclusivo de QA.

Requer QA_TEST_PASSWORD no ambiente, sem registrar senha nem tokens.
Execute somente contra http://127.0.0.1:18128 e após qa_fixture.py.
"""

import datetime as dt
import json
import os
import time
from pathlib import Path

import httpx


ROOT = Path(__file__).resolve().parent
FIXTURE = json.loads((ROOT / "fixture-ids.json").read_text())
BASE = os.environ.get("QA_API_BASE", "http://127.0.0.1:18128")
if BASE != "http://127.0.0.1:18128":
    raise RuntimeError("Destino diferente da API exclusiva de QA")
PASSWORD = os.environ["QA_TEST_PASSWORD"]
RESULTS = []


def ids(group, key):
    return FIXTURE[group][key]


def add(case, requirement, response, expected, *, field=None, value=None, note=""):
    observed = response.status_code
    passed = observed in (expected if isinstance(expected, tuple) else (expected,))
    payload = response.json()
    if field is not None and passed:
        passed = payload.get(field) == value
    if observed >= 400 and passed:
        passed = isinstance(payload.get("error"), dict) and all(
            key in payload["error"] for key in ("code", "message", "details")
        )
    RESULTS.append({
        "id": case,
        "requirement": requirement,
        "layer": "HTTP",
        "expected": f"HTTP {expected}" + (f", {field}={value}" if field else ""),
        "observed": f"HTTP {observed}" + (f", {field}={payload.get(field)}" if field and isinstance(payload, dict) else ""),
        "result": "aprovado" if passed else "reprovado",
        "note": note,
    })
    return payload


def req(client, method, path, user=None, **kwargs):
    headers = {"Authorization": f"Bearer {TOKENS[user]}"} if user else {}
    return client.request(method, path, headers=headers, **kwargs)


def login(client, key):
    email = ids("users", key)["email"]
    response = client.post("/api/v1/auth/login", data={"username": email, "password": PASSWORD})
    if response.status_code == 429:
        add("AUTH-configured-limit", "configuração de sessão", response, 200,
            note="LOGIN_RATE_LIMIT=100/minute no contêiner, mas o limitador fixa 5/minute")
        time.sleep(61)
        response = client.post("/api/v1/auth/login", data={"username": email, "password": PASSWORD})
    payload = add(f"AUTH-{key}", "autenticação", response, 401 if key == "inactive" else 200)
    if response.status_code == 200:
        TOKENS[key] = payload["access_token"]
        if key == "dentist1":
            refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": payload["refresh_token"]})
            add("AUTH-refresh", "sessão", refresh, 200)


TOKENS = {}
care_at = (dt.datetime.now(dt.timezone(dt.timedelta(hours=-3))) - dt.timedelta(minutes=5)).isoformat()
future_care = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1)).isoformat()

with httpx.Client(base_url=BASE, timeout=12, trust_env=False) as client:
    for key in FIXTURE["users"]:
        login(client, key)

    shared = ids("patients", "shared")
    shared_d1 = ids("appointments", "shared_d1")
    shared_d2 = ids("appointments", "shared_d2")

    add("AUTH-no-token", "RF-023", req(client, "GET", f"/api/v1/patients/{shared}/record"), 401)
    add("AGENDA-list-admin", "RF-017", req(client, "GET", "/api/v1/appointments", "admin"), 200)
    own_list = req(client, "GET", "/api/v1/appointments", "dentist1")
    own = add("AGENDA-list-own", "RF-017", own_list, 200)
    RESULTS.append({"id": "AGENDA-own-filter", "requirement": "RF-017", "layer": "HTTP",
                    "expected": "somente consultas do dentista1", "observed": f"{len(own)} consultas",
                    "result": "aprovado" if all(item["dentist_id"] == ids("dentists", "dentist1") for item in own) else "reprovado", "note": ""})
    add("AGENDA-filter-status", "RF-017", req(client, "GET", "/api/v1/appointments?status=CONFIRMED", "reception"), 200)
    add("AGENDA-other-dentist-detail", "RF-017", req(client, "GET", f"/api/v1/appointments/{shared_d2}", "dentist1"), 404)
    add("AGENDA-invalid-period", "RF-017", req(client, "GET", "/api/v1/appointments?start_date=2026-11-03T12%3A00%3A00Z&end_date=2026-11-02T12%3A00%3A00Z", "reception"), 422)

    add("CLINICAL-admin", "RF-023-CA03", req(client, "GET", f"/api/v1/patients/{shared}/record", "admin"), 403)
    add("CLINICAL-reception", "RF-023-CA03", req(client, "GET", f"/api/v1/patients/{shared}/record", "reception"), 403)
    add("CLINICAL-no-profile", "RF-023", req(client, "GET", f"/api/v1/patients/{shared}/record", "no_profile"), 403)
    add("CLINICAL-other-clinic", "RF-023-CA03", req(client, "GET", f"/api/v1/patients/{shared}/record", "dentist_other_clinic"), 403)
    add("CLINICAL-no-origin", "RF-023", req(client, "GET", f"/api/v1/patients/{shared}/record", "dentist1"), 403)
    add("CLINICAL-legacy-no-proof", "RN-031", req(client, "GET", f"/api/v1/patients/{ids('patients','legacy')}/record", "dentist1"), 403)

    add("AGENDA-direct-completion", "RN-031", req(client, "PATCH", f"/api/v1/appointments/{shared_d1}/status", "dentist1", json={"status": "COMPLETED", "care_occurred_at": care_at}), 422)
    for key in ("shared_d1", "shared_d2"):
        add(f"AGENDA-confirm-{key}", "RN-031", req(client, "PATCH", f"/api/v1/appointments/{ids('appointments',key)}/status", "reception", json={"status": "CONFIRMED"}), 200, field="status", value="CONFIRMED")
    add("AGENDA-repeat-confirm", "RN-031", req(client, "PATCH", f"/api/v1/appointments/{shared_d1}/status", "reception", json={"status": "CONFIRMED"}), 422)
    add("AGENDA-complete-admin", "RN-031", req(client, "PATCH", f"/api/v1/appointments/{shared_d1}/status", "admin", json={"status": "COMPLETED", "care_occurred_at": care_at}), 403)
    add("AGENDA-complete-reception", "RN-031", req(client, "PATCH", f"/api/v1/appointments/{shared_d1}/status", "reception", json={"status": "COMPLETED", "care_occurred_at": care_at}), 403)
    add("AGENDA-complete-other-dentist", "RN-031", req(client, "PATCH", f"/api/v1/appointments/{shared_d1}/status", "dentist2", json={"status": "COMPLETED", "care_occurred_at": care_at}), 404)
    add("AGENDA-complete-no-time", "RN-031", req(client, "PATCH", f"/api/v1/appointments/{shared_d1}/status", "dentist1", json={"status": "COMPLETED"}), 422)
    add("AGENDA-complete-no-zone", "RN-031", req(client, "PATCH", f"/api/v1/appointments/{shared_d1}/status", "dentist1", json={"status": "COMPLETED", "care_occurred_at": "2026-10-30T10:00:00"}), 422)
    add("AGENDA-complete-future", "RN-031", req(client, "PATCH", f"/api/v1/appointments/{shared_d1}/status", "dentist1", json={"status": "COMPLETED", "care_occurred_at": future_care}), 422)
    add("AGENDA-complete-status", "RN-031", req(client, "PATCH", f"/api/v1/appointments/{shared_d1}/status", "dentist1", json={"status": "COMPLETED", "care_occurred_at": care_at}), 200, field="status", value="COMPLETED")
    add("AGENDA-repeat-complete", "RN-031", req(client, "PATCH", f"/api/v1/appointments/{shared_d1}/status", "dentist1", json={"status": "COMPLETED", "care_occurred_at": care_at}), 422)

    record = req(client, "GET", f"/api/v1/patients/{shared}/record", "dentist1")
    add("RECORD-general-notes", "RF-023-CA03", record, 200, field="general_notes", value="Observação geral fictícia QA")
    add("RECORD-admin-after-proof", "RF-023-CA03", req(client, "GET", f"/api/v1/patients/{shared}/record", "admin"), 403)
    add("RECORD-reception-after-proof", "RF-023-CA03", req(client, "GET", f"/api/v1/patients/{shared}/record", "reception"), 403)

    draft1 = add("DRAFT-own-create", "RF-024-CA01", req(client, "POST", "/api/v1/patients/evolutions", "dentist1", json={"patient_id": shared, "appointment_id": shared_d1, "description": "Texto fictício D1"}), 201, field="status", value="DRAFT")
    draft2 = add("DRAFT-other-author-create", "RF-024-CA01", req(client, "POST", "/api/v1/patients/evolutions", "dentist2", json={"patient_id": shared, "appointment_id": shared_d2, "description": "Texto fictício D2"}), 201, field="status", value="DRAFT")
    evolution1 = draft1.get("id")
    evolution2 = draft2.get("id")
    add("DRAFT-duplicate-appointment", "RF-024-CA09", req(client, "POST", "/api/v1/patients/evolutions", "dentist1", json={"patient_id": shared, "appointment_id": shared_d1, "description": "Duplicata fictícia"}), 409)
    add("DRAFT-wrong-dentist", "RF-024-CA02", req(client, "POST", "/api/v1/patients/evolutions", "dentist1", json={"patient_id": shared, "appointment_id": shared_d2, "description": "Vínculo incompatível"}), 404)
    add("DRAFT-wrong-patient", "RF-024-CA02", req(client, "POST", "/api/v1/patients/evolutions", "dentist1", json={"patient_id": ids("patients", "cancel"), "appointment_id": shared_d1, "description": "Vínculo incompatível"}), 403)
    add("DRAFT-other-clinic", "RF-024-CA07", req(client, "POST", "/api/v1/patients/evolutions", "dentist_other_clinic", json={"patient_id": shared, "appointment_id": shared_d1, "description": "Outra clínica"}), 403)
    add("DRAFT-admin", "RF-024-CA07", req(client, "POST", "/api/v1/patients/evolutions", "admin", json={"patient_id": shared, "description": "Admin não pode"}), 403)
    add("DRAFT-reception", "RF-024-CA07", req(client, "POST", "/api/v1/patients/evolutions", "reception", json={"patient_id": shared, "description": "Recepção não pode"}), 403)

    listing1 = add("HISTORY-d1-draft-private", "RF-023-CA05", req(client, "GET", f"/api/v1/patients/{shared}/evolutions", "dentist1"), 200)
    RESULTS.append({"id": "HISTORY-d1-excludes-d2", "requirement": "RF-023-CA05", "layer": "HTTP", "expected": "D1 vê apenas seu rascunho", "observed": f"IDs {[x['id'] for x in listing1]}", "result": "aprovado" if {x["id"] for x in listing1} == {evolution1} else "reprovado", "note": ""})
    add("DRAFT-other-author-edit", "RF-024-CA03", req(client, "PATCH", f"/api/v1/patients/evolutions/{evolution1}/draft", "dentist2", json={"description": "Não autorizado"}), 403)
    add("DRAFT-other-author-finalize", "RF-024-CA03", req(client, "POST", f"/api/v1/patients/evolutions/{evolution1}/finalize", "dentist2"), 403)
    add("DRAFT-own-edit", "RF-024-CA03", req(client, "PATCH", f"/api/v1/patients/evolutions/{evolution1}/draft", "dentist1", json={"description": "Texto fictício D1 revisado"}), 200, field="description", value="Texto fictício D1 revisado")
    add("DRAFT-own-finalize", "RF-024-CA03", req(client, "POST", f"/api/v1/patients/evolutions/{evolution1}/finalize", "dentist1"), 200, field="status", value="FINALIZED")
    listing2 = add("HISTORY-shared-finalized", "RF-023-CA05", req(client, "GET", f"/api/v1/patients/{shared}/evolutions", "dentist2"), 200)
    RESULTS.append({"id": "HISTORY-d2-final-and-own-draft", "requirement": "RF-023-CA05", "layer": "HTTP", "expected": "D2 vê finalizada D1 e rascunho D2", "observed": f"IDs {[x['id'] for x in listing2]}", "result": "aprovado" if {x["id"] for x in listing2} == {evolution1, evolution2} else "reprovado", "note": ""})
    add("FINALIZED-no-edit", "RF-024-CA05", req(client, "PATCH", f"/api/v1/patients/evolutions/{evolution1}/draft", "dentist1", json={"description": "Alteração indevida"}), 422)
    add("FINALIZED-no-refinalize", "RF-024-CA05", req(client, "POST", f"/api/v1/patients/evolutions/{evolution1}/finalize", "dentist1"), 422)

    cancel_appt = ids("appointments", "cancel_only")
    cancel_patient = ids("patients", "cancel")
    add("CANCEL-confirm", "RN-031", req(client, "PATCH", f"/api/v1/appointments/{cancel_appt}/status", "reception", json={"status": "CONFIRMED"}), 200)
    add("CANCEL-access-before", "RN-031", req(client, "GET", f"/api/v1/patients/{cancel_patient}/record", "dentist1"), 200)
    add("CANCEL-operation", "RN-031", req(client, "POST", f"/api/v1/appointments/{cancel_appt}/cancel", "reception"), 200, field="status", value="CANCELED")
    add("CANCEL-access-after", "RN-031", req(client, "GET", f"/api/v1/patients/{cancel_patient}/record", "dentist1"), 403)

    no_show_appt = ids("appointments", "no_show_only")
    no_show_patient = ids("patients", "no_show")
    add("NOSHOW-confirm", "RN-031", req(client, "PATCH", f"/api/v1/appointments/{no_show_appt}/status", "reception", json={"status": "CONFIRMED"}), 200)
    add("NOSHOW-access-before", "RN-031", req(client, "GET", f"/api/v1/patients/{no_show_patient}/record", "dentist1"), 200)
    add("NOSHOW-operation", "RN-031", req(client, "PATCH", f"/api/v1/appointments/{no_show_appt}/status", "dentist1", json={"status": "NO_SHOW"}), 200, field="status", value="NO_SHOW")
    add("NOSHOW-access-after", "RN-031", req(client, "GET", f"/api/v1/patients/{no_show_patient}/record", "dentist1"), 403)

    alt_patient = ids("patients", "alternative")
    for key in ("alt_one", "alt_two"):
        add(f"ALT-confirm-{key}", "RN-031", req(client, "PATCH", f"/api/v1/appointments/{ids('appointments',key)}/status", "reception", json={"status": "CONFIRMED"}), 200)
    add("ALT-cancel-one", "RN-031", req(client, "POST", f"/api/v1/appointments/{ids('appointments','alt_one')}/cancel", "reception"), 200)
    add("ALT-access-remains", "RN-031", req(client, "GET", f"/api/v1/patients/{alt_patient}/record", "dentist1"), 200)
    add("ALT-cancel-last", "RN-031", req(client, "POST", f"/api/v1/appointments/{ids('appointments','alt_two')}/cancel", "reception"), 200)
    add("ALT-access-revoked", "RN-031", req(client, "GET", f"/api/v1/patients/{alt_patient}/record", "dentist1"), 403)

    cont_patient = ids("patients", "continuity")
    cont_past = ids("appointments", "continuity_past")
    cont_later = ids("appointments", "continuity_later")
    add("CONT-confirm-past", "RN-031", req(client, "PATCH", f"/api/v1/appointments/{cont_past}", "admin", json={"status": "CONFIRMED"}), 200)
    add("CONT-complete-generic", "RN-031", req(client, "PATCH", f"/api/v1/appointments/{cont_past}", "dentist1", json={"status": "COMPLETED", "care_occurred_at": care_at}), 200, field="status", value="COMPLETED")
    add("CONT-confirm-later", "RN-031", req(client, "PATCH", f"/api/v1/appointments/{cont_later}/status", "reception", json={"status": "CONFIRMED"}), 200)
    add("CONT-cancel-later", "RN-031", req(client, "POST", f"/api/v1/appointments/{cont_later}/cancel", "reception"), 200)
    add("CONT-access-after-cancel", "RN-031", req(client, "GET", f"/api/v1/patients/{cont_patient}/record", "dentist1"), 200)

    open_patient = ids("patients", "open")
    open_appt = ids("appointments", "open")
    add("OPEN-confirm", "RN-031", req(client, "PATCH", f"/api/v1/appointments/{open_appt}/status", "reception", json={"status": "CONFIRMED"}), 200)
    add("OPEN-list-before", "RF-023", req(client, "GET", f"/api/v1/patients/{open_patient}/evolutions", "dentist1"), 404)
    opened = add("OPEN-GET-creates", "D02 aberto", req(client, "GET", f"/api/v1/patients/{open_patient}/record", "dentist1"), 200)
    second = add("OPEN-GET-reuses", "RF-023-CA01", req(client, "GET", f"/api/v1/patients/{open_patient}/record", "dentist1"), 200)
    RESULTS.append({"id": "OPEN-single-record", "requirement": "RF-023-CA01", "layer": "HTTP", "expected": "mesmo ID após repetição", "observed": f"{opened.get('id')}/{second.get('id')}", "result": "aprovado" if opened.get("id") == second.get("id") else "reprovado", "note": "GET com efeito de escrita é contrato atual; D02 aberto"})

    sentinel = "QA-SENTINEL-CLINICO-FICTICIO-73184"
    bad = req(client, "POST", "/api/v1/patients/evolutions", "dentist1", json={"patient_id": shared, "description": {"text": sentinel}})
    add("ERROR-clinical-text-absent", "RF-024", bad, 422)
    RESULTS.append({"id": "ERROR-no-leak", "requirement": "RF-024", "layer": "HTTP", "expected": "sentinela ausente no erro", "observed": "ausente" if sentinel not in bad.text else "presente", "result": "aprovado" if sentinel not in bad.text else "reprovado", "note": ""})

    rollback_patient = ids("patients", "rollback")
    rollback_appt = ids("appointments", "rollback")
    add("ROLLBACK-confirm", "RN-031", req(client, "PATCH", f"/api/v1/appointments/{rollback_appt}/status", "reception", json={"status": "CONFIRMED"}), 200)
    add("ROLLBACK-wrong-link", "RF-024-CA02", req(client, "POST", "/api/v1/patients/evolutions", "dentist1", json={"patient_id": rollback_patient, "appointment_id": shared_d1, "description": "Falha fictícia"}), 404)
    add("ROLLBACK-no-record", "RF-024-CA06", req(client, "GET", f"/api/v1/patients/{rollback_patient}/evolutions", "dentist1"), 404)

    # Marca o caminho HTTP que a interface atual usa: sem care_occurred_at.
    add("UI-contract-completion-body", "RN-031", req(client, "PATCH", f"/api/v1/appointments/{shared_d2}/status", "dentist2", json={"status": "COMPLETED"}), 422)

(ROOT / "http-results.json").write_text(json.dumps({
    "base": BASE,
    "care_occurred_at_fixture": care_at,
    "cases": RESULTS,
    "shared_record_id": record.json().get("id"),
    "finalized_evolution_id": evolution1,
}, indent=2, ensure_ascii=False) + "\n")
passed = sum(case["result"] == "aprovado" for case in RESULTS)
failed = len(RESULTS) - passed
print(f"HTTP cases={len(RESULTS)} approved={passed} failed={failed}")
for case in RESULTS:
    if case["result"] != "aprovado":
        print(case["id"], case["expected"], case["observed"])
