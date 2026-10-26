"""Ensaios da API em PostgreSQL 16 exclusivamente descartável.

Executar por ``tests/run_clinical_pg16.sh``. O módulo pula sem o destino
temporário e nunca cria nem migra o banco de desenvolvimento.
"""

import datetime
import os
import socket
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event
from unittest.mock import patch

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import Session

from app.appointments.models import Appointment, AppointmentStatus
from app.core.database import engine as app_engine
from app.dentists.models import Dentist
from app.main import app
from app.patients.models import Patient
from app.records.access_models import ClinicalAccessGrant
from app.records.models import ClinicalEvolution, MedicalRecord
from app.records.repository import RecordRepository
from app.security.hashing import hash_password
from app.security.roles import Role
from app.users.models import Clinic, User


@pytest.fixture(scope="module")
def pg_engine():
    url = os.environ.get("LUMINA_CLINICAL_PG16_URL")
    if not url:
        pytest.skip("PostgreSQL descartável não configurado")
    parsed = make_url(url)
    assert parsed.drivername == "postgresql+psycopg"
    assert parsed.host == "127.0.0.1"
    assert parsed.database == "lumina_clinical_api_scratch"
    assert parsed.port is not None
    assert str(app_engine.url) == str(parsed)

    engine = create_engine(url, pool_pre_ping=True)
    with engine.connect() as connection:
        assert connection.scalar(text("SHOW server_version_num"))[:2] == "16"
        assert connection.scalar(text("SELECT current_database()")) == parsed.database
        assert connection.scalar(text("SELECT to_regclass('public.clinical_access_grants')"))
    yield engine
    engine.dispose()


@pytest.fixture(scope="module")
def identities(pg_engine):
    """Prepara somente dados fictícios no banco temporário exclusivo."""
    with Session(pg_engine, autoflush=False, expire_on_commit=False) as db:
        clinic = Clinic(
            name="Clínica PostgreSQL 16 descartável",
            cnpj="00000000000191",
            email="pg16-scratch@clinica.example.com",
        )
        db.add(clinic)
        db.flush()
        receptionist = User(
            clinic_id=clinic.id,
            full_name="Recepção Teste",
            email="recepcao.pg16@clinica.example.com",
            password_hash=hash_password("Senha@1234"),
            cpf="00000000001",
            role=Role.RECEPTIONIST,
        )
        dentist_user = User(
            clinic_id=clinic.id,
            full_name="Dentista Teste",
            email="dentista.pg16@clinica.example.com",
            password_hash=hash_password("Senha@1234"),
            cpf="00000000002",
            role=Role.DENTIST,
        )
        db.add_all([receptionist, dentist_user])
        db.flush()
        dentist = Dentist(user_id=dentist_user.id, cro_number="12345", cro_state="PE")
        db.add(dentist)
        db.commit()
        return clinic.id, receptionist.email, dentist_user.email, dentist.id


def _appointment(pg_engine, identities, *, suffix: str) -> tuple[int, int]:
    clinic_id, _, _, dentist_id = identities
    with Session(pg_engine, autoflush=False, expire_on_commit=False) as db:
        patient = Patient(
            clinic_id=clinic_id,
            full_name=f"Paciente {suffix}",
            cpf={
                "flow": "12345678901",
                "confirm": "12345678902",
                "lock": "12345678903",
                "cancel": "12345678904",
                "rollback": "12345678905",
            }[suffix],
            medical_record_number=f"PG16-{suffix.upper()}",
            birth_date=datetime.date(1990, 1, 1),
        )
        db.add(patient)
        db.flush()
        appointment = Appointment(
            clinic_id=clinic_id,
            patient_id=patient.id,
            dentist_id=dentist_id,
            scheduled_at=datetime.datetime.now(datetime.timezone.utc)
            - datetime.timedelta(
                hours={"rollback": 10, "cancel": 8, "flow": 6, "confirm": 4, "lock": 2}[suffix]
            ),
            duration_minutes=30,
            status=AppointmentStatus.SCHEDULED,
        )
        db.add(appointment)
        db.commit()
        return patient.id, appointment.id


def _headers(client, email: str) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "Senha@1234"},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _free_local_port() -> int:
    with socket.socket() as connection:
        connection.bind(("127.0.0.1", 0))
        return connection.getsockname()[1]


