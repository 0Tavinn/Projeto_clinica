"""Verificação de elegibilidade para acessar conteúdo clínico."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.exceptions import ForbiddenError, InactiveUserError, NotFoundError
from app.dentists.models import Dentist
from app.patients.models import Patient
from app.records.access_repository import ClinicalAccessGrantRepository
from app.security.roles import Role
from app.users.models import Clinic, User


def require_clinical_access(
    db: Session, *, current_user: User, patient_id: int
) -> tuple[Patient, Dentist]:
    """Exige leitor elegível e ao menos uma origem assistencial válida.

    A evidência pertence à dupla paciente–dentista na clínica. O cadastro
    profissional e o usuário são conferidos novamente em cada requisição.
    """
    if not current_user.is_active:
        raise InactiveUserError()
    if current_user.role is not Role.DENTIST:
        raise ForbiddenError("Apenas dentistas podem acessar conteúdo clínico.")

    clinic = db.get(Clinic, current_user.clinic_id)
    if clinic is None or not clinic.is_active:
        raise ForbiddenError("Clínica indisponível para acesso clínico.")

    dentist = db.execute(
        select(Dentist).where(Dentist.user_id == current_user.id)
    ).scalar_one_or_none()
    if (
        dentist is None
        or not dentist.cro_number.strip()
        or not dentist.cro_state.strip()
    ):
        raise ForbiddenError("Cadastro profissional indisponível.")

    patient = db.get(Patient, patient_id)
    if patient is None:
        raise NotFoundError("Paciente não encontrado no sistema.")
    if patient.clinic_id != current_user.clinic_id:
        raise ForbiddenError("Acesso negado: Este paciente pertence a outra clínica.")

    # D06 ainda não definiu uma regra clínica para paciente inativo.
    if not ClinicalAccessGrantRepository(db).has_valid_origin(
        clinic_id=current_user.clinic_id,
        patient_id=patient.id,
        dentist_id=dentist.id,
    ):
        raise ForbiddenError("Não há vínculo assistencial válido para este paciente.")

    return patient, dentist