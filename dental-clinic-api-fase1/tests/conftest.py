import os

# Precisa ser definido ANTES de qualquer import de app.* (get_settings usa
# lru_cache na primeira chamada). Testes rodam sempre contra SQLite
# in-memory, nunca contra o MySQL de desenvolvimento/produção.
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
TestSessionLocal = sessionmaker(bind=TEST_ENGINE, autoflush=False, autocommit=False)


@pytest.fixture(scope="function", autouse=True)
def _setup_database():
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture(scope="function", autouse=True)
def _reset_rate_limiter():
    # O rate limiter de login é um singleton em memória (por design — ver
    # docstring de app.security.rate_limit). Sem resetar entre testes, o IP
    # fixo do TestClient acumularia tentativas de um teste para o outro.
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
    c = Clinic(name="Clínica Teste")
    db_session.add(c)
    db_session.commit()
    db_session.refresh(c)
    return c


def _make_user(db_session, clinic, *, email, role, password="Senha@1234", is_active=True):
    user = User(
        clinic_id=clinic.id,
        email=email,
        hashed_password=hash_password(password),
        full_name=email.split("@")[0].title(),
        role=role,
        is_active=is_active,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def receptionist_user(db_session, clinic):
    return _make_user(
        db_session, clinic, email="recepcao@clinica.example.com", role=Role.RECEPTIONIST
    )


@pytest.fixture
def dentist_user(db_session, clinic):
    return _make_user(
        db_session, clinic, email="dentista@clinica.example.com", role=Role.DENTIST
    )


@pytest.fixture
def patient_user(db_session, clinic):
    """Perfil modelado, mas ainda não ativo no MVP — usado para testar RBAC."""
    return _make_user(
        db_session, clinic, email="paciente@clinica.example.com", role=Role.PATIENT
    )


@pytest.fixture
def inactive_user(db_session, clinic):
    return _make_user(
        db_session,
        clinic,
        email="inativo@clinica.example.com",
        role=Role.RECEPTIONIST,
        is_active=False,
    )


def login_and_get_token(client, email: str, password: str = "Senha@1234") -> str:
    response = client.post(
        "/api/v1/auth/login", data={"username": email, "password": password}
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth_headers(client, email: str, password: str = "Senha@1234") -> dict:
    token = login_and_get_token(client, email, password)
    return {"Authorization": f"Bearer {token}"}
