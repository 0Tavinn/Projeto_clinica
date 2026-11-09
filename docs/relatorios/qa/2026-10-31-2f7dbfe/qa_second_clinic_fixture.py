"""Cria recepção fictícia na segunda clínica do banco exclusivo QA."""

import os

from app.core.database import SessionLocal
from app.dentists.models import Dentist  # noqa: F401: registra o mapeador relacionado
from app.security.hashing import hash_password
from app.security.roles import Role
from app.users.models import User


with SessionLocal() as db:
    if db.get_bind().url.database != "lumina_qa_20261031_2f7dbfe_db":
        raise RuntimeError("Destino não é o banco descartável desta execução QA")
    user = User(
        clinic_id=int(os.environ["QA_CLINIC_B_ID"]),
        full_name="Recepção QA Clínica B",
        email="reception_b.qa31@example.test",
        password_hash=hash_password(os.environ["QA_TEST_PASSWORD"]),
        cpf="00000000051",
        role=Role.RECEPTIONIST,
        is_active=True,
    )
    db.add(user)
    db.commit()
    print("created_second_clinic_reception_id", user.id)
