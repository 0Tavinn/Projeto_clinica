from sqlalchemy import select

from app.dentists.models import Dentist
from app.security.roles import Role
from app.users.models import Clinic, User
from tests.conftest import _make_user, auth_headers


def _user_payload(*, email, cpf, role="DENTIST", cro="12345"):
    payload = {
        "full_name": "Profissional da Agenda",
        "email": email,
        "password": "Senha@1234",
        "cpf": cpf,
        "phone": "81999990000",
        "role": role,
    }
    if role == "DENTIST":
        payload.update(
            {
                "cro_number": cro,
                "cro_state": "pe",
                "specialty": "Ortodontia",
            }
        )
    return payload


def test_post_users_creates_dentist_profile_in_same_flow(
    client, db_session, administrator_user
):
    headers = auth_headers(client, administrator_user.email)
    response = client.post(
        "/api/v1/users",
        headers=headers,
        json=_user_payload(
            email="novo.dentista@clinica.example.com",
            cpf="00000000101",
        ),
    )
    assert response.status_code == 201, response.text

    user = db_session.execute(
        select(User).where(User.email == "novo.dentista@clinica.example.com")
    ).scalar_one()
    dentist = db_session.execute(
        select(Dentist).where(Dentist.user_id == user.id)
    ).scalar_one()
    assert user.role is Role.DENTIST
    assert dentist.cro_number == "12345"
    assert dentist.cro_state == "PE"
    assert dentist.specialty == "Ortodontia"


def test_post_users_rolls_back_user_when_dentist_profile_conflicts(
    client, db_session, administrator_user
):
    headers = auth_headers(client, administrator_user.email)
    first = client.post(
        "/api/v1/users",
        headers=headers,
        json=_user_payload(
            email="primeiro.dentista@clinica.example.com",
            cpf="00000000102",
            cro="99999",
        ),
    )
    assert first.status_code == 201

    second_email = "segundo.dentista@clinica.example.com"
    conflict = client.post(
        "/api/v1/users",
        headers=headers,
        json=_user_payload(
            email=second_email,
            cpf="00000000103",
            cro="99999",
        ),
    )
    assert conflict.status_code == 409
    assert (
        db_session.execute(select(User).where(User.email == second_email)).scalar_one_or_none()
        is None
    )


def test_dentist_professional_fields_are_validated(client, administrator_user):
    headers = auth_headers(client, administrator_user.email)
    missing_cro = _user_payload(
        email="sem.cro@clinica.example.com",
        cpf="00000000104",
    )
    missing_cro.pop("cro_number")
    missing_cro_response = client.post(
        "/api/v1/users", headers=headers, json=missing_cro
    )
    assert missing_cro_response.status_code == 422
    missing_cro_error = missing_cro_response.json()["error"]
    assert missing_cro_error["code"] == "VALIDATION_ERROR"
    assert isinstance(missing_cro_error["details"][0]["ctx"]["error"], str)

    receptionist = _user_payload(
        email="recepcao.extra@clinica.example.com",
        cpf="00000000105",
        role="RECEPTIONIST",
    )
    receptionist["cro_number"] = "123"
    receptionist_response = client.post(
        "/api/v1/users", headers=headers, json=receptionist
    )
    assert receptionist_response.status_code == 422
    assert isinstance(
        receptionist_response.json()["error"]["details"][0]["ctx"]["error"],
        str,
    )


def test_non_dentist_user_does_not_create_professional_profile(
    client, db_session, administrator_user
):
    headers = auth_headers(client, administrator_user.email)
    response = client.post(
        "/api/v1/users",
        headers=headers,
        json=_user_payload(
            email="nova.recepcao@clinica.example.com",
            cpf="00000000106",
            role="RECEPTIONIST",
        ),
    )
    assert response.status_code == 201
    user_id = response.json()["id"]
    assert (
        db_session.execute(select(Dentist).where(Dentist.user_id == user_id)).scalar_one_or_none()
        is None
    )


def test_get_dentists_returns_only_active_dentists_from_same_clinic(
    client,
    db_session,
    clinic,
    administrator_user,
    receptionist_user,
    dentist_user,
):
    active_profile = Dentist(
        user_id=dentist_user.id,
        cro_number="11111",
        cro_state="PE",
    )
    inactive_user = _make_user(
        db_session,
        clinic,
        email="dentista.inativo@clinica.example.com",
        cpf="00000000107",
        role=Role.DENTIST,
        is_active=False,
    )
    inactive_profile = Dentist(
        user_id=inactive_user.id,
        cro_number="22222",
        cro_state="PE",
    )
    other_clinic = Clinic(
        name="Outra Clínica",
        cnpj="00000000000272",
        email="outra@clinica.example.com",
        is_active=True,
    )
    db_session.add_all([active_profile, inactive_profile, other_clinic])
    db_session.commit()
    db_session.refresh(other_clinic)
    other_user = _make_user(
        db_session,
        other_clinic,
        email="dentista@outra.example.com",
        cpf="00000000108",
        role=Role.DENTIST,
    )
    db_session.add(
        Dentist(
            user_id=other_user.id,
            cro_number="33333",
            cro_state="PE",
        )
    )
    db_session.commit()

    receptionist_headers = auth_headers(client, receptionist_user.email)
    response = client.get("/api/v1/dentists", headers=receptionist_headers)
    assert response.status_code == 200, response.text
    assert [item["user_id"] for item in response.json()] == [dentist_user.id]
    assert response.json()[0]["full_name"] == dentist_user.full_name
    assert response.json()[0]["is_active"] is True

    dentist_headers = auth_headers(client, dentist_user.email)
    assert client.get("/api/v1/dentists", headers=dentist_headers).status_code == 403

    admin_headers = auth_headers(client, administrator_user.email)
    assert client.get("/api/v1/dentists", headers=admin_headers).status_code == 200
