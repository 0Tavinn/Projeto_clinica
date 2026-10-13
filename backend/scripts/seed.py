"""
Seed local para criar a clínica e os dados mínimos de demonstração.

Cria ou reaproveita:
- uma clínica;
- um administrador;
- uma recepcionista;
- um dentista com perfil profissional;
- dois pacientes.

Uso:
    python -m scripts.seed

O banco PostgreSQL deve existir previamente. Este script não cria tabelas e
não executa migrações Alembic.
"""

import os
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.appointments.models import Appointment, AppointmentStatus
from app.core.database import SessionLocal
from app.dentists.models import Dentist
from app.patients.models import Patient
from app.security.hashing import hash_password
from app.security.roles import Role
from app.users.models import Clinic, User
from app.users.repository import UserRepository

def get_or_create_clinic(db) -> Clinic:
    cnpj = os.getenv("SEED_CLINIC_CNPJ", "00000000000191")

    clinic = db.execute(
        select(Clinic).where(Clinic.cnpj == cnpj)
    ).scalar_one_or_none()

    if clinic:
        return clinic

    clinic = Clinic(
        name=os.getenv("SEED_CLINIC_NAME", "Clínica Odontológica Demo"),
        cnpj=cnpj,
        phone=os.getenv("SEED_CLINIC_PHONE", "81999990000"),
        email=os.getenv("SEED_CLINIC_EMAIL", "contato@clinica.demo"),
        address=os.getenv(
            "SEED_CLINIC_ADDRESS",
            "Endereço de demonstração",
        ),
        is_active=True,
    )
    db.add(clinic)
    db.commit()
    db.refresh(clinic)

    print(f"[seed] clínica criada: {clinic.name}")
    return clinic


def get_or_create_administrator(db, clinic: Clinic) -> User:
    email = os.getenv("SEED_ADMIN_EMAIL", "admin@clinica.demo").lower()
    password = os.getenv("SEED_ADMIN_PASSWORD", "Admin@123")
    cpf = os.getenv("SEED_ADMIN_CPF", "00000000000")
    phone = os.getenv("SEED_ADMIN_PHONE", "81999990001")

    repository = UserRepository(db)
    existing = repository.get_by_email(email)

    if existing:
        print(f"[seed] administrador já existe: {email}")
        return existing

    user = User(
        clinic_id=clinic.id,
        full_name=os.getenv("SEED_ADMIN_NAME", "Administrador Demo"),
        email=email,
        password_hash=hash_password(password),
        cpf=cpf,
        phone=phone,
        role=Role.ADMINISTRATOR,
        is_active=True,
    )

    created = repository.create(user)
    print(f"[seed] administrador criado: {email}")
    return created

