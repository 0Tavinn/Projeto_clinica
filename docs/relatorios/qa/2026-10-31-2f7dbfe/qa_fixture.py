"""Dados exclusivamente fictícios para banco descartável da execução QA 2026-10-31.

Execute dentro do contêiner API de QA, via stdin, com QA_TEST_PASSWORD no ambiente.
O script não cria esquema e não deve apontar para qualquer banco compartilhado.
"""

import datetime as dt
import json
import os

from app.appointments.models import Appointment, AppointmentStatus
from app.core.database import SessionLocal
from app.dentists.models import Dentist
from app.patients.models import Patient
from app.records.models import MedicalRecord
from app.security.hashing import hash_password
from app.security.roles import Role
from app.users.models import Clinic, User


password = os.environ["QA_TEST_PASSWORD"]
now = dt.datetime.now(dt.timezone.utc)

with SessionLocal() as db:
    if db.get_bind().url.database != "lumina_qa_20261031_2f7dbfe_db":
        raise RuntimeError("Destino não é o banco descartável desta execução QA")
    clinics = {
        "a": Clinic(name="Clínica QA A", cnpj="10000000000001", email="qa-a@example.test"),
        "b": Clinic(name="Clínica QA B", cnpj="10000000000002", email="qa-b@example.test"),
    }
    db.add_all(clinics.values())
    db.flush()

    specifications = [
        ("admin", "a", Role.ADMINISTRATOR, True),
        ("reception", "a", Role.RECEPTIONIST, True),
        ("dentist1", "a", Role.DENTIST, True),
        ("dentist2", "a", Role.DENTIST, True),
        ("no_profile", "a", Role.DENTIST, True),
        ("inactive", "a", Role.DENTIST, False),
        ("dentist_other_clinic", "b", Role.DENTIST, True),
    ]
    users = {}
    for n, (key, clinic_key, role, active) in enumerate(specifications, start=1):
        user = User(
            clinic_id=clinics[clinic_key].id,
            full_name=f"Pessoa QA {key}",
            email=f"{key}.qa31@example.test",
            password_hash=hash_password(password),
            cpf=f"{n:011d}",
            role=role,
            is_active=active,
        )
        users[key] = user
        db.add(user)
    db.flush()

    dentists = {}
    for n, key in enumerate(("dentist1", "dentist2", "inactive", "dentist_other_clinic"), start=1):
        dentist = Dentist(user_id=users[key].id, cro_number=f"QA31{n:04d}", cro_state="PE")
        dentists[key] = dentist
        db.add(dentist)
    db.flush()

    patients = {}
    patient_specs = [
        ("shared", "a"), ("cancel", "a"), ("no_show", "a"),
        ("alternative", "a"), ("continuity", "a"),
        ("legacy", "a"), ("rollback", "a"), ("race_edit", "a"),
        ("race_finalize", "a"), ("double_edit", "a"),
        ("open", "a"), ("other_clinic", "b"),
    ]
    for n, (key, clinic_key) in enumerate(patient_specs, start=1):
        patient = Patient(
            clinic_id=clinics[clinic_key].id,
            full_name=f"Paciente QA {key}",
            cpf=f"{n + 100:011d}",
            medical_record_number=f"QA31-{n:03d}",
            birth_date=dt.date(1990, 1, 1),
        )
        patients[key] = patient
        db.add(patient)
    db.flush()

    db.add(MedicalRecord(patient_id=patients["shared"].id, general_notes="Observação geral fictícia QA"))

    appointment_specs = [
        ("shared_d1", "shared", "dentist1", False, AppointmentStatus.SCHEDULED),
        ("shared_d2", "shared", "dentist2", False, AppointmentStatus.SCHEDULED),
        ("cancel_only", "cancel", "dentist1", True, AppointmentStatus.SCHEDULED),
        ("no_show_only", "no_show", "dentist1", False, AppointmentStatus.SCHEDULED),
        ("alt_one", "alternative", "dentist1", True, AppointmentStatus.SCHEDULED),
        ("alt_two", "alternative", "dentist1", True, AppointmentStatus.SCHEDULED),
        ("continuity_past", "continuity", "dentist1", False, AppointmentStatus.SCHEDULED),
        ("continuity_later", "continuity", "dentist1", True, AppointmentStatus.SCHEDULED),
        ("legacy_confirmed", "legacy", "dentist1", False, AppointmentStatus.CONFIRMED),
        ("rollback", "rollback", "dentist1", True, AppointmentStatus.SCHEDULED),
        ("race_edit", "race_edit", "dentist1", True, AppointmentStatus.SCHEDULED),
        ("race_finalize", "race_finalize", "dentist1", True, AppointmentStatus.SCHEDULED),
        ("double_edit", "double_edit", "dentist1", True, AppointmentStatus.SCHEDULED),
        ("open", "open", "dentist1", True, AppointmentStatus.SCHEDULED),
        ("other_clinic", "other_clinic", "dentist_other_clinic", True, AppointmentStatus.SCHEDULED),
    ]
    appointments = {}
    past_count = future_count = 0
    for key, patient_key, dentist_key, future, status in appointment_specs:
        if future:
            future_count += 1
            scheduled_at = now + dt.timedelta(days=30, minutes=45 * future_count)
        else:
            past_count += 1
            scheduled_at = now - dt.timedelta(days=2) + dt.timedelta(minutes=45 * past_count)
        appointment = Appointment(
            clinic_id=patients[patient_key].clinic_id,
            patient_id=patients[patient_key].id,
            dentist_id=dentists[dentist_key].id,
            scheduled_at=scheduled_at,
            duration_minutes=30,
            status=status,
            notes=f"QA {key}",
        )
        appointments[key] = appointment
        db.add(appointment)
    db.commit()

    print(json.dumps({
        "fixture_utc": now.isoformat(),
        "clinics": {key: value.id for key, value in clinics.items()},
        "users": {key: {"id": value.id, "email": value.email} for key, value in users.items()},
        "dentists": {key: value.id for key, value in dentists.items()},
        "patients": {key: value.id for key, value in patients.items()},
        "appointments": {key: value.id for key, value in appointments.items()},
    }, indent=2))
