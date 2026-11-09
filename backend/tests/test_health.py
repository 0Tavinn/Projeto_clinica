def test_health_check_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"


def test_clinical_routes_are_registered_under_api_v1(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert "get" in paths["/api/v1/patients/{patient_id}/record"]
    assert "get" in paths["/api/v1/patients/{patient_id}/evolutions"]
    assert "post" in paths["/api/v1/patients/evolutions"]
    assert "patch" in paths["/api/v1/patients/evolutions/{evolution_id}/draft"]
    assert "post" in paths["/api/v1/patients/evolutions/{evolution_id}/finalize"]
    assert "/patients/{patient_id}/record" not in paths


def test_dentist_uses_single_mapper_and_user_relationship(db_session, dentist_user):
    from sqlalchemy.orm import configure_mappers

    from app.core.database import Base
    from app.dentists.models import Dentist

    configure_mappers()
    dentist_mappers = [
        mapper.class_ for mapper in Base.registry.mappers
        if mapper.local_table.name == "dentists"
    ]
    assert dentist_mappers == [Dentist]

    dentist = Dentist(user_id=dentist_user.id, cro_number="12345", cro_state="PE")
    db_session.add(dentist)
    db_session.commit()
    assert dentist_user.dentist is dentist
    assert dentist.user is dentist_user
