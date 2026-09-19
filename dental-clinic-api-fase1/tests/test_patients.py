from tests.conftest import auth_headers


def test_patient_crud(client, administrator_user):
    headers = auth_headers(client, administrator_user.email)

    create_response = client.post(
        "/api/v1/patients",
        headers=headers,
        json={
            "full_name": "Maria da Silva",
            "cpf": "11122233344",
            "medical_record_number": "PRT-0001",
            "birth_date": "1995-04-12",
            "phone": "81999990010",
            "email": "maria.silva@email.com",
            "address": "Rua das Flores, 100",
        },
    )

    assert create_response.status_code == 201
    patient_id = create_response.json()["id"]

    list_response = client.get("/api/v1/patients", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    get_response = client.get(
        f"/api/v1/patients/{patient_id}",
        headers=headers,
    )
    assert get_response.status_code == 200
    assert get_response.json()["full_name"] == "Maria da Silva"

    update_response = client.patch(
        f"/api/v1/patients/{patient_id}",
        headers=headers,
        json={
            "phone": "81999990099",
            "address": "Rua das Flores, 200",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["phone"] == "81999990099"

    delete_response = client.delete(
        f"/api/v1/patients/{patient_id}",
        headers=headers,
    )
    assert delete_response.status_code == 204

    final_list_response = client.get("/api/v1/patients", headers=headers)
    assert final_list_response.status_code == 200
    assert final_list_response.json() == []