def get_or_create_user(
    db,
    clinic: Clinic,
    *,
    full_name: str,
    email: str,
    password: str,
    cpf: str,
    phone: str,
    role: Role,
) -> User:
    existing = db.execute(
        select(User).where(User.email == email.lower())
    ).scalar_one_or_none()

    if existing:
        print(f"[seed] usuário já existe: {email}")
        return existing

    user = User(
        clinic_id=clinic.id,
        full_name=full_name,
        email=email.lower(),
        password_hash=hash_password(password),
        cpf=cpf,
        phone=phone,
        role=role,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    print(f"[seed] usuário criado: {email}")
    return user

def get_or_create_receptionist(db, clinic: Clinic) -> User:
    return get_or_create_user(
        db,
        clinic,
        full_name="Recepcionista Seed",
        email="recepcao.seed@clinica.demo",
        password="Demo@123",
        cpf="98765432100",
        phone="81991112222",
        role=Role.RECEPTIONIST,
    )

def get_or_create_dentist(
    db,
    clinic: Clinic,
    *,
    full_name: str,
    email: str,
    password: str,
    cpf: str,
    phone: str,
    cro_number: str,
    cro_state: str,
    specialty: str,
) -> Dentist:
    user = get_or_create_user(
        db,
        clinic,
        full_name=full_name,
        email=email,
        password=password,
        cpf=cpf,
        phone=phone,
        role=Role.DENTIST,
    )

    dentist = db.execute(
        select(Dentist).where(Dentist.user_id == user.id)
    ).scalar_one_or_none()

    if dentist:
        print(f"[seed] dentista já existe: {user.email}")
        return dentist

    dentist = Dentist(
        user_id=user.id,
        cro_number=cro_number,
        cro_state=cro_state,
        specialty=specialty,
    )

    db.add(dentist)
    db.commit()
    db.refresh(dentist)

    print(f"[seed] dentista criado: {user.full_name}")
    return dentist

def get_or_create_patient(
    db,
    clinic: Clinic,
    *,
    full_name: str,
    cpf: str,
    medical_record_number: str,
    birth_date: date,
    phone: str,
    email: str,
    address: str,
) -> Patient:
    patient = db.execute(
        select(Patient).where(
            Patient.clinic_id == clinic.id,
            Patient.medical_record_number == medical_record_number,
        )
    ).scalar_one_or_none()

    if patient:
        print(f"[seed] paciente já existe: {medical_record_number}")
        return patient

    patient = Patient(
        clinic_id=clinic.id,
        full_name=full_name,
        cpf=cpf,
        medical_record_number=medical_record_number,
        birth_date=birth_date,
        phone=phone,
        email=email,
        address=address,
        is_active=True,
    )

    db.add(patient)
    db.commit()
    db.refresh(patient)

    print(f"[seed] paciente criado: {full_name}")
    return patient

def get_or_create_appointment(
    db,
    clinic: Clinic,
    *,
    patient: Patient,
    dentist: Dentist,
    scheduled_at: datetime,
    status: AppointmentStatus,
    notes: str,
    duration_minutes: int = 30,
) -> Appointment:
    appointment = db.execute(
        select(Appointment).where(
            Appointment.clinic_id == clinic.id,
            Appointment.notes == notes,
        )
    ).scalar_one_or_none()

    if appointment:
        print(f"[seed] agendamento já existe: {notes}")
        return appointment

    appointment = Appointment(
        clinic_id=clinic.id,
        patient_id=patient.id,
        dentist_id=dentist.id,
        scheduled_at=scheduled_at,
        status=status,
        notes=notes,
        duration_minutes=duration_minutes,
    )

    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    print(
        f"[seed] agendamento criado: "
        f"{patient.full_name} em {scheduled_at.isoformat()}"
    )
    return appointment

def main() -> None:
    db = SessionLocal()

    try:
        clinic = get_or_create_clinic(db)
        administrator = get_or_create_administrator(db, clinic)
        receptionist_one = get_or_create_receptionist(db, clinic)

        receptionist_two = get_or_create_user(
            db,
            clinic,
            full_name="Recepcionista Seed Dois",
            email="recepcao.dois.seed@clinica.demo",
            password="Demo@123",
            cpf="70000000005",
            phone="81992223333",
            role=Role.RECEPTIONIST,
        )

        dentists = [
            get_or_create_dentist(
                db,
                clinic,
                full_name="Dra. Helena Martins",
                email="dentista.seed@clinica.demo",
                password="Demo@123",
                cpf="24681357928",
                phone="81993334444",
                cro_number="SEED-2026-001",
                cro_state="PE",
                specialty="Clínica Geral",
            ),
            get_or_create_dentist(
                db,
                clinic,
                full_name="Dr. Marcos Almeida",
                email="marcos.dentista.seed@clinica.demo",
                password="Demo@123",
                cpf="70000000001",
                phone="81993334445",
                cro_number="SEED-2026-002",
                cro_state="PE",
                specialty="Ortodontia",
            ),
            get_or_create_dentist(
                db,
                clinic,
                full_name="Dra. Beatriz Santos",
                email="beatriz.dentista.seed@clinica.demo",
                password="Demo@123",
                cpf="70000000002",
                phone="81993334446",
                cro_number="SEED-2026-003",
                cro_state="PE",
                specialty="Endodontia",
            ),
            get_or_create_dentist(
                db,
                clinic,
                full_name="Dr. Lucas Ferreira",
                email="lucas.dentista.seed@clinica.demo",
                password="Demo@123",
                cpf="70000000003",
                phone="81993334447",
                cro_number="SEED-2026-004",
                cro_state="PE",
                specialty="Periodontia",
            ),
            get_or_create_dentist(
                db,
                clinic,
                full_name="Dra. Renata Costa",
                email="renata.dentista.seed@clinica.demo",
                password="Demo@123",
                cpf="70000000004",
                phone="81993334448",
                cro_number="SEED-2026-005",
                cro_state="PE",
                specialty="Odontopediatria",
            ),
        ]

        dentist = dentists[0]

        patient_one = get_or_create_patient(
            db,
            clinic,
            full_name="Paciente Seed Um",
            cpf="13579246828",
            medical_record_number="SEED-PAC-001",
            birth_date=date(1990, 5, 10),
            phone="81995556666",
            email="paciente.um@clinica.demo",
            address="Rua de Demonstração, 100, Recife - PE",
        )

        patient_two = get_or_create_patient(
            db,
            clinic,
            full_name="Paciente Seed Dois",
            cpf="31415926590",
            medical_record_number="SEED-PAC-002",
            birth_date=date(1985, 8, 20),
            phone="81997778888",
            email="paciente.dois@clinica.demo",
            address="Avenida de Demonstração, 200, Recife - PE",
        )

        patients = [patient_one, patient_two]

        for index in range(3, 51):
            patient = get_or_create_patient(
                db,
                clinic,
                full_name=f"Paciente Seed {index:02d}",
                cpf=f"8{index:010d}",
                medical_record_number=f"SEED-PAC-{index:03d}",
                birth_date=date(
                    1980 + (index % 25),
                    (index % 12) + 1,
                    (index % 28) + 1,
                ),
                phone=f"8199{index:07d}",
                email=f"paciente.seed.{index:02d}@clinica.demo",
                address=f"Rua de Demonstração, {100 + index}, Recife - PE",
            )
            patients.append(patient)

        local_timezone = ZoneInfo("America/Recife")

        base_datetime = datetime.now(local_timezone) + timedelta(days=30)
        first_appointment_time = base_datetime.replace(
            hour=9,
            minute=0,
            second=0,
            microsecond=0,
        )
        second_appointment_time = first_appointment_time + timedelta(hours=1)

        appointment_one = get_or_create_appointment(
            db,
            clinic,
            patient=patient_one,
            dentist=dentist,
            scheduled_at=first_appointment_time,
            status=AppointmentStatus.SCHEDULED,
            notes="[SEED-S5-001] Consulta inicial de demonstração",
            duration_minutes=30,
        )

        appointment_two = get_or_create_appointment(
            db,
            clinic,
            patient=patient_two,
            dentist=dentist,
            scheduled_at=second_appointment_time,
            status=AppointmentStatus.CONFIRMED,
            notes="[SEED-S5-002] Consulta confirmada de demonstração",
            duration_minutes=30,
        )

        print("[seed] concluído.")
        print(f"[seed] administrador: {administrator.email}")
        print(
            f"[seed] recepcionistas: "
            f"{receptionist_one.email}, {receptionist_two.email}"
        )
        print(
            f"[seed] dentistas: "
            f"{', '.join(item.full_name for item in dentists)}"
        )
        print(f"[seed] pacientes: {patient_one.id}, {patient_two.id}")
        print(
            f"[seed] agendamentos: "
            f"{appointment_one.id}, {appointment_two.id}"
        )
        print(f"[seed] total de pacientes seed: {len(patients)}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()