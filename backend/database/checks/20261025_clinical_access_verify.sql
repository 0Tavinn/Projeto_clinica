-- Somente leitura após reinício do PostgreSQL 16 descartável.
BEGIN READ ONLY;
DO $verify$
DECLARE
    allowed_count integer;
BEGIN
    IF current_database() NOT IN
        ('lumina_acl25_new', 'lumina_acl25_upgrade', 'lumina_acl25_base') THEN
        RAISE EXCEPTION 'Destino não é banco de ensaio ACL25';
    END IF;
    IF (SELECT count(*) FROM clinics) <> 1
       OR (SELECT count(*) FROM users) <> 3
       OR (SELECT count(*) FROM dentists) <> 2
       OR (SELECT count(*) FROM patients) <> 2
       OR (SELECT count(*) FROM appointments) <> 6
       OR (SELECT count(*) FROM medical_records) <> 1
       OR (SELECT count(*) FROM clinical_evolutions) <> 1
       OR (SELECT count(*) FROM clinical_access_grants) <> 5 THEN
        RAISE EXCEPTION 'Contagens mudaram após reinício';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM clinical_access_grants g
        JOIN appointments a ON a.id = g.appointment_id
        WHERE a.notes = 'ACL25 legacy' AND a.status = 'COMPLETED'
          AND g.granted_at = TIMESTAMPTZ '2026-10-19 12:00:00+00'
          AND g.confirmed_by_user_id IS NULL
          AND g.care_occurred_at IS NULL
          AND g.care_recorded_at IS NULL
          AND g.care_recorded_by_user_id IS NULL
    ) THEN
        RAISE EXCEPTION 'Concessão antiga foi modificada';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM medical_records WHERE general_notes = 'Nota fictícia anterior ACL25'
    ) OR NOT EXISTS (
        SELECT 1 FROM clinical_evolutions
        WHERE description = 'Evolução fictícia anterior ACL25'
    ) THEN
        RAISE EXCEPTION 'Dados clínicos antigos não foram preservados';
    END IF;
    IF EXISTS (
        SELECT 1 FROM clinical_access_grants g
        JOIN appointments a ON a.id = g.appointment_id
        WHERE (g.clinic_id, g.patient_id, g.dentist_id)
           IS DISTINCT FROM (a.clinic_id, a.patient_id, a.dentist_id)
    ) THEN
        RAISE EXCEPTION 'Participantes da origem divergiram';
    END IF;
    SELECT count(*) INTO allowed_count
    FROM clinical_access_grants g
    JOIN appointments a ON a.id = g.appointment_id
    JOIN patients p ON p.id = g.patient_id
    JOIN dentists d ON d.id = g.dentist_id
    JOIN users reader ON reader.id = d.user_id
    WHERE p.medical_record_number = 'ACL25-P-A'
      AND d.cro_number = 'ACL25-A'
      AND reader.is_active AND reader.role = 'DENTIST'
      AND reader.clinic_id = g.clinic_id AND p.clinic_id = g.clinic_id
      AND g.confirmed_by_user_id IS NOT NULL
      AND (a.status = 'CONFIRMED'
           OR (a.status = 'COMPLETED'
               AND g.care_occurred_at IS NOT NULL
               AND g.care_recorded_at IS NOT NULL
               AND g.care_recorded_by_user_id IS NOT NULL));
    IF allowed_count <> 1 THEN
        RAISE EXCEPTION 'Fundamentos após reinício: esperado 1, obtido %', allowed_count;
    END IF;
    IF (SELECT status FROM appointments WHERE notes = 'ACL25 canceled') <> 'CANCELED'
       OR (SELECT status FROM appointments WHERE notes = 'ACL25 absent') <> 'NO_SHOW'
       OR (SELECT status FROM appointments WHERE notes = 'ACL25 active') <> 'CANCELED'
       OR (SELECT status FROM appointments WHERE notes = 'ACL25 completed') <> 'COMPLETED'
       OR NOT EXISTS (SELECT 1 FROM users
                      WHERE email = 'r-acl25@example.test'
                        AND NOT is_active AND role = 'ADMINISTRATOR') THEN
        RAISE EXCEPTION 'Estados fictícios após reinício divergiram';
    END IF;
END;
$verify$;
ROLLBACK;
