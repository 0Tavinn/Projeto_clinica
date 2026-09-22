import os

# Testes usam SQLite em memória, nunca o PostgreSQL de desenvolvimento.
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.security.hashing import hash_password
from app.security.rate_limit import login_rate_limiter
from app.security.roles import Role
from app.users.models import Clinic, User

TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(
    bind=TEST_ENGINE,
    autoflush=False,
    autocommit=False,
)


@pytest.fixture(scope="function", autouse=True)
def _setup_database():
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture(scope="function", autouse=True)
def _reset_rate_limiter():
    login_rate_limiter._hits.clear()
    yield
    login_rate_limiter._hits.clear()


@pytest.fixture
def db_session():
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def clinic(db_session):
    clinic = Clinic(
        name="Clínica Teste",
        cnpj="00000000000191",
        phone="81999990000",
        email="contato@clinica.example.com",
        address="Rua de Teste, 1",
    )
    db_session.add(clinic)
    db_session.commit()
    db_session.refresh(clinic)
    return clinic


def _make_user(
    db_session,
    clinic,
    *,
    email,
    cpf,
    role,
    password="Senha@1234",
    is_active=True,
):
    user = User(
        clinic_id=clinic.id,
        email=email,
        password_hash=hash_password(password),
        full_name=email.split("@")[0].title(),
        cpf=cpf,
        phone="81999990000",
        role=role,
        is_active=is_active,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def administrator_user(db_session, clinic):
    return _make_user(
        db_session,
        clinic,
        email="admin@clinica.example.com",
        cpf="00000000001",
        role=Role.ADMINISTRATOR,
    )


@pytest.fixture
def receptionist_user(db_session, clinic):
    return _make_user(
        db_session,
        clinic,
        email="recepcao@clinica.example.com",
        cpf="00000000002",
        role=Role.RECEPTIONIST,
    )


@pytest.fixture
def dentist_user(db_session, clinic):
    return _make_user(
        db_session,
        clinic,
        email="dentista@clinica.example.com",
        cpf="00000000003",
        role=Role.DENTIST,
    )


@pytest.fixture
def inactive_user(db_session, clinic):
    return _make_user(
        db_session,
        clinic,
        email="inativo@clinica.example.com",
        cpf="00000000004",
        role=Role.RECEPTIONIST,
        is_active=False,
    )


def login_and_get_token(
    client,
    email: str,
    password: str = "Senha@1234",
) -> str:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth_headers(
    client,
    email: str,
    password: str = "Senha@1234",
) -> dict:
    token = login_and_get_token(client, email, password)
    return {"Authorization": f"Bearer {token}"}