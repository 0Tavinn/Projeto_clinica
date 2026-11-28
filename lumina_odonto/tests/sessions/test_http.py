"""Permissões, validade e revogação exercitadas via HTTP e PostgreSQL real."""
import os
import pytest

if os.getenv("LUMINA_SESSION_PG") != "1":
    pytest.skip("Exige PostgreSQL exclusivo do runner de sessão.", allow_module_level=True)


from datetime import datetime, timezone
import jwt
from app import main as m
from .support import bearer, login, unlock, user_id, state, audit_count, signed_like


def test_login_and_unlock_report_the_actual_jwt_validity(client):
    for role in ["admin", "dentista"]:
        response = client.post("/api/v1/auth/login", json={
            "email": role + ".demo@example.com", "password": "DemoLumina2026!"})
        assert response.status_code == 200
        body = response.json()
        assert set(body) == {"access_token", "token_type", "expires_in"}
        claims = jwt.decode(body["access_token"], m.JWT_SECRET, algorithms=["HS256"])
        assert body["expires_in"] == claims["exp"] - claims["iat"] == 1800
        assert body["token_type"] == "bearer"
    response = client.post("/api/v1/auth/clinical-unlock", headers=bearer(body["access_token"]),
                           json={"password": "ClinicaDemo2026!"})
    clinical = response.json()
    assert response.status_code == 200
    assert set(clinical) == {"clinical_token", "token_type", "expires_in"}
    claims = jwt.decode(clinical["clinical_token"], m.JWT_SECRET, algorithms=["HS256"])
    assert clinical["expires_in"] == claims["exp"] - claims["iat"] == 900


def test_logout_revokes_both_tokens_and_other_logins_for_the_same_user(client):
    access, other = login(client), login(client)
    admin = login(client, "admin")
    clinical = unlock(client, access)
    identifier = user_id(client, access)
    before, events = state(identifier), audit_count(identifier, "SESSION_LOGOUT")
    assert client.get("/api/v1/clinical/patients", headers=bearer(clinical)).status_code == 200
    response = client.post("/api/v1/auth/logout", headers=bearer(access))
    assert response.status_code == 204 and response.content == b""
    for token in [access, other]:
        assert client.get("/api/v1/auth/me", headers=bearer(token)).status_code == 401
    assert client.get("/api/v1/clinical/patients", headers=bearer(clinical)).status_code == 401
    assert client.get("/api/v1/auth/me", headers=bearer(admin)).status_code == 200
    assert state(identifier) == {**before, "session_version": before["session_version"] + 1}
    assert audit_count(identifier, "SESSION_LOGOUT") == events + 1
    assert client.post("/api/v1/auth/logout", headers=bearer(access)).status_code == 401
    assert client.get("/api/v1/auth/me", headers=bearer(login(client))).status_code == 200


def test_clinical_lock_keeps_login_and_allows_new_unlock(client):
    access = login(client)
    clinical = unlock(client, access)
    identifier = user_id(client, access)
    before, events = state(identifier), audit_count(identifier, "CLINICAL_SESSION_LOCKED")
    response = client.post("/api/v1/auth/clinical-lock", headers=bearer(access))
    assert response.status_code == 204 and response.content == b""
    assert client.get("/api/v1/auth/me", headers=bearer(access)).status_code == 200
    assert client.get("/api/v1/clinical/patients", headers=bearer(clinical)).status_code == 401
    assert state(identifier) == {**before, "clinical_version": before["clinical_version"] + 1}
    assert audit_count(identifier, "CLINICAL_SESSION_LOCKED") == events + 1
    fresh = unlock(client, access)
    assert client.get("/api/v1/clinical/patients", headers=bearer(fresh)).status_code == 200


@pytest.mark.parametrize("path", ["/auth/me", "/access-links"])
def test_clinical_token_cannot_be_used_in_administration(client, path):
    token = unlock(client, login(client))
    assert client.get("/api/v1" + path, headers=bearer(token)).status_code == 401


