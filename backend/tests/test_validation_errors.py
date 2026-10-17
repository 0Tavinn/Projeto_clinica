import logging

from tests.conftest import auth_headers


def test_validation_error_does_not_log_or_return_submitted_password(
    client, administrator_user, caplog
):
    headers = auth_headers(client, administrator_user.email)
    submitted_value = "S6SHRT"

    with caplog.at_level(logging.INFO, logger="dental_clinic_api.errors"):
        response = client.post(
            "/api/v1/users",
            headers=headers,
            json={
                "full_name": "Usuário Exemplo",
                "email": "teste@example.com",
                "password": submitted_value,
                "cpf": "33344455566",
                "role": "RECEPTIONIST",
            },
        )

    assert response.status_code == 422
    assert submitted_value not in caplog.text
    assert submitted_value not in response.text
    assert all("input" not in issue and "ctx" not in issue for issue in response.json()["error"]["details"])
