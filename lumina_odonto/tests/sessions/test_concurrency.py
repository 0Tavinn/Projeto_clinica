"""Comprova a reconferência das versões após espera real de bloqueio."""
import os
import pytest

if os.getenv("LUMINA_SESSION_PG") != "1":
    pytest.skip("Exige PostgreSQL exclusivo do runner de sessão.", allow_module_level=True)


from concurrent.futures import ThreadPoolExecutor
from sqlalchemy import text
from app import main as m
from .support import bearer, login, user_id, state, audit_count, wait_for_updates


def test_two_waiting_logouts_only_revoke_once(client):
    access = login(client)
    identifier = user_id(client, access)
    before, events = state(identifier), audit_count(identifier, "SESSION_LOGOUT")
    with ThreadPoolExecutor(max_workers=2) as executor, m.engine.connect() as blocker:
        blocker.execute(text("SELECT id FROM users WHERE id=:id FOR UPDATE"), {"id": identifier})
        futures = [executor.submit(client.post, "/api/v1/auth/logout", headers=bearer(access)) for _ in range(2)]
        try:
            wait_for_updates("SET session_version=session_version+1", count=2)
        finally:
            # Libera sempre, inclusive se a sondagem falhar, evitando travar o executor.
            blocker.rollback()
        statuses = sorted(future.result(timeout=15).status_code for future in futures)
    assert statuses == [204, 401]
    assert state(identifier) == {**before, "session_version": before["session_version"] + 1}
    assert audit_count(identifier, "SESSION_LOGOUT") == events + 1


@pytest.mark.parametrize("path,column", [
    ("/auth/logout", "session_version"),
    ("/auth/clinical-lock", "clinical_version"),
])
def test_reset_committed_during_wait_wins_over_stale_request(client, path, column):
    access = login(client)
    identifier = user_id(client, access)
    before = state(identifier)
    with ThreadPoolExecutor(max_workers=1) as executor, m.engine.connect() as blocker:
        blocker.execute(text("SELECT id FROM users WHERE id=:id FOR UPDATE"), {"id": identifier})
        future = executor.submit(client.post, "/api/v1" + path, headers=bearer(access))
        try:
            wait_for_updates("SET " + column + "=" + column + "+1")
            # Simula o incremento atômico que um reset confirmado executa.
            blocker.execute(text(f"UPDATE users SET {column}={column}+1 WHERE id=:id"), {"id": identifier})
            blocker.commit()
        finally:
            blocker.rollback()
        response = future.result(timeout=15)
    assert response.status_code == 401
    assert state(identifier) == {**before, column: before[column] + 1}