def _start_api(port: int) -> subprocess.Popen:
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=Path(__file__).resolve().parents[1],
        env=os.environ.copy(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(100):
        if process.poll() is not None:
            raise AssertionError("A API temporária terminou durante a inicialização")
        try:
            response = httpx.get(f"http://127.0.0.1:{port}/health", timeout=0.5)
            if response.status_code == 200:
                return process
        except httpx.HTTPError:
            pass
        time.sleep(0.1)
    _stop_api(process)
    raise AssertionError("A API temporária não respondeu a /health")


def _stop_api(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def test_http_flow_persists_after_api_restart(pg_engine, identities):
    """Exercita contrato técnico atual; D02 e D03 ainda não são aceites clínicos."""
    _, receptionist_email, dentist_email, _ = identities
    patient_id, appointment_id = _appointment(pg_engine, identities, suffix="flow")
    port = _free_local_port()
    process = _start_api(port)
    try:
        with httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=5) as client:
            receptionist = _headers(client, receptionist_email)
            dentist = _headers(client, dentist_email)
            confirmed = client.patch(
                f"/api/v1/appointments/{appointment_id}/status",
                json={"status": "CONFIRMED"},
                headers=receptionist,
            )
            assert confirmed.status_code == 200, confirmed.text

            occurred_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
                minutes=5
            )
            completed = client.patch(
                f"/api/v1/appointments/{appointment_id}/status",
                json={"status": "COMPLETED", "care_occurred_at": occurred_at.isoformat()},
                headers=dentist,
            )
            assert completed.status_code == 200, completed.text

            record = client.get(f"/api/v1/patients/{patient_id}/record", headers=dentist)
            assert record.status_code == 200, record.text
            record_id = record.json()["id"]
            draft = client.post(
                "/api/v1/patients/evolutions",
                json={
                    "patient_id": patient_id,
                    "appointment_id": appointment_id,
                    "description": "Evolução fictícia persistente",
                },
                headers=dentist,
            )
            assert draft.status_code == 201, draft.text
            evolution_id = draft.json()["id"]
            finalized = client.post(
                f"/api/v1/patients/evolutions/{evolution_id}/finalize", headers=dentist
            )
            assert finalized.status_code == 200, finalized.text
    finally:
        _stop_api(process)

    process = _start_api(port)
    try:
        with httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=5) as client:
            dentist = _headers(client, dentist_email)
            record = client.get(f"/api/v1/patients/{patient_id}/record", headers=dentist)
            listed = client.get(f"/api/v1/patients/{patient_id}/evolutions", headers=dentist)
            assert record.status_code == 200, record.text
            assert record.json()["id"] == record_id
            assert listed.status_code == 200, listed.text
            assert [(item["id"], item["status"]) for item in listed.json()] == [
                (evolution_id, "FINALIZED")
            ]
    finally:
        _stop_api(process)

    with Session(pg_engine) as db:
        grant = db.get(ClinicalAccessGrant, appointment_id)
        assert grant.confirmed_by_user_id is not None
        assert grant.care_occurred_at is not None
        assert grant.care_recorded_at is not None
        assert grant.care_recorded_by_user_id is not None
        assert db.get(MedicalRecord, record_id).patient_id == patient_id
        assert db.get(ClinicalEvolution, evolution_id).status == "FINALIZED"


def test_parallel_confirmation_and_completion_keep_one_evidence(pg_engine, identities):
    _, receptionist_email, dentist_email, _ = identities
    _, appointment_id = _appointment(pg_engine, identities, suffix="confirm")
    with TestClient(app) as client:
        headers = _headers(client, receptionist_email)
        url = f"/api/v1/appointments/{appointment_id}/status"
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [
                pool.submit(client.patch, url, json={"status": "CONFIRMED"}, headers=headers)
                for _ in range(2)
            ]
            responses = [future.result(timeout=10) for future in futures]

        assert sorted(response.status_code for response in responses) == [200, 422]
        dentist = _headers(client, dentist_email)
        occurred_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
            minutes=5
        )
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [
                pool.submit(
                    client.patch,
                    url,
                    json={
                        "status": "COMPLETED",
                        "care_occurred_at": occurred_at.isoformat(),
                    },
                    headers=dentist,
                )
                for _ in range(2)
            ]
            completions = [future.result(timeout=10) for future in futures]

    assert sorted(response.status_code for response in completions) == [200, 422]
    with Session(pg_engine) as db:
        assert db.scalar(
            select(func.count()).select_from(ClinicalAccessGrant).where(
                ClinicalAccessGrant.appointment_id == appointment_id
            )
        ) == 1
        grant = db.get(ClinicalAccessGrant, appointment_id)
        assert grant.confirmed_by_user_id is not None
        assert grant.care_occurred_at is not None
        assert grant.care_recorded_at is not None
        assert grant.care_recorded_by_user_id is not None
        assert db.get(Appointment, appointment_id).status is AppointmentStatus.COMPLETED


