"""
Seed local para criar a clínica inicial e o administrador da demonstração.

Uso:
    python -m scripts.seed

O banco PostgreSQL deve existir previamente. Este script não cria tabelas e
não executa migrações Alembic.
"""
import os

from sqlalchemy import select

from app.core.database import SessionLocal
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


def main() -> None:
    db = SessionLocal()

    try:
        clinic = get_or_create_clinic(db)
        get_or_create_administrator(db, clinic)

        print("[seed] concluído.")
        print("[seed] Em ambiente local, login padrão: admin@clinica.demo")
        print("[seed] Senha padrão: Admin@123")
    finally:
        db.close()


if __name__ == "__main__":
    main()