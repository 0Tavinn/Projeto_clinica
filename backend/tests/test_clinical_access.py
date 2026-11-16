from app.dentists.models import Dentist
from tests.conftest import auth_headers


def test_clinical_access_requires_second_factor(
    client, db_session, dentist_user
):
    dentist = Dentist(
        user_id=dentist_user.id,
        cro_number="TEST-CLINICAL",
        cro_state="PE",
    )
    db_session.add(dentist)
    db_session.commit()
    headers = auth_headers(client, dentist_user.email)

    denied = client.get("/api/v1/patients/1/record", headers=headers)
    assert denied.status_code == 401

    unlocked = client.post(
        "/api/v1/auth/clinical-access",
        headers=headers,
        json={"clinical_password": "Prontuario@123"},
    )
    assert unlocked.status_code == 200
    clinical_headers = {
        "Authorization": f"Bearer {unlocked.json()['access_token']}"
    }

    allowed = client.get("/api/v1/patients/1/record", headers=clinical_headers)
    assert allowed.status_code in {200, 404}


def test_clinical_access_rejects_wrong_password(client, dentist_user):
    headers = auth_headers(client, dentist_user.email)
    response = client.post(
        "/api/v1/auth/clinical-access",
        headers=headers,
        json={"clinical_password": "senha-incorreta"},
    )
    assert response.status_code == 401
