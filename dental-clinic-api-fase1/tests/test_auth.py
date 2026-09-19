from tests.conftest import auth_headers


def test_login_success_returns_tokens(client, receptionist_user):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": receptionist_user.email, "password": "Senha@1234"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]


def test_login_wrong_password_is_rejected(client, receptionist_user):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": receptionist_user.email, "password": "senha-errada"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZEDERROR"


def test_login_unknown_email_returns_same_generic_error(client):
    """
    Usuário inexistente deve retornar a MESMA mensagem/status que senha
    incorreta, para não permitir enumeração de contas por diferença de
    resposta.
    """
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "nao-existe@clinica.example.com", "password": "qualquer"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Email ou senha inválidos."


def test_login_inactive_user_is_rejected(client, inactive_user):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": inactive_user.email, "password": "Senha@1234"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INACTIVEUSERERROR"


def test_login_rate_limit_blocks_after_threshold(client, receptionist_user):
    for _ in range(5):
        r = client.post(
            "/api/v1/auth/login",
            data={"username": receptionist_user.email, "password": "senha-errada"},
        )
        assert r.status_code == 401

    blocked = client.post(
        "/api/v1/auth/login",
        data={"username": receptionist_user.email, "password": "senha-errada"},
    )
    assert blocked.status_code == 429


def test_me_returns_current_user(client, dentist_user):
    headers = auth_headers(client, dentist_user.email)
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == dentist_user.email
    assert body["role"] == "DENTIST"
    assert "password_hash" not in body


def test_me_without_token_is_unauthorized(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_me_with_garbage_token_is_unauthorized(client):
    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert response.status_code == 401


def test_refresh_flow_issues_new_valid_access_token(client, receptionist_user):
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": receptionist_user.email, "password": "Senha@1234"},
    )
    refresh_token = login_response.json()["refresh_token"]

    refresh_response = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert refresh_response.status_code == 200
    new_access_token = refresh_response.json()["access_token"]

    me_response = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {new_access_token}"}
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == receptionist_user.email


def test_refresh_rejects_an_access_token_used_as_refresh_token(
    client, receptionist_user
):
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": receptionist_user.email, "password": "Senha@1234"},
    )
    access_token = login_response.json()["access_token"]

    response = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": access_token}
    )
    assert response.status_code == 401
