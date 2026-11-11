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
from app.records.access_repository import ClinicalAccessGrantRepository
from app.records.access_models import ClinicalAccessGrant
from app.records.models import ClinicalEvolution, MedicalRecord
from app.records.repository import RecordRepository
from app.security.auth import create_access_token
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
            "qa_edit": "12345678906",
            "qa_finalize": "12345678907",
            "qa_other": "12345678908",
            "qa_care": "12345678909",
            "qa_version": "12345678910",
            "d02d03d04": "12345678911",
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
                hours={"rollback": 10, "cancel": 8, "flow": 6, "confirm": 4,
                       "lock": 2, "qa_edit": 12, "qa_finalize": 14,
                       "qa_other": 16, "qa_care": 18, "qa_version": 20,
                       "d02d03d04": 22}[suffix]
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


def _open_record(client, patient_id: int, headers: dict[str, str]) -> int:
    """Exercita a abertura explícita após a confirmação da consulta."""
    absent = client.get(f"/api/v1/patients/{patient_id}/record", headers=headers)
    assert absent.status_code == 404, absent.text
    opened = client.post(f"/api/v1/patients/{patient_id}/record", headers=headers)
    assert opened.status_code == 201, opened.text
    return opened.json()["id"]


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
            record_id = _open_record(client, patient_id, dentist)
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
            completed = client.patch(
                f"/api/v1/appointments/{appointment_id}/status",
                json={"status": "COMPLETED", "care_occurred_at": occurred_at.isoformat()},
                headers=dentist,
            )
            assert completed.status_code == 200, completed.text
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
    patient_id, appointment_id = _appointment(pg_engine, identities, suffix="confirm")
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
        _open_record(client, patient_id, dentist)
        draft = client.post(
            "/api/v1/patients/evolutions",
            json={"patient_id": patient_id, "appointment_id": appointment_id,
                  "description": "Evolução para conclusão concorrente"}, headers=dentist,
        )
        assert draft.status_code == 201, draft.text
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


def test_explicit_opening_and_completion_require_saved_evolution(pg_engine, identities):
    """Confere D02–D04 em conexões HTTP e banco PostgreSQL separados."""
    _, receptionist_email, dentist_email, _ = identities
    patient_id, appointment_id = _appointment(pg_engine, identities, suffix="d02d03d04")
    with TestClient(app) as client:
        receptionist = _headers(client, receptionist_email)
        dentist = _headers(client, dentist_email)
        assert client.patch(
            f"/api/v1/appointments/{appointment_id}/status",
            json={"status": "CONFIRMED"}, headers=receptionist,
        ).status_code == 200
        record_url = f"/api/v1/patients/{patient_id}/record"
        assert client.get(record_url, headers=dentist).status_code == 404
        with Session(pg_engine) as db:
            assert db.scalar(select(func.count()).select_from(MedicalRecord).where(
                MedicalRecord.patient_id == patient_id
            )) == 0

        # O bloqueio do paciente deve serializar dois pedidos de abertura.
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(client.post, record_url, headers=dentist)
                       for _ in range(2)]
            opened = [future.result(timeout=10) for future in futures]
        assert sorted(response.status_code for response in opened) == [200, 201]
        assert len({response.json()["id"] for response in opened}) == 1

        occurred_at = (datetime.datetime.now(datetime.timezone.utc)
                       - datetime.timedelta(minutes=5)).isoformat()
        completion_url = f"/api/v1/appointments/{appointment_id}/status"
        completion = {"status": "COMPLETED", "care_occurred_at": occurred_at}
        missing = client.patch(completion_url, json=completion, headers=dentist)
        assert missing.status_code == 422
        invalid = client.post(
            "/api/v1/patients/evolutions",
            json={"patient_id": patient_id, "appointment_id": appointment_id,
                  "description": "   "}, headers=dentist,
        )
        assert invalid.status_code == 422
        draft = client.post(
            "/api/v1/patients/evolutions",
            json={"patient_id": patient_id, "appointment_id": appointment_id,
                  "description": "Atendimento fictício registrado"}, headers=dentist,
        )
        assert draft.status_code == 201, draft.text
        premature = client.post(
            f"/api/v1/patients/evolutions/{draft.json()['id']}/finalize",
            headers=dentist,
        )
        assert premature.status_code == 422
        completed = client.patch(completion_url, json=completion, headers=dentist)
        assert completed.status_code == 200, completed.text
        finalized = client.post(
            f"/api/v1/patients/evolutions/{draft.json()['id']}/finalize",
            headers=dentist,
        )
        assert finalized.status_code == 200, finalized.text
        assert finalized.json()["version"] == 2

    with Session(pg_engine) as db:
        assert db.scalar(select(func.count()).select_from(MedicalRecord).where(
            MedicalRecord.patient_id == patient_id
        )) == 1


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
        _open_record(client, patient_id, dentist)
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
                        json={"version": draft.json()["version"], "description": "Sobrescrita indevida"},
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


