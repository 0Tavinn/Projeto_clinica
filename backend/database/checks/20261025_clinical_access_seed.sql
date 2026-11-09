-- Somente bancos descartáveis lumina_acl25_new / upgrade / base.
-- Executar após schema novo ou após a migração publicada de 24/10 e ANTES
-- da migração incremental de 25/10 no caminho upgrade.
BEGIN;
DO $seed$
DECLARE
    clinic_value integer;
    patient_a integer;
    patient_b integer;
    dentist_a integer;
    dentist_b integer;
    user_value integer;
    legacy_appointment integer;
    record_value integer;
BEGIN
    IF current_database() NOT IN
        ('lumina_acl25_new', 'lumina_acl25_upgrade', 'lumina_acl25_base') THEN
        RAISE EXCEPTION 'Destino não é banco de ensaio ACL25';
    END IF;
    INSERT INTO clinics (name, cnpj, email)
    VALUES ('Clínica fictícia ACL25', '98000000000001', 'clinic-acl25@example.test')
    RETURNING id INTO clinic_value;
    INSERT INTO users (clinic_id, full_name, email, password_hash, cpf, role)
    VALUES (clinic_value, 'Dentista fictício ACL25 A', 'a-acl25@example.test',
            'hash-ficticio', '98000000001', 'DENTIST')
    RETURNING id INTO user_value;
    INSERT INTO dentists (user_id, cro_number, cro_state)
    VALUES (user_value, 'ACL25-A', 'SP') RETURNING id INTO dentist_a;
    INSERT INTO users (clinic_id, full_name, email, password_hash, cpf, role)
    VALUES (clinic_value, 'Dentista fictício ACL25 B', 'b-acl25@example.test',
            'hash-ficticio', '98000000002', 'DENTIST')
    RETURNING id INTO user_value;
    INSERT INTO dentists (user_id, cro_number, cro_state)
    VALUES (user_value, 'ACL25-B', 'SP') RETURNING id INTO dentist_b;
    INSERT INTO users (clinic_id, full_name, email, password_hash, cpf, role)
    VALUES (clinic_value, 'Recepção fictícia ACL25', 'r-acl25@example.test',
            'hash-ficticio', '98000000003', 'RECEPTIONIST');
    INSERT INTO patients (clinic_id, full_name, cpf, medical_record_number, birth_date)
    VALUES (clinic_value, 'Paciente fictício ACL25 A', '98000000004',
            'ACL25-P-A', DATE '1990-01-01') RETURNING id INTO patient_a;
    INSERT INTO patients (clinic_id, full_name, cpf, medical_record_number, birth_date)
    VALUES (clinic_value, 'Paciente fictício ACL25 B', '98000000005',
            'ACL25-P-B', DATE '1991-01-01') RETURNING id INTO patient_b;

    INSERT INTO appointments
        (clinic_id, patient_id, dentist_id, scheduled_at, status, notes)
    VALUES (clinic_value, patient_a, dentist_a,
            TIMESTAMPTZ '2026-10-20 09:00:00+00', 'CONFIRMED', 'ACL25 legacy')
    RETURNING id INTO legacy_appointment;
    -- Evidência antiga incompleta: preservar, mas não tratar como confiável.
    INSERT INTO clinical_access_grants
        (appointment_id, clinic_id, patient_id, dentist_id, granted_at)
    VALUES (legacy_appointment, clinic_value, patient_a, dentist_a,
            TIMESTAMPTZ '2026-10-19 12:00:00+00');

    INSERT INTO appointments
        (clinic_id, patient_id, dentist_id, scheduled_at, notes)
    VALUES
        (clinic_value, patient_a, dentist_a,
         TIMESTAMPTZ '2026-10-21 09:00:00+00', 'ACL25 canceled'),
        (clinic_value, patient_a, dentist_a,
         TIMESTAMPTZ '2026-10-22 09:00:00+00', 'ACL25 absent'),
        (clinic_value, patient_a, dentist_a,
         TIMESTAMPTZ '2026-10-23 09:00:00+00', 'ACL25 active'),
        (clinic_value, patient_a, dentist_a,
         TIMESTAMPTZ '2026-10-24 09:00:00+00', 'ACL25 completed'),
        (clinic_value, patient_b, dentist_b,
         TIMESTAMPTZ '2026-10-25 09:00:00+00', 'ACL25 other');

    -- Dados clínicos anteriores à atualização devem sobreviver à migração.
    INSERT INTO medical_records (patient_id, general_notes)
    VALUES (patient_b, 'Nota fictícia anterior ACL25')
    RETURNING id INTO record_value;
    INSERT INTO clinical_evolutions
        (medical_record_id, dentist_id, description)
    VALUES (record_value, dentist_b, 'Evolução fictícia anterior ACL25');
END;
$seed$;
COMMIT;