@pytest.mark.parametrize("path", ["/auth/logout", "/auth/clinical-lock"])
@pytest.mark.parametrize("fault", ["missing", "expired", "wrong_signature", "wrong_kind", "legacy"])
def test_session_endpoints_reject_incompatible_tokens(client, path, fault):
    access = login(client)
    if fault == "missing":
        headers = {}
    else:
        if fault == "expired":
            token = signed_like(access, exp=int(datetime.now(timezone.utc).timestamp()) - 60)
        elif fault == "wrong_signature":
            token = jwt.encode({"sub": "2", "type": "access"}, "another-test-secret-00000000000000000", algorithm="HS256")
        elif fault == "wrong_kind":
            token = unlock(client, access)
        else:
            # Mesmo com a chave deste ensaio, o formato legado sem versões não serve.
            token = jwt.encode({"sub": "2", "type": "access"}, m.JWT_SECRET, algorithm="HS256")
        headers = bearer(token)
    assert client.post("/api/v1" + path, headers=headers).status_code == 401


def test_admin_cannot_unlock_or_lock_clinical_content(client):
    access = login(client, "admin")
    assert client.post("/api/v1/auth/clinical-unlock", headers=bearer(access),
                       json={"password": "ClinicaDemo2026!"}).status_code == 403
    assert client.post("/api/v1/auth/clinical-lock", headers=bearer(access)).status_code == 403


@pytest.mark.parametrize("path", ["/auth/logout", "/auth/clinical-lock"])
def test_failed_audit_rolls_back_session_revocation(client, monkeypatch, path):
    access = login(client)
    clinical = unlock(client, access)
    identifier = user_id(client, access)
    before = state(identifier)
    def fail(*args, **kwargs):
        raise RuntimeError("PRIVATE_SESSION_SENTINEL")
    monkeypatch.setattr(m, "audit", fail)
    from fastapi.testclient import TestClient
    with TestClient(m.app, raise_server_exceptions=False) as failing_client:
        response = failing_client.post("/api/v1" + path, headers=bearer(access))
    assert response.status_code == 500
    assert "PRIVATE_SESSION_SENTINEL" not in response.text
    assert state(identifier) == before
    assert client.get("/api/v1/auth/me", headers=bearer(access)).status_code == 200
    assert client.get("/api/v1/clinical/patients", headers=bearer(clinical)).status_code == 200


def test_logout_does_not_revoke_a_user_from_another_clinic(client):
    from sqlalchemy import text
    # Somente no banco exclusivo: cria outra clínica para testar isolamento de sessão.
    with m.engine.begin() as db:
        clinic = db.execute(text("""INSERT INTO clinics (name,cnpj,email)
            VALUES ('Clínica Fictícia Sessão','99999999999991','clinic.session@example.test')
            RETURNING id""")).scalar_one()
        db.execute(text("""INSERT INTO users
            (clinic_id,full_name,email,cpf,role,password_hash)
            SELECT :clinic,'Admin Fictício Outra Clínica','admin.outside@example.test',
                   '99999999992','ADMINISTRATOR',password_hash
            FROM users WHERE email='admin.demo@example.com'"""), {"clinic": clinic})
    other = client.post("/api/v1/auth/login", json={
        "email": "admin.outside@example.test", "password": "DemoLumina2026!"})
    assert other.status_code == 200
    other_access = other.json()["access_token"]
    access = login(client, "admin")
    assert client.post("/api/v1/auth/logout", headers=bearer(access)).status_code == 204
    assert client.get("/api/v1/auth/me", headers=bearer(access)).status_code == 401
    response = client.get("/api/v1/auth/me", headers=bearer(other_access))
    assert response.status_code == 200 and response.json()["clinic_id"] == clinic
    response = client.get("/api/v1/access-links", headers=bearer(other_access))
    assert response.status_code == 200 and response.json() == []
