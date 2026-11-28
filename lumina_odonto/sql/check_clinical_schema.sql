-- Verificações reproduzíveis; execute somente em banco descartável.
-- Comando: psql -v ON_ERROR_STOP=1 -f check_clinical_schema.sql
-- As linhas inseridas são revertidas ao final; sequências podem avançar.
\set ON_ERROR_STOP on
BEGIN;

DO $$
DECLARE
    clinic_key INTEGER;
    admin_key INTEGER;
    dentist_user_key INTEGER;
    dentist_key INTEGER;
    patient_key INTEGER;
    record_key INTEGER;
    appointment_key INTEGER;
    adjacent_key INTEGER;
    link_key INTEGER;
    event_key INTEGER;
BEGIN
    INSERT INTO clinics (name, cnpj, email)
    VALUES ('Verificação descartável', '99999999000199', 'schema-check@example.test')
    RETURNING id INTO clinic_key;
    INSERT INTO users (clinic_id, full_name, email, password_hash, cpf, role)
    VALUES (clinic_key, 'Administrador de teste', 'admin-check@example.test',
        'sem-login', '99999999991', 'ADMINISTRATOR')
    RETURNING id INTO admin_key;
    INSERT INTO users (clinic_id, full_name, email, password_hash, cpf, role)
    VALUES (clinic_key, 'Dentista de teste', 'dentist-check@example.test',
        'sem-login', '99999999992', 'DENTIST')
    RETURNING id INTO dentist_user_key;
    INSERT INTO dentists (user_id, cro_number, cro_state)
    VALUES (dentist_user_key, 'CHECK-999', 'SP') RETURNING id INTO dentist_key;
    INSERT INTO patients (clinic_id, full_name, cpf, medical_record_number, birth_date)
    VALUES (clinic_key, 'Paciente de teste', '99999999993', 'CHECK-999', '1990-01-01')
    RETURNING id INTO patient_key;
    INSERT INTO medical_records (patient_id)
    VALUES (patient_key) RETURNING id INTO record_key;
    BEGIN
        INSERT INTO medical_records (patient_id) VALUES (patient_key);
        RAISE EXCEPTION 'Falhou: prontuário duplicado aceito';
    EXCEPTION WHEN unique_violation THEN NULL;
    END;
    IF EXISTS (SELECT 1 FROM users WHERE id = admin_key
        AND (session_version <> 1 OR clinical_version <> 1)) THEN
        RAISE EXCEPTION 'Falhou: versões iniciais do usuário';
    END IF;
    BEGIN
        UPDATE users SET session_version = 0 WHERE id = admin_key;
        RAISE EXCEPTION 'Falhou: versão de sessão inválida aceita';
    EXCEPTION WHEN check_violation THEN NULL;
    END;
    BEGIN
        UPDATE users SET clinical_version = 0 WHERE id = admin_key;
        RAISE EXCEPTION 'Falhou: versão clínica inválida aceita';
    EXCEPTION WHEN check_violation THEN NULL;
    END;

    INSERT INTO appointments (clinic_id, patient_id, dentist_id, scheduled_at)
    VALUES (clinic_key, patient_key, dentist_key, '2099-01-15 10:00:00+00')
    RETURNING id INTO appointment_key;
    IF NOT EXISTS (SELECT 1 FROM appointments WHERE id = appointment_key
        AND scheduled_period = tstzrange(
            '2099-01-15 10:00:00+00', '2099-01-15 10:30:00+00', '[)')) THEN
        RAISE EXCEPTION 'Falhou: período não calculado';
    END IF;
    INSERT INTO appointments (clinic_id, patient_id, dentist_id, scheduled_at)
    VALUES (clinic_key, patient_key, dentist_key, '2099-01-15 10:30:00+00')
    RETURNING id INTO adjacent_key;
    BEGIN
        INSERT INTO appointments (clinic_id, patient_id, dentist_id, scheduled_at)
        VALUES (clinic_key, patient_key, dentist_key, '2099-01-15 10:15:00+00');
        RAISE EXCEPTION 'Falhou: sobreposição ativa aceita';
    EXCEPTION WHEN exclusion_violation THEN NULL;
    END;
    INSERT INTO appointments (clinic_id, patient_id, dentist_id, scheduled_at, status)
    VALUES (clinic_key, patient_key, dentist_key, '2099-01-15 10:15:00+00', 'CANCELED');
    BEGIN
        UPDATE appointments SET duration_minutes = 0 WHERE id = appointment_key;
        RAISE EXCEPTION 'Falhou: duração inválida aceita';
    EXCEPTION WHEN check_violation THEN NULL;
    END;

    INSERT INTO clinical_evolutions (medical_record_id, dentist_id, description)
    VALUES (record_key, dentist_key, 'Descrição válida, sem consulta vinculada');
    BEGIN
        INSERT INTO clinical_evolutions (medical_record_id, dentist_id, description)
        VALUES (record_key, dentist_key, '   ');
        RAISE EXCEPTION 'Falhou: descrição vazia aceita';
    EXCEPTION WHEN check_violation THEN NULL;
    END;
    BEGIN
        INSERT INTO clinical_evolutions (medical_record_id, dentist_id, description)
        VALUES (record_key, dentist_key, E'\t\n\r ');
        RAISE EXCEPTION 'Falhou: descrição apenas com caracteres de espaço aceita';
    EXCEPTION WHEN check_violation THEN NULL;
    END;
    BEGIN
        INSERT INTO clinical_evolutions (medical_record_id, dentist_id, description, version)
        VALUES (record_key, dentist_key, 'Descrição', 0);
        RAISE EXCEPTION 'Falhou: versão inválida da evolução aceita';
    EXCEPTION WHEN check_violation THEN NULL;
    END;
    BEGIN
        INSERT INTO clinical_evolutions (medical_record_id, dentist_id, description, status)
        VALUES (record_key, dentist_key, 'Descrição', 'FINALIZED');
        RAISE EXCEPTION 'Falhou: finalização sem data aceita';
    EXCEPTION WHEN check_violation THEN NULL;
    END;
    BEGIN
        INSERT INTO clinical_evolutions (
            medical_record_id, dentist_id, description, finalized_at)
        VALUES (record_key, dentist_key, 'Descrição', now());
        RAISE EXCEPTION 'Falhou: rascunho com data de finalização aceito';
    EXCEPTION WHEN check_violation THEN NULL;
    END;
    INSERT INTO clinical_evolutions (
        medical_record_id, dentist_id, description, status, finalized_at)
    VALUES (record_key, dentist_key, 'Finalização válida', 'FINALIZED', now());

    INSERT INTO clinical_access_links (clinic_id, patient_id, dentist_id)
    VALUES (clinic_key, patient_key, dentist_key) RETURNING id INTO link_key;
    BEGIN
        INSERT INTO clinical_access_links (clinic_id, patient_id, dentist_id)
        VALUES (clinic_key, patient_key, dentist_key);
        RAISE EXCEPTION 'Falhou: vínculo duplicado aceito';
    EXCEPTION WHEN unique_violation THEN NULL;
    END;
    INSERT INTO clinical_access_events (
        link_id, action, actor_user_id, appointment_id, source,
        appointment_scheduled_at, link_version)
    VALUES (link_key, 'GRANTED', admin_key, appointment_key, 'APPOINTMENT',
        '2099-01-15 10:00:00+00', 1) RETURNING id INTO event_key;
    BEGIN
        INSERT INTO clinical_access_events (
            link_id, action, actor_user_id, appointment_id, source,
            appointment_scheduled_at, link_version)
        VALUES (link_key, 'REACTIVATED', admin_key, appointment_key, 'APPOINTMENT',
            '2099-01-15 10:00:00+00', 2);
        RAISE EXCEPTION 'Falhou: consulta repetida concedeu acesso';
    EXCEPTION WHEN unique_violation THEN NULL;
    END;
    BEGIN
        INSERT INTO clinical_access_events (link_id, action, actor_user_id, source, link_version)
        VALUES (link_key, 'REVOKED', admin_key, 'ADMIN', 1);
        RAISE EXCEPTION 'Falhou: evento duplicado por versão aceito';
    EXCEPTION WHEN unique_violation THEN NULL;
    END;
    BEGIN
        INSERT INTO clinical_access_events (link_id, action, actor_user_id, source, link_version)
        VALUES (link_key, 'GRANTED', admin_key, 'APPOINTMENT', 2);
        RAISE EXCEPTION 'Falhou: origem sem consulta/snapshot aceita';
    EXCEPTION WHEN check_violation THEN NULL;
    END;
    UPDATE clinical_access_links SET status = 'REVOKED', version = 2 WHERE id = link_key;
    INSERT INTO clinical_access_events (link_id, action, actor_user_id, source, link_version)
    VALUES (link_key, 'REVOKED', admin_key, 'ADMIN', 2);
    UPDATE appointments SET scheduled_at = '2099-02-15 10:00:00+00',
        status = 'COMPLETED' WHERE id = appointment_key;
    IF (SELECT appointment_scheduled_at FROM clinical_access_events WHERE id = event_key)
        <> '2099-01-15 10:00:00+00'::timestamptz THEN
        RAISE EXCEPTION 'Falhou: snapshot histórico alterado';
    END IF;
    IF (SELECT status FROM clinical_access_links WHERE id = link_key) <> 'REVOKED' THEN
        RAISE EXCEPTION 'Falhou: status antigo reativou vínculo';
    END IF;
    BEGIN
        UPDATE clinical_access_events SET action = 'REACTIVATED' WHERE id = event_key;
        RAISE EXCEPTION 'Falhou: atualização de histórico aceita';
    EXCEPTION WHEN check_violation THEN NULL;
    END;
    BEGIN
        UPDATE clinical_access_links SET version = 0 WHERE id = link_key;
        RAISE EXCEPTION 'Falhou: versão inválida de vínculo aceita';
    EXCEPTION WHEN check_violation THEN NULL;
    END;
    UPDATE clinical_access_links SET status = 'ACTIVE', version = 3 WHERE id = link_key;
    INSERT INTO clinical_access_events (
        link_id, action, actor_user_id, appointment_id, source,
        appointment_scheduled_at, link_version)
    VALUES (link_key, 'REACTIVATED', admin_key, adjacent_key, 'APPOINTMENT',
        '2099-01-15 10:30:00+00', 3);
    IF (SELECT count(*) FROM clinical_access_events WHERE link_id = link_key) <> 3 THEN
        RAISE EXCEPTION 'Falhou: trilha concessão/revogação/reativação incompleta';
    END IF;
    BEGIN
        DELETE FROM clinical_access_events WHERE id = event_key;
        RAISE EXCEPTION 'Falhou: exclusão de histórico aceita';
    EXCEPTION WHEN check_violation THEN NULL;
    END;
    BEGIN
        DELETE FROM clinical_access_links WHERE id = link_key;
        RAISE EXCEPTION 'Falhou: vínculo com histórico excluído';
    EXCEPTION WHEN foreign_key_violation THEN NULL;
    END;
    BEGIN
        DELETE FROM appointments WHERE id = appointment_key;
        RAISE EXCEPTION 'Falhou: origem de histórico excluída';
    EXCEPTION WHEN foreign_key_violation THEN NULL;
    END;
    UPDATE clinical_access_links SET updated_at = '2000-01-01' WHERE id = link_key;
    IF (SELECT updated_at FROM clinical_access_links WHERE id = link_key)
        = '2000-01-01'::timestamptz THEN
        RAISE EXCEPTION 'Falhou: gatilho de atualização';
    END IF;
    RAISE NOTICE 'OK: versões, prontuário único, agenda, evolução, auditoria e idempotência';
END;
$$;
ROLLBACK;