def test_edit_waits_for_finalization_lock(pg_engine, identities):
    _, receptionist_email, dentist_email, _ = identities
    patient_id, appointment_id = _appointment(pg_engine, identities, suffix="lock")
    with TestClient(app) as client:
        receptionist = _headers(client, receptionist_email)
        dentist = _headers(client, dentist_email)
        confirmed = client.patch(
            f"/api/v1/appointments/{appointment_id}/status",
            json={"status": "CONFIRMED"},
            headers=receptionist,
        )
        assert confirmed.status_code == 200, confirmed.text
        draft = client.post(
            "/api/v1/patients/evolutions",
            json={
                "patient_id": patient_id,
                "appointment_id": appointment_id,
                "description": "Texto antes da finalização",
            },
            headers=dentist,
        )
        assert draft.status_code == 201, draft.text
        evolution_id = draft.json()["id"]

        reached_lock = Event()
        original = RecordRepository.get_evolution_for_update

        def observe_lock(repository, requested_id):
            reached_lock.set()
            return original(repository, requested_id)

        with Session(pg_engine, expire_on_commit=False) as holder:
            locked = holder.execute(
                select(ClinicalEvolution)
                .where(ClinicalEvolution.id == evolution_id)
                .with_for_update(of=ClinicalEvolution)
            ).scalar_one()
            locked.status = "FINALIZED"
            locked.finalized_at = datetime.datetime.now(datetime.timezone.utc)

            with patch.object(RecordRepository, "get_evolution_for_update", observe_lock):
                with ThreadPoolExecutor(max_workers=1) as pool:
                    future = pool.submit(
                        client.patch,
                        f"/api/v1/patients/evolutions/{evolution_id}/draft",
                        json={"description": "Sobrescrita indevida"},
                        headers=dentist,
                    )
                    assert reached_lock.wait(timeout=5)
                    holder.commit()
                    response = future.result(timeout=10)
        assert response.status_code == 422, response.text

    with Session(pg_engine) as db:
        stored = db.get(ClinicalEvolution, evolution_id)
        assert stored.status == "FINALIZED"
        assert stored.description == "Texto antes da finalização"


def test_draft_rechecks_origin_after_appointment_lock(pg_engine, identities):
    _, receptionist_email, dentist_email, _ = identities
    patient_id, appointment_id = _appointment(pg_engine, identities, suffix="cancel")
    with TestClient(app) as client:
        receptionist = _headers(client, receptionist_email)
        dentist = _headers(client, dentist_email)
        response = client.patch(
            f"/api/v1/appointments/{appointment_id}/status",
            json={"status": "CONFIRMED"},
            headers=receptionist,
        )
        assert response.status_code == 200, response.text

        reached_lock = Event()
        original = RecordRepository.get_appointment_for_update

        def observe_lock(repository, requested_id, clinic_id):
            reached_lock.set()
            return original(repository, requested_id, clinic_id)

        with Session(pg_engine) as holder:
            appointment = holder.execute(
                select(Appointment)
                .where(Appointment.id == appointment_id)
                .with_for_update(of=Appointment)
            ).scalar_one()
            appointment.status = AppointmentStatus.CANCELED

            with patch.object(RecordRepository, "get_appointment_for_update", observe_lock):
                with ThreadPoolExecutor(max_workers=1) as pool:
                    future = pool.submit(
                        client.post,
                        "/api/v1/patients/evolutions",
                        json={
                            "patient_id": patient_id,
                            "appointment_id": appointment_id,
                            "description": "Não deve ser persistida",
                        },
                        headers=dentist,
                    )
                    assert reached_lock.wait(timeout=5)
                    holder.commit()
                    response = future.result(timeout=10)

        assert response.status_code == 403, response.text

    with Session(pg_engine) as db:
        assert db.scalar(
            select(func.count()).select_from(MedicalRecord).where(
                MedicalRecord.patient_id == patient_id
            )
        ) == 0
        assert db.scalar(
            select(func.count()).select_from(ClinicalEvolution).where(
                ClinicalEvolution.appointment_id == appointment_id
            )
        ) == 0


def test_record_opening_rolls_back_if_draft_fails(pg_engine, identities):
    _, receptionist_email, dentist_email, _ = identities
    patient_id, appointment_id = _appointment(pg_engine, identities, suffix="rollback")
    with TestClient(app) as client:
        receptionist = _headers(client, receptionist_email)
        dentist = _headers(client, dentist_email)
        response = client.patch(
            f"/api/v1/appointments/{appointment_id}/status",
            json={"status": "CONFIRMED"},
            headers=receptionist,
        )
        assert response.status_code == 200, response.text

        with patch.object(
            RecordRepository,
            "add_evolution",
            side_effect=RuntimeError("Falha simulada após abertura"),
        ):
            with pytest.raises(RuntimeError, match="Falha simulada"):
                client.post(
                    "/api/v1/patients/evolutions",
                    json={
                        "patient_id": patient_id,
                        "appointment_id": appointment_id,
                        "description": "Não deve ser persistida",
                    },
                    headers=dentist,
                )

    with Session(pg_engine) as db:
        assert db.scalar(
            select(func.count()).select_from(MedicalRecord).where(
                MedicalRecord.patient_id == patient_id
            )
        ) == 0
        assert db.scalar(
            select(func.count()).select_from(ClinicalEvolution).where(
                ClinicalEvolution.appointment_id == appointment_id
            )
        ) == 0
