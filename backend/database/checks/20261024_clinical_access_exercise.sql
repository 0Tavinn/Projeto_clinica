-- Ensaio estrutural; simula confirmações, não testa autorização nem API.
-- Somente dados fictícios dos bancos descartáveis identificados.
BEGIN;
DO $exercise$
DECLARE
    first_appointment integer;
    second_appointment integer;
    third_appointment integer;
    clinic_value integer;
    patient_value integer;
    other_patient integer;
    dentist_value integer;
    other_dentist integer;
BEGIN
    IF current_database() NOT IN (
        'lumina_acl_new_20261024', 'lumina_acl_upgrade_20261024'
    ) THEN
        RAISE EXCEPTION 'Ensaio permitido apenas nos bancos descartáveis identificados';
    END IF;

    SELECT id, clinic_id, patient_id, dentist_id
      INTO first_appointment, clinic_value, patient_value, dentist_value
      FROM appointments WHERE notes = 'Consulta fictícia A';
    SELECT id INTO second_appointment
      FROM appointments WHERE notes = 'Consulta fictícia B';
    SELECT id, patient_id, dentist_id
      INTO third_appointment, other_patient, other_dentist
      FROM appointments WHERE notes = 'Consulta fictícia C';

    IF first_appointment IS NULL OR second_appointment IS NULL
       OR third_appointment IS NULL THEN
        RAISE EXCEPTION 'Dados fictícios de origem ausentes';
    END IF;
    IF EXISTS (SELECT 1 FROM medical_records WHERE patient_id = patient_value) THEN
        RAISE EXCEPTION 'Ensaio exige prontuário ainda não aberto para o paciente A';
    END IF;
    IF EXISTS (SELECT 1 FROM clinical_access_grants) THEN
        RAISE EXCEPTION 'Ensaio exige tabela de concessões vazia';
    END IF;

    -- Simulação da futura operação de Agenda: estado e concessão na mesma
    -- transação. A FK isolada não comprova essa operação.
    UPDATE appointments SET status = 'CONFIRMED'
      WHERE id IN (first_appointment, second_appointment, third_appointment);
    INSERT INTO clinical_access_grants
        (appointment_id, clinic_id, patient_id, dentist_id)
    VALUES
        (first_appointment, clinic_value, patient_value, dentist_value),
        (second_appointment, clinic_value, patient_value, dentist_value);

    BEGIN
        INSERT INTO clinical_access_grants
            (appointment_id, clinic_id, patient_id, dentist_id)
        VALUES (first_appointment, clinic_value, patient_value, dentist_value);
        RAISE EXCEPTION 'Duplicidade de consulta foi aceita';
    EXCEPTION WHEN unique_violation THEN
        NULL;
    END;

    BEGIN
        INSERT INTO clinical_access_grants
            (appointment_id, clinic_id, patient_id, dentist_id)
        VALUES (third_appointment, clinic_value, other_patient, dentist_value);
        RAISE EXCEPTION 'Dentista diferente da origem foi aceito';
    EXCEPTION WHEN foreign_key_violation THEN
        NULL;
    END;
    BEGIN
        INSERT INTO clinical_access_grants
            (appointment_id, clinic_id, patient_id, dentist_id)
        VALUES (third_appointment, clinic_value, patient_value, other_dentist);
        RAISE EXCEPTION 'Paciente diferente da origem foi aceito';
    EXCEPTION WHEN foreign_key_violation THEN
        NULL;
    END;
    INSERT INTO clinical_access_grants
        (appointment_id, clinic_id, patient_id, dentist_id)
    VALUES (third_appointment, clinic_value, other_patient, other_dentist);

    BEGIN
        UPDATE appointments SET patient_id = other_patient
          WHERE id = first_appointment;
        RAISE EXCEPTION 'Troca de paciente após concessão foi aceita';
    EXCEPTION WHEN foreign_key_violation THEN
        NULL;
    END;
    BEGIN
        UPDATE appointments SET dentist_id = other_dentist
          WHERE id = first_appointment;
        RAISE EXCEPTION 'Troca de dentista após concessão foi aceita';
    EXCEPTION WHEN foreign_key_violation THEN
        NULL;
    END;

    UPDATE appointments SET status = 'COMPLETED' WHERE id = first_appointment;
    UPDATE appointments SET status = 'CANCELED' WHERE id = second_appointment;
    UPDATE appointments SET status = 'NO_SHOW' WHERE id = third_appointment;

    IF (SELECT count(*) FROM clinical_access_grants) <> 3
       OR (SELECT count(*) FROM clinical_access_grants
           WHERE patient_id = patient_value AND dentist_id = dentist_value) <> 2
       OR EXISTS (SELECT 1 FROM medical_records WHERE patient_id = patient_value)
       OR (SELECT count(*) FROM medical_records) <> 1
       OR (SELECT count(*) FROM clinical_evolutions) <> 1 THEN
        RAISE EXCEPTION 'Contagens ou independência do prontuário divergentes';
    END IF;
END;
$exercise$;
COMMIT;
