"""Filtros SQL e exclusão do próprio agendamento continuam fora do kernel."""

import datetime as dt
import pytest

from app.appointments.models import Appointment, AppointmentStatus
from app.appointments.repository import AppointmentRepository
from app.dentists.models import Dentist
from app.security.roles import Role
from app.users.models import Clinic
from app.patients.models import Patient
from tests.conftest import _make_user


@pytest.mark.parametrize("engine", ["auto", "sequential"])
def test_repository_filters_and_excluding_id(db_session, clinic, dentist_user, monkeypatch, engine):
    from app.core.config import get_settings
    monkeypatch.setattr(get_settings(), "APPOINTMENT_CONFLICT_ENGINE", engine)
    other_clinic = Clinic(name="Outra QA", cnpj="11111111000111", email="other@example.test")
    db_session.add(other_clinic)
    db_session.flush()
    other_user = _make_user(db_session, other_clinic, email="other@example.test",
                            cpf="77777777777", role=Role.DENTIST)
    dentists = [Dentist(user_id=dentist_user.id, cro_number="1", cro_state="PE"),
                Dentist(user_id=other_user.id, cro_number="2", cro_state="PE")]
    patient = Patient(clinic_id=clinic.id, full_name="QA", cpf="12345678901",
                      medical_record_number="OPENCL-FILTER", birth_date=dt.date(1990, 1, 1))
    db_session.add_all(dentists+[patient])
    db_session.flush()
    now = dt.datetime.now(dt.timezone.utc)+dt.timedelta(days=5)
    repository = AppointmentRepository(db_session)
    lookup = dict(clinic_id=clinic.id, dentist_id=dentists[0].id, scheduled_at=now, duration_minutes=30)
    for status in (AppointmentStatus.CANCELED, AppointmentStatus.COMPLETED, AppointmentStatus.NO_SHOW):
        db_session.add(Appointment(clinic_id=clinic.id, patient_id=patient.id,
                                  dentist_id=dentists[0].id, scheduled_at=now,
                                  duration_minutes=30, status=status))
    db_session.add(Appointment(clinic_id=other_clinic.id, patient_id=patient.id,
                              dentist_id=dentists[1].id, scheduled_at=now,
                              duration_minutes=30, status=AppointmentStatus.SCHEDULED))
    db_session.commit()
    assert not repository.has_conflict(**lookup)
    own = Appointment(clinic_id=clinic.id, patient_id=patient.id, dentist_id=dentists[0].id,
                      scheduled_at=now, duration_minutes=30, status=AppointmentStatus.CONFIRMED)
    db_session.add(own)
    db_session.commit()
    assert repository.has_conflict(**lookup)
    assert not repository.has_conflict(**lookup, excluding_id=own.id)
    # Mesmo dentista com clínica diferente também não participa da comparação.
    own.clinic_id = other_clinic.id
    db_session.commit()
    assert not repository.has_conflict(**lookup)
