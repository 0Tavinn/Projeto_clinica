"""Contrato público da sessão; estes casos não precisam acessar PostgreSQL."""

import os

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://qa:qa@localhost/qa")
os.environ.setdefault("JWT_SECRET", "qa-only-session-contract-not-production")

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.mark.parametrize("path", ["/auth/logout", "/auth/clinical-lock"])
def test_session_endpoints_require_access_token(path):
    with TestClient(app) as client:
        assert client.post("/api/v1" + path).status_code == 401


def test_session_openapi_describes_validity_and_empty_responses():
    spec = app.openapi()
    for name, token_name in [("AccessTokenResponse", "access_token"),
                             ("ClinicalTokenResponse", "clinical_token")]:
        fields = spec["components"]["schemas"][name]["properties"]
        assert set(fields) == {token_name, "token_type", "expires_in"}
        assert fields["expires_in"]["exclusiveMinimum"] == 0
    for path in ["/auth/logout", "/auth/clinical-lock"]:
        response = spec["paths"]["/api/v1" + path]["post"]["responses"]["204"]
        assert "content" not in response
