"""Protege os ensaios de escrita contra uso acidental do banco da equipe."""

import os
import pytest


@pytest.fixture(autouse=True)
def disposable_database_only():
    if os.getenv("LUMINA_SESSION_PG") != "1":
        pytest.skip("Exige runner de sessão com PostgreSQL descartável.")
    from app import main as m
    assert m.engine.url.database.startswith("lumina_qa_session_")


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from app import main as m
    with TestClient(m.app) as http:
        yield http
