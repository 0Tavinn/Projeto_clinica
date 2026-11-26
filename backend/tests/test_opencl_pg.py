"""Concorrência HTTP/SQL apenas no PostgreSQL 16 exclusivo do runner."""

import datetime as dt
import os
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, func, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_db
from app.users.models import Clinic, User
from app.dentists.models import Dentist
from app.patients.models import Patient
from app.appointments.models import Appointment
from app.appointments.repository import AppointmentRepository
from app.appointments.conflict_detection import detect_conflict
from app.security.auth import create_access_token
from app.security.roles import Role


@pytest.fixture
def scratch():
    """Recusa destinos fora da rede e do banco exclusivos do ensaio."""
    url = os.environ.get("LUMINA_OPENCL_PG_URL")
    if not url:
        pytest.skip("PostgreSQL exclusivo não configurado")
    parsed = make_url(url)
    assert parsed.host == "pg" and parsed.database == "lumina_opencl_scratch"
    assert parsed.username == "opencl_qa"
    engine = create_engine(url, connect_args={"options": "-c statement_timeout=15000"})
    with Session(engine) as db:
        assert str(db.scalar(text("SHOW server_version_num"))).startswith("16")
        clinic = Clinic(name="QA OpenCL", cnpj="12345678000199", email="qa@example.test")
        db.add(clinic)
        db.flush()
        users = [
            User(clinic_id=clinic.id, full_name="QA", email=f"qa{i}@example.test",
                 cpf=f"{i+1:011d}", password_hash="not-used",
                 role=Role.RECEPTIONIST if i < 2 else Role.DENTIST)
            for i in range(3)
        ]
        db.add_all(users)
        db.flush()
        dentist = Dentist(user_id=users[2].id, cro_number="11111", cro_state="PE")
        patient = Patient(clinic_id=clinic.id, full_name="QA", cpf="99999999999",
                          medical_record_number="OPENCL", birth_date=dt.date(1990, 1, 1))
        second_patient = Patient(clinic_id=clinic.id, full_name="Outra QA", cpf="88888888888",
                                 medical_record_number="OPENCL-2", birth_date=dt.date(1991, 1, 1))
        db.add_all([dentist, patient, second_patient])
        db.commit()
        headers = [{"Authorization": f"Bearer {create_access_token(user)}"} for user in users[:2]]
        values = clinic.id, dentist.id, (patient.id, second_patient.id), headers
    def independent_session():
        # Uma conexão/transação por requisição, inclusive autenticação.
        with Session(engine, autoflush=False) as db:
            yield db
    app.dependency_overrides[get_db] = independent_session
    try:
        yield engine, values
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_http_race_and_gist_authority(scratch, monkeypatch):
    """Espera real do advisory lock e rejeição GiST com prevenção contornada."""
    from app.core.config import get_settings
    # Esta sondagem exige kernel real, independentemente do padrão cotidiano.
    monkeypatch.setattr(get_settings(), "APPOINTMENT_CONFLICT_ENGINE", "auto")
    engine, (clinic_id, dentist_id, patient_ids, headers) = scratch
    scheduled = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=10)).replace(microsecond=0)
    payload = {"patient_id": patient_ids[0], "dentist_id": dentist_id,
               "scheduled_at": scheduled.isoformat(), "duration_minutes": 30}
    results = []
    def observed(*args, **kwargs):
        result = detect_conflict(*args, **kwargs)
        results.append(result)
        return result
    def request(header, patient_id=patient_ids[0]):
        with TestClient(app) as client:
            return client.post("/api/v1/appointments", json=dict(payload, patient_id=patient_id), headers=header)
    with engine.connect() as holder:
        holder.execute(text("SELECT pg_advisory_xact_lock(:key)"),
                       {"key": clinic_id*1_000_000+dentist_id})
        with patch("app.appointments.repository.detect_conflict", side_effect=observed):
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(request, header, patient_id)
                           for header, patient_id in zip(headers, patient_ids)]
                try:
                    deadline = time.monotonic()+10
                    waiting = 0
                    while time.monotonic() < deadline:
                        with engine.connect() as monitor:
                            waiting = monitor.scalar(text(
                                "SELECT count(*) FROM pg_stat_activity "
                                "WHERE datname=current_database() AND wait_event_type='Lock' "
                                "AND query LIKE 'SELECT pg_advisory_xact_lock%'"
                            ))
                        if waiting >= 2:
                            break
                        time.sleep(.05)
                    assert waiting >= 2, "Duas requisições devem esperar o lock real"
                finally:
                    holder.commit()
                responses = [future.result(timeout=20) for future in futures]
    assert sorted(response.status_code for response in responses) == [201, 409]
    accepted = next(response for response in responses if response.status_code == 201)
    assert accepted.json()["patient_id"] in patient_ids
    rejected = next(response for response in responses if response.status_code == 409)
    assert rejected.json()["error"]["code"] == "APPOINTMENT_TIME_CONFLICT"
    assert any(result.engine == "opencl" and result.conflict and not result.fallback
               for result in results)
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(Appointment)) == 1
        assert db.scalar(select(Appointment.patient_id)) == accepted.json()["patient_id"]

    # A sondagem ignora apenas a prevenção em memória. O PostgreSQL continua
    # recusando a reserva duplicada e a transação falha sem inserir nova linha.
    with patch.object(AppointmentRepository, "has_conflict", return_value=False):
        duplicate = request(headers[1])
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "APPOINTMENT_TIME_CONFLICT"
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(Appointment)) == 1
        assert db.scalar(select(Appointment.patient_id)) == accepted.json()["patient_id"]
        # A adjacência [fim,início) continua permitida após rollback do conflito.
    adjacent = dict(payload, scheduled_at=(scheduled+dt.timedelta(minutes=30)).isoformat())
    with TestClient(app) as client:
        response = client.post("/api/v1/appointments", json=adjacent, headers=headers[0])
    assert response.status_code == 201, response.text
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(Appointment)) == 2
