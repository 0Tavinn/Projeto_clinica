"""Duas finalizações da mesma evolução em conexões API independentes, PostgreSQL 16.

Executar pelo qa_two_finalizations_pg16.sh, que prepara banco descartável.
"""

import datetime as dt
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.records.models import ClinicalEvolution
from tests.test_clinical_pg16 import _appointment, _headers, identities, pg_engine


def test_two_simultaneous_finalizations_same_evolution(pg_engine, identities):
    _, receptionist_email, dentist_email, _ = identities
    patient_id, appointment_id = _appointment(pg_engine, identities, suffix="flow")
    with TestClient(app) as client:
        receptionist = _headers(client, receptionist_email)
        dentist = _headers(client, dentist_email)
        confirmed = client.patch(
            f"/api/v1/appointments/{appointment_id}/status",
            json={"status": "CONFIRMED"}, headers=receptionist,
        )
        assert confirmed.status_code == 200, confirmed.text
        draft = client.post(
            "/api/v1/patients/evolutions",
            json={"patient_id": patient_id, "appointment_id": appointment_id,
                  "description": "Finalização concorrente fictícia"},
            headers=dentist,
        )
        assert draft.status_code == 201, draft.text
        evolution_id = draft.json()["id"]
        barrier = Barrier(2)

        def finalize():
            barrier.wait(timeout=5)
            return client.post(f"/api/v1/patients/evolutions/{evolution_id}/finalize", headers=dentist)

        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = [future.result(timeout=12) for future in
                         [pool.submit(finalize), pool.submit(finalize)]]

    statuses = sorted(response.status_code for response in responses)
    with Session(pg_engine) as db:
        stored = db.get(ClinicalEvolution, evolution_id)
        assert stored.status == "FINALIZED"
        assert stored.finalized_at is not None
        assert stored.description == "Finalização concorrente fictícia"
    print("two_finalizations_http", statuses, "stored_status", stored.status)
    assert statuses == [200, 422]
