"""Contratos de validade e encerramento da sessão da API de prontuário."""

from typing import Literal

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int = Field(gt=0, description="Validade do token, em segundos.")


class ClinicalTokenResponse(BaseModel):
    clinical_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int = Field(gt=0, description="Validade da liberação, em segundos.")


def install(app):
    # Segue o registro tardio dos módulos existentes, evitando importação circular.
    from app import main as m

    router = APIRouter(prefix="/api/v1/auth", tags=["Autenticação"])

    @router.post("/logout", status_code=204, response_class=Response)
    def logout(user=Depends(m.access_user), db=Depends(m.db_dep)):
        with db.begin_nested():
            # A versão já existente invalida todos os tokens desta conta nesta API.
            # O predicado é reconferido pelo PostgreSQL após eventual espera pelo lock:
            # uma requisição antiga não pode encerrar uma sessão posterior a um reset.
            changed = m.one(db, """UPDATE users
                SET session_version=session_version+1
                WHERE id=:id AND clinic_id=:clinic AND is_active
                  AND session_version=:version RETURNING id""",
                id=user["id"], clinic=user["clinic_id"], version=user["session_version"])
            m.require(changed is not None, 401, "Sessão inválida")
            m.audit(db, user["id"], "SESSION_LOGOUT", "user", str(user["id"]))
        # A revogação e a auditoria só se tornam efetivas no mesmo commit.
        db.commit()
        return Response(status_code=204)

    @router.post("/clinical-lock", status_code=204, response_class=Response)
    def clinical_lock(user=Depends(m.access_user), db=Depends(m.db_dep)):
        m.require(user["role"] == "DENTIST", 403, "Apenas dentistas")
        m.dentist_for(db, user)
        with db.begin_nested():
            # Bloquear prontuários mantém o login, mas invalida as liberações clínicas.
            # Também confere a sessão: um logout/reset concorrente prevalece.
            changed = m.one(db, """UPDATE users
                SET clinical_version=clinical_version+1
                WHERE id=:id AND clinic_id=:clinic AND is_active AND role='DENTIST'
                  AND session_version=:session AND clinical_version=:clinical RETURNING id""",
                id=user["id"], clinic=user["clinic_id"], session=user["session_version"],
                clinical=user["clinical_version"])
            m.require(changed is not None, 401, "Sessão ou liberação clínica alterada")
            m.audit(db, user["id"], "CLINICAL_SESSION_LOCKED", "user", str(user["id"]))
        db.commit()
        return Response(status_code=204)

    app.include_router(router)