@pytest.mark.parametrize(
    "suffix,action,other_origin",
    [
        ("qa_edit", "edit", None),
        ("qa_finalize", "finalize", None),
        ("qa_other", "edit", "confirmed"),
        ("qa_care", "finalize", "completed"),
    ],
)
def test_mutation_rechecks_access_after_evolution_lock(
    pg_engine, identities, suffix, action, other_origin
):
    """Uma espera real não pode conservar autorização já revogada."""
    clinic_id, receptionist_email, dentist_email, dentist_id = identities
    patient_id, appointment_id = _appointment(pg_engine, identities, suffix=suffix)
    with TestClient(app) as client:
        receptionist = _headers(client, receptionist_email)
        dentist = _headers(client, dentist_email)
        assert client.patch(
            f"/api/v1/appointments/{appointment_id}/status",
            json={"status": "CONFIRMED"}, headers=receptionist,
        ).status_code == 200
        _open_record(client, patient_id, dentist)
        draft = client.post(
            "/api/v1/patients/evolutions",
            json={"patient_id": patient_id, "appointment_id": appointment_id,
                  "description": "Texto original"},
            headers=dentist,
        )
        assert draft.status_code == 201, draft.text
        evolution_id = draft.json()["id"]

        if other_origin is not None:
            now = datetime.datetime.now(datetime.timezone.utc)
            with Session(pg_engine) as db:
                receptionist_id = db.scalar(
                    select(User.id).where(User.email == receptionist_email)
                )
                dentist_user_id = db.scalar(
                    select(User.id).where(User.email == dentist_email)
                )
                second = Appointment(
                    clinic_id=clinic_id, patient_id=patient_id, dentist_id=dentist_id,
                    scheduled_at=now - datetime.timedelta(days=3),
                    duration_minutes=30,
                    status=(AppointmentStatus.CONFIRMED if other_origin == "confirmed"
                            else AppointmentStatus.COMPLETED),
                )
                db.add(second)
                db.flush()
                db.add(ClinicalAccessGrant(
                    appointment_id=second.id, clinic_id=clinic_id,
                    patient_id=patient_id, dentist_id=dentist_id,
                    granted_at=now, confirmed_by_user_id=receptionist_id,
                    care_occurred_at=(now - datetime.timedelta(days=3)
                                      if other_origin == "completed" else None),
                    care_recorded_at=(now if other_origin == "completed" else None),
                    care_recorded_by_user_id=(dentist_user_id
                                              if other_origin == "completed" else None),
                ))
                db.commit()

        reached_lock = Event()
        original = RecordRepository.get_evolution_for_update

        def observe_lock(repository, requested_id):
            reached_lock.set()
            return original(repository, requested_id)

        with Session(pg_engine) as holder:
            holder.execute(
                select(ClinicalEvolution.id)
                .where(ClinicalEvolution.id == evolution_id)
                .with_for_update(of=ClinicalEvolution)
            ).scalar_one()
            with patch.object(RecordRepository, "get_evolution_for_update", observe_lock):
                with ThreadPoolExecutor(max_workers=1) as pool:
                    if action == "edit":
                        future = pool.submit(
                            client.patch,
                            f"/api/v1/patients/evolutions/{evolution_id}/draft",
                            json={"version": draft.json()["version"], "description": "Texto alterado"}, headers=dentist,
                        )
                    else:
                        future = pool.submit(
                            client.post,
                            f"/api/v1/patients/evolutions/{evolution_id}/finalize",
                            headers=dentist,
                        )
                    assert reached_lock.wait(timeout=5)
                    # O sinal marca a chegada ao SELECT; o servidor confirma
                    # que a requisição realmente está esperando a linha.
                    deadline = time.monotonic() + 5
                    waiting = False
                    while time.monotonic() < deadline:
                        with pg_engine.connect() as connection:
                            waiting = connection.scalar(text(
                                "SELECT count(*) FROM pg_stat_activity "
                                "WHERE wait_event_type = 'Lock' "
                                "AND query ILIKE '%clinical_evolutions%' "
                                "AND pid <> pg_backend_pid()"
                            )) >= 1
                        if waiting:
                            break
                        time.sleep(0.05)
                    assert waiting, "A mutação não aguardou o bloqueio PostgreSQL"
                    canceled = client.post(
                        f"/api/v1/appointments/{appointment_id}/cancel",
                        headers=receptionist,
                    )
                    assert canceled.status_code == 200, canceled.text
                    holder.commit()
                    response = future.result(timeout=10)

        # D03 conserva acesso ao histórico por outra origem, mas a consulta
        # vinculada cancelada já não permite editar nem finalizar.
        assert response.status_code == (422 if other_origin else 403), response.text
        if not other_origin:
            assert response.json()["error"]["code"] == "FORBIDDENERROR"
        with Session(pg_engine) as db:
            stored = db.get(ClinicalEvolution, evolution_id)
            assert stored.description == "Texto original"
            assert stored.status == "DRAFT"
            assert stored.finalized_at is None


