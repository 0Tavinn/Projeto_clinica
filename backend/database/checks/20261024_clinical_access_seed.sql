-- Dados exclusivamente fictícios; execute apenas nos bancos descartáveis
-- lumina_acl_new_20261024 e lumina_acl_upgrade_20261024.
BEGIN;
DO $seed$
DECLARE
    clinic_id_value integer;
    patient_id_value integer;
    other_patient_id integer;
    user_id_value integer;
    dentist_id_value integer;
    other_dentist_id integer;
    appointment_id_value integer;
    record_id_value integer;
BEGIN
    IF current_database() NOT IN (
        'lumina_acl_new_20261024', 'lumina_acl_upgrade_20261024'
    ) THEN
        RAISE EXCEPTION 'Ensaio permitido apenas nos bancos descartáveis identificados';
    END IF;

    INSERT INTO clinics (name, cnpj, email)
    VALUES ('Clínica fictícia ACL', '99000000000001', 'acl-clinic@example.test')
    RETURNING id INTO clinic_id_value;

    INSERT INTO users (clinic_id, full_name, email, password_hash, cpf, role)
    VALUES (clinic_id_value, 'Dentista fictício A', 'acl-a@example.test',
            'hash-ficticio', '99000000001', 'DENTIST')
    RETURNING id INTO user_id_value;
    INSERT INTO dentists (user_id, cro_number, cro_state)
    VALUES (user_id_value, 'ACL-FAKE-A', 'SP')
    RETURNING id INTO dentist_id_value;

    INSERT INTO users (clinic_id, full_name, email, password_hash, cpf, role)
    VALUES (clinic_id_value, 'Dentista fictício B', 'acl-b@example.test',
            'hash-ficticio', '99000000002', 'DENTIST')
    RETURNING id INTO user_id_value;
    INSERT INTO dentists (user_id, cro_number, cro_state)
    VALUES (user_id_value, 'ACL-FAKE-B', 'SP')
    RETURNING id INTO other_dentist_id;

    INSERT INTO patients (clinic_id, full_name, cpf, medical_record_number, birth_date)
    VALUES (clinic_id_value, 'Paciente fictício A', '99000000003',
            'ACL-FAKE-1', DATE '1990-01-01')
    RETURNING id INTO patient_id_value;
    INSERT INTO patients (clinic_id, full_name, cpf, medical_record_number, birth_date)
    VALUES (clinic_id_value, 'Paciente fictício B', '99000000004',
            'ACL-FAKE-2', DATE '1991-01-01')
    RETURNING id INTO other_patient_id;

    INSERT INTO appointments
        (clinic_id, patient_id, dentist_id, scheduled_at, duration_minutes, notes)
    VALUES
        (clinic_id_value, patient_id_value, dentist_id_value,
         TIMESTAMPTZ '2026-11-01 09:00:00+00', 30, 'Consulta fictícia A')
    RETURNING id INTO appointment_id_value;
    INSERT INTO appointments
        (clinic_id, patient_id, dentist_id, scheduled_at, duration_minutes, notes)
    VALUES
        (clinic_id_value, patient_id_value, dentist_id_value,
         TIMESTAMPTZ '2026-11-02 09:00:00+00', 30, 'Consulta fictícia B');
    INSERT INTO appointments
        (clinic_id, patient_id, dentist_id, scheduled_at, duration_minutes, notes)
    VALUES
        (clinic_id_value, other_patient_id, other_dentist_id,
         TIMESTAMPTZ '2026-11-03 09:00:00+00', 30, 'Consulta fictícia C');

    -- Histórico anterior à migração: deve permanecer intocado.
    INSERT INTO medical_records (patient_id, general_notes)
    VALUES (other_patient_id, 'Observação fictícia anterior')
    RETURNING id INTO record_id_value;
    INSERT INTO clinical_evolutions
        (medical_record_id, dentist_id, appointment_id, description)
    VALUES (record_id_value, other_dentist_id,
            (SELECT id FROM appointments WHERE notes = 'Consulta fictícia C'),
            'Evolução fictícia anterior');
END;
$seed$;
COMMIT;
