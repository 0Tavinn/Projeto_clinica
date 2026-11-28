import os
import pytest
os.environ.setdefault('DATABASE_URL', 'postgresql+psycopg://lumina:lumina@localhost/lumina')
os.environ.setdefault('JWT_SECRET', 'test-only-not-for-production-00000000')
pytest.importorskip('psycopg')
pytest.importorskip('pwdlib')
from fastapi.testclient import TestClient
from fastapi import HTTPException
from app import main as m
from app.crud import appointment_dto
from pydantic import ValidationError

@pytest.mark.parametrize('value', ['2', True, None, 0, -1])
@pytest.mark.parametrize('model', [m.EvolutionPatch, m.FinalizeIn])
def test_strict_version(model, value):
    with pytest.raises(ValidationError):
        model(version=value)

def test_range_not_exposed():
    assert appointment_dto({'id': 1, 'scheduled_period': object()}) == {'id': 1}

def test_validation_no_echo():
    m.app.dependency_overrides[m.clinical_user] = lambda: {}
    m.app.dependency_overrides[m.db_dep] = lambda: None
    try:
        response = TestClient(m.app).post('/api/v1/evolutions', json={'description': 'SECRET_SENTINEL'})
        assert response.status_code == 422
        assert 'SECRET_SENTINEL' not in response.text
    finally:
        m.app.dependency_overrides.clear()

def test_revocation_during_compute(monkeypatch):
    class DB:
        def rollback(self): pass
    calls = []
    def allowed(*args, **kwargs):
        calls.append(1)
        if len(calls) == 2: raise HTTPException(403)
        return 1
    monkeypatch.setattr(m, 'allowed', allowed)
    monkeypatch.setattr(m, 'allrows', lambda *a, **kw: [{'description':'texto', 'patient_id':7}])
    with pytest.raises(HTTPException) as exc:
        m.search('texto', 7, 'cpu', 0, {}, DB())
    assert exc.value.status_code == 403
