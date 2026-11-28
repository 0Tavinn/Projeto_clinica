"""Leituras e bloqueios limitados da lista clínica; não encerra transações."""

from sqlalchemy import text

_SCOPE = """
    FROM clinical_access_links l
    JOIN patients p ON p.id=l.patient_id AND p.clinic_id=l.clinic_id
    LEFT JOIN medical_records r ON r.patient_id=p.id
    WHERE l.clinic_id=:clinic AND l.dentist_id=:dentist
      AND l.status='ACTIVE' AND p.is_active
"""
_SEARCH = """
      AND (CAST(:search AS TEXT) IS NULL OR p.full_name ILIKE :search ESCAPE '!'
           OR p.medical_record_number ILIKE :search ESCAPE '!')
"""
_COLUMNS = """SELECT p.id AS patient_id,p.full_name,p.medical_record_number,
              r.id AS medical_record_id,l.id AS access_link_id """


def list_candidate_ids(db, *, clinic_id, dentist_id, after_id, limit, search):
    """Busca apenas IDs; a autorização será reconferida após eventuais esperas."""
    statement = "SELECT p.id " + _SCOPE + _SEARCH + """
        AND p.id>:after ORDER BY p.id LIMIT :limit
    """
    return list(db.execute(text(statement), {
        "clinic":clinic_id,"dentist":dentist_id,"after":after_id,
        "limit":limit,"search":search,
    }).scalars())


def lock_patients_and_links(db, *, clinic_id, dentist_id, patient_ids):
    """Segue patient -> link, como change_link, com ordem crescente de paciente.

    FOR SHARE permite leituras simultâneas e impede revogação até encerrar
    esta requisição. A consulta seguinte usa novo snapshot READ COMMITTED.
    """
    if not patient_ids:
        return
    params={"clinic":clinic_id,"dentist":dentist_id,"ids":patient_ids}
    db.execute(text("""SELECT id FROM patients
        WHERE clinic_id=:clinic AND id=ANY(:ids)
        ORDER BY id FOR SHARE"""), params).all()
    # Não filtra ACTIVE aqui: uma revogação que acabou de confirmar também
    # precisa ser observada pela leitura final, sem conservar o snapshot inicial.
    db.execute(text("""SELECT id FROM clinical_access_links
        WHERE clinic_id=:clinic AND dentist_id=:dentist AND patient_id=ANY(:ids)
        ORDER BY patient_id FOR SHARE"""), params).all()


def read_visible_patients(db, *, clinic_id, dentist_id, patient_ids, search=None):
    """Projeta somente identificação; nunca CPF, contatos ou texto clínico."""
    if not patient_ids:
        return []
    return [dict(row) for row in db.execute(text(
        _COLUMNS + _SCOPE + _SEARCH + " AND p.id=ANY(:ids) ORDER BY p.id"
    ), {"clinic":clinic_id,"dentist":dentist_id,"ids":patient_ids,
        "search":search}).mappings()]


def read_administrative_links(db, *, clinic_id, patient_id, dentist_id, limit, offset):
    """Preserva l.* e o array administrativo, acrescentando nomes e flags.

    Os JOINs também conferem a clínica dos envolvidos; inativos e revogados
    continuam visíveis para gestão, sem conceder elegibilidade para reativar.
    """
    return [dict(row) for row in db.execute(text("""
        SELECT l.*,p.full_name AS patient_full_name,
               p.medical_record_number AS patient_medical_record_number,
               p.is_active AS patient_is_active,
               u.full_name AS dentist_full_name,u.is_active AS dentist_is_active,
               u.id AS dentist_user_id,d.cro_number AS dentist_cro_number,
               d.cro_state AS dentist_cro_state
        FROM clinical_access_links l
        JOIN patients p ON p.id=l.patient_id AND p.clinic_id=l.clinic_id
        JOIN dentists d ON d.id=l.dentist_id
        JOIN users u ON u.id=d.user_id AND u.clinic_id=l.clinic_id
        WHERE l.clinic_id=:clinic
          AND (CAST(:patient AS INTEGER) IS NULL OR l.patient_id=:patient)
          AND (CAST(:dentist AS INTEGER) IS NULL OR l.dentist_id=:dentist)
        ORDER BY l.id LIMIT :limit OFFSET :offset
    """), {"clinic":clinic_id,"patient":patient_id,"dentist":dentist_id,
           "limit":limit,"offset":offset}).mappings()]
