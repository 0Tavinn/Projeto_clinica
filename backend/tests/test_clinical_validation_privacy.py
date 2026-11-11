"""Testes de sigilo em erros de validação clínica."""

import logging

from tests.conftest import auth_headers


def test_invalid_clinical_payload_is_absent_from_response_and_log(
    client, dentist_user, caplog
):
    secret = "SIGILO_CLINICO_FICTICIO_7f39"
    headers = auth_headers(client, dentist_user.email)

    # patient_id ausente provoca erro de validação do corpo inteiro.
    with caplog.at_level(logging.INFO, logger="dental_clinic_api.errors"):
        response = client.post(
            "/api/v1/patients/evolutions",
            json={
                "description": secret,
                "notes": secret,
            },
            headers=headers,
        )

    assert response.status_code == 422, response.text
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert isinstance(error["details"], list)
    assert error["details"]
    assert all("input" not in issue for issue in error["details"])

    assert secret not in response.text
    assert secret not in caplog.text
    assert any(
        record.name == "dental_clinic_api.errors"
        and "validation_error" in record.getMessage()
        for record in caplog.records
    )