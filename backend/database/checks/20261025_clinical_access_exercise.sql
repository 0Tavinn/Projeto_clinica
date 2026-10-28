-- Ensaio estrutural SQL e de consulta de elegibilidade. Não prova ator HTTP.
-- Rodar após schema novo ou após a migração incremental de 25/10.
BEGIN;

CREATE FUNCTION pg_temp.acl25_has_access(reader_user_id integer, target_patient_id integer)
RETURNS boolean LANGUAGE sql STABLE AS $query$
    SELECT EXISTS (
        SELECT 1
        FROM clinical_access_grants AS g
        JOIN appointments AS a ON a.id = g.appointment_id
        JOIN patients AS p ON p.id = g.patient_id
        JOIN dentists AS d ON d.id = g.dentist_id
        JOIN users AS reader ON reader.id = d.user_id
        JOIN clinics AS c ON c.id = g.clinic_id
        WHERE reader.id = reader_user_id
          AND reader.is_active AND reader.role = 'DENTIST'
          AND c.is_active
          AND reader.clinic_id = g.clinic_id
          AND p.clinic_id = g.clinic_id
          AND g.patient_id = target_patient_id
          AND g.confirmed_by_user_id IS NOT NULL
          AND (
              a.status = 'CONFIRMED'
              OR (a.status = 'COMPLETED'
                  AND g.care_occurred_at IS NOT NULL
                  AND g.care_recorded_at IS NOT NULL
                  AND g.care_recorded_by_user_id IS NOT NULL)
          )
    );
$query$;

DO $exercise$
DECLARE
    clinic_value integer;
    patient_a integer;
    patient_b integer;
    dentist_a integer;
    dentist_b integer;
    reader_a integer;
    reader_b integer;
    receptionist integer;
    legacy_id integer;
    canceled_id integer;
    absent_id integer;
    active_id integer;
    completed_id integer;
    other_id integer;
