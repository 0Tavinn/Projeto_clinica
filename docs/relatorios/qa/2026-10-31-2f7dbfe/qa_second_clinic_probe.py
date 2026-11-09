"""Prova positiva e negativa de isolamento com vínculo válido nas duas clínicas."""

import json
import os
from pathlib import Path

import httpx


ROOT = Path(__file__).resolve().parent
fixture = json.loads((ROOT / "fixture-ids.json").read_text())
results = []


def record(case, expected, observed, passed):
    results.append({"id": case, "requirement": "RF-023-CA03", "layer": "HTTP",
                    "expected": expected, "observed": observed,
                    "result": "aprovado" if passed else "reprovado", "note": ""})


with httpx.Client(base_url="http://127.0.0.1:18128", timeout=8, trust_env=False) as client:
    def login(email):
        response = client.post("/api/v1/auth/login", data={
            "username": email, "password": os.environ["QA_TEST_PASSWORD"],
        })
        if response.status_code != 200:
            raise RuntimeError(f"login {email}: HTTP {response.status_code}")
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    receptionist = login("reception_b.qa31@example.test")
    dentist = login(fixture["users"]["dentist_other_clinic"]["email"])
    appointment = fixture["appointments"]["other_clinic"]
    patient_b = fixture["patients"]["other_clinic"]
    patient_a = fixture["patients"]["shared"]
    confirmation = client.patch(f"/api/v1/appointments/{appointment}/status",
                                headers=receptionist, json={"status": "CONFIRMED"})
    record("CLINIC-B-confirm-real", "200 pela recepção B", f"HTTP {confirmation.status_code}", confirmation.status_code == 200)
    own = client.get(f"/api/v1/patients/{patient_b}/record", headers=dentist)
    record("CLINIC-B-own-record", "200 no paciente B após confirmação", f"HTTP {own.status_code}", own.status_code == 200)
    cross = client.get(f"/api/v1/patients/{patient_a}/record", headers=dentist)
    record("CLINIC-B-denied-A", "403 no paciente A mesmo com origem B válida", f"HTTP {cross.status_code}", cross.status_code == 403)
    agenda = client.get("/api/v1/appointments", headers=dentist)
    items = agenda.json() if agenda.status_code == 200 else []
    record("CLINIC-B-own-agenda", "somente consultas da clínica B", f"HTTP {agenda.status_code}; clínicas {[i['clinic_id'] for i in items]}",
           agenda.status_code == 200 and len(items) == 1 and all(i["clinic_id"] == fixture["clinics"]["b"] for i in items))

(ROOT / "second-clinic-results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n")
print(f"second clinic cases={len(results)} approved={sum(x['result']=='aprovado' for x in results)} failed={sum(x['result']=='reprovado' for x in results)}")
for result in results:
    print(result["id"], result["observed"], result["result"])
