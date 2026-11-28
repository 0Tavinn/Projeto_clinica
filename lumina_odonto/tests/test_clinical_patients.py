"""Contrato mínimo e privacidade das novas leituras clínicas."""

import os
os.environ.setdefault("DATABASE_URL","postgresql+psycopg://qa:qa@localhost/qa")
os.environ.setdefault("JWT_SECRET","qa-only-clinical-patients-test-secret")
from fastapi.testclient import TestClient
from app.main import app


def test_new_routes_and_minimal_response_contract():
    document=app.openapi()
    assert "get" in document["paths"]["/api/v1/clinical/patients"]
    assert "get" in document["paths"]["/api/v1/clinical/patients/{patient_id}"]
    fields=document["components"]["schemas"]["ClinicalPatient"]["properties"]
    assert set(fields)=={"patient_id","full_name","medical_record_number",
                         "medical_record_id","access_link_id"}
    page=document["components"]["schemas"]["ClinicalPatientPage"]["properties"]
    assert set(page)=={"items","limit","next_after_id"}


def test_new_routes_require_authentication():
    with TestClient(app) as client:
        for path in ("/api/v1/clinical/patients","/api/v1/clinical/patients/1"):
            assert client.get(path).status_code==401
