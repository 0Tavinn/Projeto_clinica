"""Utilitários de QA sem impressão de tokens, senhas ou conteúdo clínico."""

import time
import jwt
from sqlalchemy import text
from app import main as m


def bearer(token):
    return {"Authorization": "Bearer " + token}


def login(client, role="dentista"):
    response = client.post("/api/v1/auth/login", json={
        "email": role + ".demo@example.com", "password": "DemoLumina2026!"})
    assert response.status_code == 200
    return response.json()["access_token"]


def unlock(client, access):
    response = client.post("/api/v1/auth/clinical-unlock", headers=bearer(access),
                           json={"password": "ClinicaDemo2026!"})
    assert response.status_code == 200
    return response.json()["clinical_token"]


def user_id(client, access):
    response = client.get("/api/v1/auth/me", headers=bearer(access))
    assert response.status_code == 200
    return response.json()["id"]


def state(identifier):
    with m.engine.connect() as db:
        row = db.execute(text("""SELECT session_version,clinical_version FROM users
            WHERE id=:id"""), {"id": identifier}).mappings().one()
        return dict(row)


def audit_count(identifier, action):
    with m.engine.connect() as db:
        return db.execute(text("""SELECT count(*) FROM audit_logs
            WHERE user_id=:id AND action=:action"""), {"id": identifier, "action": action}).scalar_one()


def signed_like(token, **changes):
    data = jwt.decode(token, m.JWT_SECRET, algorithms=["HS256"])
    data.update(changes)
    return jwt.encode(data, m.JWT_SECRET, algorithm="HS256")


def wait_for_updates(fragment, count=1):
    # A sondagem observa esperas reais no PostgreSQL; não usa sleeps como prova.
    deadline = time.monotonic() + 12
    while time.monotonic() < deadline:
        with m.engine.connect() as db:
            actual = db.execute(text("""SELECT count(*) FROM pg_stat_activity
                WHERE datname=current_database() AND pid<>pg_backend_pid()
                  AND wait_event_type='Lock' AND query ILIKE :fragment"""),
                {"fragment": "%" + fragment + "%"}).scalar_one()
        if actual >= count:
            return
        time.sleep(0.03)
    raise AssertionError("Não foram observadas as esperas de lock exigidas pelo ensaio.")