def test_draft_version_rejects_concurrent_and_stale_edits(pg_engine, identities):
    """Duas conexões com a mesma versão não podem gravar duas edições."""
    _, receptionist_email, dentist_email, _ = identities
    patient_id, appointment_id = _appointment(pg_engine, identities, suffix="qa_version")
    with TestClient(app) as client:
        receptionist = _headers(client, receptionist_email)
        dentist = _headers(client, dentist_email)
        assert client.patch(
            f"/api/v1/appointments/{appointment_id}/status",
            json={"status": "CONFIRMED"}, headers=receptionist,
        ).status_code == 200
        _open_record(client, patient_id, dentist)
        draft = client.post(
            "/api/v1/patients/evolutions",
            json={"patient_id": patient_id, "appointment_id": appointment_id,
                  "description": "Texto inicial"}, headers=dentist,
        )
        assert draft.status_code == 201, draft.text
        evolution_id = draft.json()["id"]
        assert draft.json()["version"] == 1
        url = f"/api/v1/patients/evolutions/{evolution_id}/draft"

        with Session(pg_engine) as holder:
            holder.execute(
                select(ClinicalEvolution.id)
                .where(ClinicalEvolution.id == evolution_id)
                .with_for_update(of=ClinicalEvolution)
            ).scalar_one()
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(
                    client.patch, url,
                    json={"version": 1, "description": description}, headers=dentist,
                ) for description in ("Edição A", "Edição B")]
                deadline = time.monotonic() + 5
                waiting = 0
                while time.monotonic() < deadline:
                    with pg_engine.connect() as connection:
                        waiting = connection.scalar(text(
                            "SELECT count(*) FROM pg_stat_activity "
                            "WHERE wait_event_type = 'Lock' "
                            "AND query ILIKE '%clinical_evolutions%' "
                            "AND pid <> pg_backend_pid()"
                        ))
                    if waiting >= 2:
                        break
                    time.sleep(0.05)
                assert waiting >= 2, "As duas edições não aguardaram o lock"
                holder.commit()
                responses = [future.result(timeout=10) for future in futures]

        assert sorted(response.status_code for response in responses) == [200, 409]
        winner = next(response for response in responses if response.status_code == 200)
        loser = next(response for response in responses if response.status_code == 409)
        assert winner.json()["version"] == 2
        assert loser.json()["error"]["code"] == "CONFLICTERROR"
        assert "Edição A" not in loser.text and "Edição B" not in loser.text

        stale = client.patch(url, json={"version": 1, "notes": "Antiga"}, headers=dentist)
        assert stale.status_code == 409
        for invalid in ({"description": "Sem versão"}, {"version": 0},
                        {"version": "1"}, {"version": None}):
            response = client.patch(url, json=invalid, headers=dentist)
            assert response.status_code == 422, response.text
            assert response.json()["error"]["code"] == "VALIDATION_ERROR"

        current = client.patch(
            url, json={"version": 2, "notes": "Nota atual"}, headers=dentist,
        )
        assert current.status_code == 200, current.text
        assert current.json()["version"] == 3
        assert current.json()["description"] == winner.json()["description"]

        with patch.object(RecordRepository, "update_evolution", side_effect=RuntimeError):
            with pytest.raises(RuntimeError):
                client.patch(url, json={"version": 3, "notes": "Falha parcial"}, headers=dentist)
        with Session(pg_engine) as db:
            stored = db.get(ClinicalEvolution, evolution_id)
            assert stored.version == 3
            assert stored.notes == "Nota atual"
            assert stored.description == winner.json()["description"]

        # Outro autor com vínculo e outro dentista em clínica diferente
        # continuam sem poder usar a versão correta para alterar o registro.
        with Session(pg_engine, expire_on_commit=False) as db:
            second_user = User(
                clinic_id=identities[0], full_name="Segundo dentista",
                email="segundo.version@example.test", password_hash="hash-ficticio",
                cpf="00000000011", role=Role.DENTIST,
            )
            foreign_clinic = Clinic(
                name="Clínica externa", cnpj="00000000000292",
                email="externa.version@example.test",
            )
            db.add_all([second_user, foreign_clinic])
            db.flush()
            foreign_user = User(
                clinic_id=foreign_clinic.id, full_name="Dentista externo",
                email="externo.version@example.test", password_hash="hash-ficticio",
                cpf="00000000012", role=Role.DENTIST,
            )
            db.add(foreign_user)
            db.flush()
            second_dentist = Dentist(
                user_id=second_user.id, cro_number="54321", cro_state="PE",
            )
            db.add(second_dentist)
            db.flush()
            second_appointment = Appointment(
                clinic_id=identities[0], patient_id=patient_id,
                dentist_id=second_dentist.id,
                scheduled_at=datetime.datetime.now(datetime.timezone.utc)
                + datetime.timedelta(days=2),
                duration_minutes=30, status=AppointmentStatus.CONFIRMED,
            )
            db.add(second_appointment)
            db.flush()
            receptionist_id = db.scalar(
                select(User.id).where(User.email == receptionist_email)
            )
            db.add(ClinicalAccessGrant(
                appointment_id=second_appointment.id, clinic_id=identities[0],
                patient_id=patient_id, dentist_id=second_dentist.id,
                granted_at=datetime.datetime.now(datetime.timezone.utc),
                confirmed_by_user_id=receptionist_id,
            ))
            db.commit()
            second_headers = {"Authorization": f"Bearer {create_access_token(second_user)}"}
            foreign_headers = {"Authorization": f"Bearer {create_access_token(foreign_user)}"}
        for headers in (second_headers, foreign_headers):
            denied = client.patch(
                url, json={"version": 3, "description": "Sem autoria"}, headers=headers,
            )
            assert denied.status_code == 403, denied.text

        completed = client.patch(
            f"/api/v1/appointments/{appointment_id}/status",
            json={"status": "COMPLETED", "care_occurred_at":
                  (datetime.datetime.now(datetime.timezone.utc)
                   - datetime.timedelta(minutes=5)).isoformat()},
            headers=dentist,
        )
        assert completed.status_code == 200, completed.text
        finalized = client.post(
            f"/api/v1/patients/evolutions/{evolution_id}/finalize", headers=dentist,
        )
        assert finalized.status_code == 200, finalized.text
        assert finalized.json()["version"] == 4
        immutable = client.patch(
            url, json={"version": 4, "description": "Indevida"}, headers=dentist,
        )
        assert immutable.status_code == 422
        with Session(pg_engine) as db:
            stored = db.get(ClinicalEvolution, evolution_id)
            assert stored.status == "FINALIZED"
            assert stored.version == 4


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
        _open_record(client, patient_id, dentist)

        reached_lock = Event()
        original = ClinicalAccessGrantRepository.lock_origin_appointments

        def observe_lock(repository, *, clinic_id, patient_id, dentist_id):
            reached_lock.set()
            return original(
                repository, clinic_id=clinic_id,
                patient_id=patient_id, dentist_id=dentist_id,
            )

        with Session(pg_engine) as holder:
            appointment = holder.execute(
                select(Appointment)
                .where(Appointment.id == appointment_id)
                .with_for_update(of=Appointment)
            ).scalar_one()
            appointment.status = AppointmentStatus.CANCELED

            with patch.object(
                ClinicalAccessGrantRepository, "lock_origin_appointments", observe_lock
            ):
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
                    try:
                        assert reached_lock.wait(timeout=5)
                        # Confirma a espera real antes de cancelar a origem.
                        deadline = time.monotonic() + 5
                        waiting = False
                        while time.monotonic() < deadline:
                            with pg_engine.connect() as connection:
                                waiting = connection.scalar(text(
                                    "SELECT count(*) FROM pg_stat_activity "
                                    "WHERE wait_event_type = 'Lock' "
                                    "AND query ILIKE '%clinical_access_grants%' "
                                    "AND pid <> pg_backend_pid()"
                                )) >= 1
                            if waiting:
                                break
                            time.sleep(0.05)
                        assert waiting, "A criação não aguardou o bloqueio PostgreSQL"
                    finally:
                        holder.commit()
                    response = future.result(timeout=10)

        assert response.status_code == 403, response.text

    with Session(pg_engine) as db:
        assert db.scalar(
            select(func.count()).select_from(MedicalRecord).where(
                MedicalRecord.patient_id == patient_id
            )
        ) == 1
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
        _open_record(client, patient_id, dentist)

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
        ) == 1
        assert db.scalar(
            select(func.count()).select_from(ClinicalEvolution).where(
                ClinicalEvolution.appointment_id == appointment_id
            )
        ) == 0
