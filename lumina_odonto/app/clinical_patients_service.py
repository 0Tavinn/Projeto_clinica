"""Seleção clínica pelo vínculo persistente, sem exigir consulta ou evolução."""

from app import clinical_patients_repository as repository


def verify_reader(db, user, dentist_id):
    """Revalida sessão, clínica e cadastro depois de esperar pelos bloqueios."""
    from app import main as m
    current=m.one(db,"SELECT * FROM users WHERE id=:id",id=user["id"])
    m.require(current and current["is_active"] and current["role"]=="DENTIST"
              and current["clinic_id"]==user["clinic_id"]
              and current["session_version"]==user["session_version"]
              and current["clinical_version"]==user["clinical_version"],
              401,"Sessão inválida")
    clinic=m.one(db,"SELECT is_active FROM clinics WHERE id=:id",id=user["clinic_id"])
    m.require(clinic and clinic["is_active"],403,"Clínica inativa")
    m.require(m.dentist_for(db,current)==dentist_id,403,"Perfil profissional alterado")


def list_patients(db, user, *, limit, after_id, query):
    """Pagina IDs candidatos autorizados e omite vínculos revogados durante espera."""
    from app import main as m
    dentist_id=m.dentist_for(db,user)
    verify_reader(db,user,dentist_id)
    search=None
    if query is not None:
        query=query.strip()
        m.require(bool(query),422,"Termo inválido")
        # Pesquisa literal: % e _ não abrem a listagem como curingas SQL.
        search="%"+query.replace("!","!!").replace("%","!%").replace("_","!_")+"%"
    candidates=repository.list_candidate_ids(
        db,clinic_id=user["clinic_id"],dentist_id=dentist_id,
        after_id=after_id,limit=limit+1,search=search,
    )
    page_ids=candidates[:limit]
    repository.lock_patients_and_links(
        db,clinic_id=user["clinic_id"],dentist_id=dentist_id,patient_ids=page_ids)
    verify_reader(db,user,dentist_id)
    items=repository.read_visible_patients(
        db,clinic_id=user["clinic_id"],dentist_id=dentist_id,
        patient_ids=page_ids,search=search)
    # O cursor avança pelos candidatos examinados, mesmo que uma revogação
    # deixe a página menor/vazia. Não inventa total nem promete snapshot entre páginas.
    return {"items":items,"limit":limit,
            "next_after_id":page_ids[-1] if len(candidates)>limit else None}


def get_patient(db, user, patient_id):
    """Bloqueia paciente/vínculo e reutiliza allowed() na decisão individual."""
    from app import main as m
    dentist_id=m.dentist_for(db,user)
    m.allowed(db,user,patient_id)
    repository.lock_patients_and_links(
        db,clinic_id=user["clinic_id"],dentist_id=dentist_id,patient_ids=[patient_id])
    # allowed lê novamente vínculo, usuário, clínica, paciente e profissional.
    m.allowed(db,user,patient_id)
    rows=repository.read_visible_patients(
        db,clinic_id=user["clinic_id"],dentist_id=dentist_id,patient_ids=[patient_id])
    m.require(bool(rows),403,"Acesso clínico não autorizado")
    return rows[0]
