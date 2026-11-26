-- Dados fictícios compatíveis com a revisão B; somente ensaio descartável.
\set ON_ERROR_STOP on
BEGIN;
INSERT INTO clinics (name, cnpj, email)
VALUES ('Clínica Legada Fictícia', '88888888000188', 'legacy@example.test');
INSERT INTO users (clinic_id, full_name, email, password_hash, cpf, role)
SELECT id, 'Dentista Legado', 'legacy-dentist@example.test', 'sem-login',
    '88888888881', 'DENTIST' FROM clinics;
INSERT INTO dentists (user_id, cro_number, cro_state)
SELECT id, 'LEGACY-888', 'SP' FROM users;
INSERT INTO patients (clinic_id, full_name, cpf, medical_record_number, birth_date)
SELECT c.id, p.name, p.cpf, p.record, '1980-01-01'::date
FROM clinics c CROSS JOIN (VALUES
    ('Paciente com prontuário', '88888888882', 'LEGACY-1'),
    ('Paciente sem prontuário', '88888888883', 'LEGACY-2')
) AS p(name, cpf, record);
INSERT INTO medical_records (patient_id, general_notes)
SELECT id, 'Conteúdo legado preservado' FROM patients WHERE cpf = '88888888882';
INSERT INTO appointments (clinic_id, patient_id, dentist_id, scheduled_at, status)
SELECT p.clinic_id, p.id, d.id, '2030-05-10 12:00:00+00'::timestamptz, 'SCHEDULED'
FROM patients p CROSS JOIN dentists d WHERE p.cpf = '88888888882';
INSERT INTO clinical_evolutions (
    medical_record_id, dentist_id, appointment_id, description, status, finalized_at)
SELECT r.id, a.dentist_id, a.id, 'Evolução legada preservada', 'FINALIZED',
    '2026-10-01 12:00:00+00'::timestamptz
FROM medical_records r JOIN appointments a ON a.patient_id = r.patient_id;
COMMIT;