BEGIN
    IF current_database() NOT IN
        ('lumina_acl25_new', 'lumina_acl25_upgrade', 'lumina_acl25_base') THEN
        RAISE EXCEPTION 'Destino não é banco de ensaio ACL25';
    END IF;
    SELECT id INTO clinic_value FROM clinics WHERE cnpj = '98000000000001';
    SELECT id INTO patient_a FROM patients WHERE medical_record_number = 'ACL25-P-A';
    SELECT id INTO patient_b FROM patients WHERE medical_record_number = 'ACL25-P-B';
    SELECT d.id, d.user_id INTO dentist_a, reader_a
      FROM dentists d WHERE d.cro_number = 'ACL25-A';
    SELECT d.id, d.user_id INTO dentist_b, reader_b
      FROM dentists d WHERE d.cro_number = 'ACL25-B';
    SELECT id INTO receptionist FROM users WHERE email = 'r-acl25@example.test';
    SELECT id INTO legacy_id FROM appointments WHERE notes = 'ACL25 legacy';
    SELECT id INTO canceled_id FROM appointments WHERE notes = 'ACL25 canceled';
    SELECT id INTO absent_id FROM appointments WHERE notes = 'ACL25 absent';
    SELECT id INTO active_id FROM appointments WHERE notes = 'ACL25 active';
    SELECT id INTO completed_id FROM appointments WHERE notes = 'ACL25 completed';
    SELECT id INTO other_id FROM appointments WHERE notes = 'ACL25 other';
    IF clinic_value IS NULL OR patient_a IS NULL OR patient_b IS NULL
       OR dentist_a IS NULL OR dentist_b IS NULL OR reader_a IS NULL
       OR reader_b IS NULL OR receptionist IS NULL OR legacy_id IS NULL
       OR canceled_id IS NULL OR absent_id IS NULL OR active_id IS NULL
       OR completed_id IS NULL OR other_id IS NULL THEN
        RAISE EXCEPTION 'Seed ACL25 incompleto';
    END IF;

    IF pg_temp.acl25_has_access(reader_a, patient_a) THEN
        RAISE EXCEPTION 'Concessão antiga sem procedência autorizou leitura';
    END IF;
    UPDATE appointments SET status = 'COMPLETED' WHERE id = legacy_id;
    IF pg_temp.acl25_has_access(reader_a, patient_a) THEN
        RAISE EXCEPTION 'COMPLETED antigo inferiu confirmação ou realização';
    END IF;
    BEGIN
        UPDATE clinical_access_grants
           SET care_occurred_at = TIMESTAMPTZ '2026-10-24 09:00:00+00',
               care_recorded_at = clock_timestamp(),
               care_recorded_by_user_id = reader_a
         WHERE appointment_id = legacy_id;
        RAISE EXCEPTION 'Realização sem confirmação confiável foi aceita';
    EXCEPTION WHEN check_violation THEN NULL;
    END;

    -- Cada par estado/concessão simula uma operação transacional do backend.
    UPDATE appointments SET status = 'CONFIRMED' WHERE id = canceled_id;
    INSERT INTO clinical_access_grants
        (appointment_id, clinic_id, patient_id, dentist_id, confirmed_by_user_id)
    VALUES (canceled_id, clinic_value, patient_a, dentist_a, receptionist);
    IF NOT pg_temp.acl25_has_access(reader_a, patient_a) THEN
        RAISE EXCEPTION 'Primeira confirmação não sustentou preparação';
    END IF;
    UPDATE appointments SET status = 'CANCELED' WHERE id = canceled_id;
    IF pg_temp.acl25_has_access(reader_a, patient_a) THEN
        RAISE EXCEPTION 'Consulta cancelada sem atendimento manteve preparação';
    END IF;

    UPDATE appointments SET status = 'CONFIRMED' WHERE id = absent_id;
    INSERT INTO clinical_access_grants
        (appointment_id, clinic_id, patient_id, dentist_id, confirmed_by_user_id)
    VALUES (absent_id, clinic_value, patient_a, dentist_a, receptionist);
    UPDATE appointments SET status = 'NO_SHOW' WHERE id = absent_id;
    IF pg_temp.acl25_has_access(reader_a, patient_a) THEN
        RAISE EXCEPTION 'Ausência sem atendimento manteve preparação';
    END IF;

    UPDATE appointments SET status = 'CONFIRMED' WHERE id = active_id;
    INSERT INTO clinical_access_grants
        (appointment_id, clinic_id, patient_id, dentist_id, confirmed_by_user_id)
    VALUES (active_id, clinic_value, patient_a, dentist_a, receptionist);
    IF NOT pg_temp.acl25_has_access(reader_a, patient_a) THEN
        RAISE EXCEPTION 'Outra confirmação não sustentou preparação';
    END IF;
    BEGIN
        INSERT INTO clinical_access_grants
            (appointment_id, clinic_id, patient_id, dentist_id, confirmed_by_user_id)
        VALUES (active_id, clinic_value, patient_a, dentist_a, receptionist);
        RAISE EXCEPTION 'Duplicidade da origem foi aceita';
    EXCEPTION WHEN unique_violation THEN NULL;
    END;
    BEGIN
        INSERT INTO clinical_access_grants
            (appointment_id, clinic_id, patient_id, dentist_id, confirmed_by_user_id)
        VALUES (other_id, clinic_value, patient_a, dentist_a, receptionist);
        RAISE EXCEPTION 'Participantes incompatíveis foram aceitos';
    EXCEPTION WHEN foreign_key_violation THEN NULL;
    END;
    BEGIN
        UPDATE clinical_access_grants SET confirmed_by_user_id = 999999999
         WHERE appointment_id = active_id;
        RAISE EXCEPTION 'Confirmador inexistente foi aceito';
    EXCEPTION WHEN foreign_key_violation THEN NULL;
    END;
    BEGIN
        UPDATE clinical_access_grants
           SET care_occurred_at = TIMESTAMPTZ '2026-10-24 09:00:00+00',
               care_recorded_at = clock_timestamp(),
               care_recorded_by_user_id = 999999999
         WHERE appointment_id = active_id;
        RAISE EXCEPTION 'Responsável pela realização inexistente foi aceito';
    EXCEPTION WHEN foreign_key_violation THEN NULL;
    END;

    -- Falha parcial reverte tanto o estado quanto a alteração de evidência.
    BEGIN
        UPDATE appointments SET status = 'COMPLETED' WHERE id = active_id;
        UPDATE clinical_access_grants
           SET care_occurred_at = TIMESTAMPTZ '2026-10-24 09:00:00+00'
         WHERE appointment_id = active_id;
        RAISE EXCEPTION 'Evidência parcial foi aceita';
    EXCEPTION WHEN check_violation THEN NULL;
    END;
    IF (SELECT status FROM appointments WHERE id = active_id) <> 'CONFIRMED'
       OR (SELECT care_occurred_at FROM clinical_access_grants
           WHERE appointment_id = active_id) IS NOT NULL THEN
        RAISE EXCEPTION 'Rollback parcial falhou';
    END IF;

    UPDATE appointments SET status = 'CONFIRMED' WHERE id = completed_id;
    INSERT INTO clinical_access_grants
        (appointment_id, clinic_id, patient_id, dentist_id, confirmed_by_user_id)
    VALUES (completed_id, clinic_value, patient_a, dentist_a, receptionist);
    UPDATE appointments SET status = 'COMPLETED' WHERE id = completed_id;
    UPDATE clinical_access_grants
       SET care_occurred_at = TIMESTAMPTZ '2026-10-24 09:30:00+00',
           care_recorded_at = clock_timestamp(),
           care_recorded_by_user_id = reader_a
     WHERE appointment_id = completed_id;
    UPDATE appointments SET status = 'CANCELED' WHERE id = active_id;
    IF NOT pg_temp.acl25_has_access(reader_a, patient_a) THEN
        RAISE EXCEPTION 'Atendimento anterior não sustentou continuidade';
    END IF;
    IF pg_temp.acl25_has_access(reader_b, patient_a)
       OR pg_temp.acl25_has_access(receptionist, patient_a) THEN
        RAISE EXCEPTION 'Outro profissional ou recepção obteve acesso';
    END IF;

    -- A identidade histórica do confirmador não depende de sua situação atual.
    UPDATE users SET is_active = false, role = 'ADMINISTRATOR'
      WHERE id = receptionist;
    IF NOT pg_temp.acl25_has_access(reader_a, patient_a) THEN
        RAISE EXCEPTION 'Mudança posterior do confirmador apagou continuidade';
    END IF;
    IF EXISTS (SELECT 1 FROM medical_records WHERE patient_id = patient_a)
       OR NOT EXISTS (SELECT 1 FROM medical_records
                      WHERE general_notes = 'Nota fictícia anterior ACL25')
       OR NOT EXISTS (SELECT 1 FROM clinical_evolutions
                      WHERE description = 'Evolução fictícia anterior ACL25') THEN
        RAISE EXCEPTION 'Prontuário foi aberto ou dados antigos foram alterados';
    END IF;
    IF (SELECT count(*) FROM clinical_access_grants) <> 5
       OR (SELECT count(*) FROM clinical_access_grants
           WHERE patient_id = patient_a AND dentist_id = dentist_a) <> 5 THEN
        RAISE EXCEPTION 'Origens históricas foram apagadas ou duplicadas';
    END IF;
END;
$exercise$;
COMMIT;
