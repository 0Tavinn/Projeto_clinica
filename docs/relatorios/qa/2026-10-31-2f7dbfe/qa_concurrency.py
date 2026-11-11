"""Sondagens PostgreSQL 16 com conexões independentes no Compose exclusivo.

Requer QA_TEST_PASSWORD. Não contém senha ou token; usa somente dados fictícios
de qa_fixture.py. O contêiner e a API são fixados ao ensaio de 2026-10-31.
"""

import concurrent.futures as futures
import json
import os
import select
import subprocess
import time
from pathlib import Path

import httpx


ROOT = Path(__file__).resolve().parent
fixture = json.loads((ROOT / "fixture-ids.json").read_text())
API = "http://127.0.0.1:18128"
DB_CONTAINER = "lumina_qa_20261031_2f7dbfe-db-1"
DB_NAME = "lumina_qa_20261031_2f7dbfe_db"
DB_USER = "qa_clinic"
PASSWORD = os.environ["QA_TEST_PASSWORD"]
results = []


def psql(sql):
    done = subprocess.run(
        ["docker", "exec", DB_CONTAINER, "psql", "-X", "-Atq", "-U", DB_USER, "-d", DB_NAME, "-c", sql],
        capture_output=True, text=True, timeout=8, check=True,
    )
    return done.stdout.strip()


def request(method, path, token, payload=None):
    with httpx.Client(base_url=API, timeout=12, trust_env=False) as client:
        return client.request(method, path, headers={"Authorization": f"Bearer {token}"}, json=payload)


def login(key):
    with httpx.Client(base_url=API, timeout=8, trust_env=False) as client:
        result = client.post("/api/v1/auth/login", data={
            "username": fixture["users"][key]["email"], "password": PASSWORD,
        })
    if result.status_code != 200:
        raise RuntimeError(f"Login QA {key}: HTTP {result.status_code}")
    return result.json()["access_token"]


def record(case, requirement, expected, observed, passed, note=""):
    results.append({"id": case, "requirement": requirement, "layer": "PostgreSQL/HTTP",
                    "expected": expected, "observed": observed,
                    "result": "aprovado" if passed else "reprovado", "note": note})


class HeldRow:
    def __init__(self, evolution_id):
        self.evolution_id = evolution_id
        self.process = None

    def __enter__(self):
        self.process = subprocess.Popen(
            ["docker", "exec", "-i", DB_CONTAINER, "psql", "-X", "-Atq", "-U", DB_USER, "-d", DB_NAME],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            bufsize=0,
        )
        self.process.stdin.write(
            f"BEGIN;\nSELECT id FROM clinical_evolutions WHERE id={self.evolution_id} FOR UPDATE;\n\\echo LOCKED\n".encode()
        )
        self.process.stdin.flush()
        deadline = time.monotonic() + 8
        output = b""
        while time.monotonic() < deadline:
            if select.select([self.process.stdout], [], [], 0.2)[0]:
                output += os.read(self.process.stdout.fileno(), 4096)
                if b"LOCKED" in output:
                    return self
            if self.process.poll() is not None:
                break
        raise RuntimeError("Não obteve bloqueio da evolução em até 8 segundos")

    def release(self):
        if self.process and self.process.poll() is None:
            self.process.stdin.write(b"COMMIT;\n")
            self.process.stdin.flush()
            self.process.stdin.close()
            self.process.wait(timeout=8)

    def __exit__(self, *_):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.process.wait(timeout=5)


def wait_for_lock(minimum=1):
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        waiting = int(psql("SELECT count(*) FROM pg_stat_activity WHERE wait_event_type='Lock' AND query ILIKE '%clinical_evolutions%' AND pid <> pg_backend_pid()"))
        if waiting >= minimum:
            return waiting
        time.sleep(0.15)
    return 0


def prepare_draft(key, receptionist, dentist):
    appointment_id = fixture["appointments"][key]
    patient_id = fixture["patients"][key]
    confirm = request("PATCH", f"/api/v1/appointments/{appointment_id}/status", receptionist, {"status": "CONFIRMED"})
    if confirm.status_code != 200:
        raise RuntimeError(f"Não confirmou {key}: HTTP {confirm.status_code}")
    draft = request("POST", "/api/v1/patients/evolutions", dentist, {
        "patient_id": patient_id, "appointment_id": appointment_id,
        "description": f"Rascunho QA {key}",
    })
    if draft.status_code != 201:
        raise RuntimeError(f"Não criou rascunho {key}: HTTP {draft.status_code}")
    return appointment_id, draft.json()["id"]


