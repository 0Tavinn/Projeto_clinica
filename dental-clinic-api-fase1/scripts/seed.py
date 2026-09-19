"""
Script de seed — cria uma clínica e os usuários iniciais (recepcionista e
dentista) para permitir o primeiro login.

Não existe endpoint público de auto-registro no MVP: a criação de usuários
do sistema é uma operação administrativa. Este script cobre o bootstrap
inicial de desenvolvimento/demo.

Uso:
    python -m scripts.seed
    (ou, dentro do container: docker compose exec api python -m scripts.seed)

As credenciais podem ser sobrescritas por variáveis de ambiente
SEED_RECEPTIONIST_EMAIL / SEED_RECEPTIONIST_PASSWORD /
SEED_DENTIST_EMAIL / SEED_DENTIST_PASSWORD — recomendado em qualquer
ambiente que não seja a máquina local do desenvolvedor.
"""
import os

from app.core.database import Base, SessionLocal, engine
from app.security.hashing import hash_password
from app.security.roles import Role
from app.users.models import Clinic, User
from app.users.repository import UserRepository


def _get_or_create_clinic(db) -> Clinic:
    clinic = db.query(Clinic).first()
    if clinic:
        return clinic
    clinic = Clinic(name="Clínica Odontológica Demo")
    db.add(clinic)
    db.commit()
    db.refresh(clinic)
    return clinic


def _get_or_create_user(db, *, clinic: Clinic, email: str, password: str, full_name: str, role: Role) -> User:
    repo = UserRepository(db)
    existing = repo.get_by_email(email)
    if existing:
        print(f"[seed] usuário já existe, pulando: {email}")
        return existing

    user = User(
        clinic_id=clinic.id,
        email=email.lower(),
        hashed_password=hash_password(password),
        full_name=full_name,
        role=role,
        is_active=True,
    )
    created = repo.create(user)
    print(f"[seed] usuário criado: {email} ({role.value})")
    return created


def main() -> None:
    # Cria as tabelas caso ainda não existam (idempotente). Em produção o
    # schema deve vir das migrações Alembic (`alembic upgrade head`); isto
    # aqui é uma rede de segurança para ambientes de desenvolvimento rápido.
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        clinic = _get_or_create_clinic(db)

        _get_or_create_user(
            db,
            clinic=clinic,
            email=os.getenv("SEED_RECEPTIONIST_EMAIL", "recepcao@clinica.demo"),
            password=os.getenv("SEED_RECEPTIONIST_PASSWORD", "Recepcao@123"),
            full_name="Recepção Demo",
            role=Role.RECEPTIONIST,
        )
        _get_or_create_user(
            db,
            clinic=clinic,
            email=os.getenv("SEED_DENTIST_EMAIL", "dentista@clinica.demo"),
            password=os.getenv("SEED_DENTIST_PASSWORD", "Dentista@123"),
            full_name="Dentista Demo",
            role=Role.DENTIST,
        )

        print(
            "[seed] concluído. ATENÇÃO: troque as senhas padrão antes de "
            "usar fora de um ambiente local/demo."
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