reception = login("reception")
dentist1 = login("dentist1")

with futures.ThreadPoolExecutor(max_workers=3) as pool:
    # Abertura simultânea após confirmação real pela API.
    patient = fixture["patients"]["rollback"]
    open_calls = [pool.submit(request, "GET", f"/api/v1/patients/{patient}/record", dentist1)
                  for _ in range(2)]
    opened = [task.result(timeout=12) for task in open_calls]
    open_ids = [item.json().get("id") for item in opened]
    count = int(psql(f"SELECT count(*) FROM medical_records WHERE patient_id={patient}"))
    record("PG-open-simultaneous", "RF-023-CA01", "dois HTTP 200, um prontuário",
           f"HTTP {[item.status_code for item in opened]}, IDs {open_ids}, linhas {count}",
           all(item.status_code == 200 for item in opened) and len(set(open_ids)) == 1 and count == 1)

    for key, action in (("race_edit", "edit"), ("race_finalize", "finalize")):
        appointment_id, evolution_id = prepare_draft(key, reception, dentist1)
        with HeldRow(evolution_id) as holder:
            if action == "edit":
                pending = pool.submit(request, "PATCH", f"/api/v1/patients/evolutions/{evolution_id}/draft",
                                      dentist1, {"description": "Edição após perda do último acesso"})
            else:
                pending = pool.submit(request, "POST", f"/api/v1/patients/evolutions/{evolution_id}/finalize",
                                      dentist1)
            waiting = wait_for_lock()
            cancel = request("POST", f"/api/v1/appointments/{appointment_id}/cancel", reception)
            holder.release()
            response = pending.result(timeout=12)
        stored = psql(f"SELECT status || '|' || description FROM clinical_evolutions WHERE id={evolution_id}")
        still_denied = request("GET", f"/api/v1/patients/{fixture['patients'][key]}/record", dentist1)
        record(f"PG-loss-access-{action}", "RN-031/RF-024", "mutação negada após revogação; rascunho intacto",
               f"espera={waiting}, cancel HTTP {cancel.status_code}, mutação HTTP {response.status_code}, estado {stored}, leitura posterior HTTP {still_denied.status_code}",
               waiting >= 1 and cancel.status_code == 200 and response.status_code == 403
               and stored == f"DRAFT|Rascunho QA {key}" and still_denied.status_code == 403,
               "Conexões independentes; bloqueio de linha garantiu a ordem")

    _, evolution_id = prepare_draft("double_edit", reception, dentist1)
    with HeldRow(evolution_id) as holder:
        first = pool.submit(request, "PATCH", f"/api/v1/patients/evolutions/{evolution_id}/draft",
                            dentist1, {"description": "Edição A"})
        wait_first = wait_for_lock()
        second = pool.submit(request, "PATCH", f"/api/v1/patients/evolutions/{evolution_id}/draft",
                             dentist1, {"description": "Edição B"})
        wait_second = wait_for_lock(2)
        holder.release()
        r1, r2 = first.result(timeout=12), second.result(timeout=12)
    final_text = psql(f"SELECT description FROM clinical_evolutions WHERE id={evolution_id}")
    record("PG-two-edits", "RF-024-CA10", "conflito explícito; nenhuma sobrescrita silenciosa",
           f"esperas {wait_first}/{wait_second}, HTTP {r1.status_code}/{r2.status_code}, final {final_text}",
           wait_first >= 1 and wait_second >= 2 and sorted([r1.status_code, r2.status_code]) == [200, 409],
           "Ambas as requisições partiram enquanto a linha estava bloqueada")

(ROOT / "concurrency-results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n")
print(f"PostgreSQL concurrency cases={len(results)} approved={sum(r['result']=='aprovado' for r in results)} failed={sum(r['result']=='reprovado' for r in results)}")
for item in results:
    print(item["id"], item["observed"], item["result"])
