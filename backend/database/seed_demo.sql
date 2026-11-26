-- Carga demonstrativa fictícia; somente banco descartável com esquema atual.
-- Recusa banco que já possui dados. Não sobrescreve senhas nem cadastros.
-- Login fictício: admin.demo@example.com / dentista.demo@example.com
-- Senha fictícia: DemoLumina2026! ; senha clínica: ClinicaDemo2026!
\set ON_ERROR_STOP on
BEGIN;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM clinics)
        OR EXISTS (SELECT 1 FROM users)
        OR EXISTS (SELECT 1 FROM patients) THEN
        RAISE EXCEPTION 'Carga demonstrativa exige banco descartável vazio.';
    END IF;
END;
$$;

INSERT INTO clinics (name, cnpj, email, phone)
VALUES ('Lumina Demonstração Fictícia', '00000000000191',
    'clinica.demo@example.test', '11900000000');

INSERT INTO users (
    clinic_id, full_name, email, password_hash, cpf, role)
SELECT id, 'Administrador Fictício', 'admin.demo@example.com',
    '$argon2id$v=19$m=65536,t=3,p=4$6/0f45yzVur9X+sdA0DovQ$C7ppYOCIXCMZ+nvsBe5Lg1/HHdzfJpb2+4Yr4a9oJ54',
    '00000000001', 'ADMINISTRATOR'
FROM clinics;

INSERT INTO users (
    clinic_id, full_name, email, password_hash, clinical_password_hash, cpf, role)
SELECT id, 'Dentista Fictício', 'dentista.demo@example.com',
    '$argon2id$v=19$m=65536,t=3,p=4$6/0f45yzVur9X+sdA0DovQ$C7ppYOCIXCMZ+nvsBe5Lg1/HHdzfJpb2+4Yr4a9oJ54',
    '$argon2id$v=19$m=65536,t=3,p=4$zJmzlrK21jpn7L23ljJGiA$L86vzjpyHE82gDpU4Ydpg9RQG8K55AEQ5cxfWNBwTdY',
    '00000000002', 'DENTIST'
FROM clinics;

INSERT INTO dentists (user_id, cro_number, cro_state, specialty)
SELECT id, 'DEMO-0001', 'SP', 'Clínica geral'
FROM users WHERE email = 'dentista.demo@example.com';

INSERT INTO patients (clinic_id, full_name, cpf, medical_record_number, birth_date)
SELECT c.id, demo.full_name, demo.cpf, demo.record_number, demo.birth_date::date
FROM clinics c CROSS JOIN (VALUES
    ('Paciente Fictício Ativo', '00000000011', 'DEMO-001', '1990-02-10'),
    ('Paciente Fictício Revogado', '00000000012', 'DEMO-002', '1985-06-20'),
    ('Paciente Fictício Sem Vínculo', '00000000013', 'DEMO-003', '2000-10-05')
) AS demo(full_name, cpf, record_number, birth_date);

INSERT INTO medical_records (patient_id)
SELECT id FROM patients;

INSERT INTO appointments (
    clinic_id, patient_id, dentist_id, scheduled_at, status, notes)
SELECT p.clinic_id, p.id, d.id,
    '2030-01-15 13:00:00+00'::timestamptz, 'SCHEDULED',
    'Consulta fictícia: concessão de vínculo ativo'
FROM patients p CROSS JOIN dentists d WHERE p.cpf = '00000000011';

INSERT INTO appointments (
    clinic_id, patient_id, dentist_id, scheduled_at, status, notes)
SELECT p.clinic_id, p.id, d.id,
    '2026-10-15 13:00:00+00'::timestamptz, 'COMPLETED',
    'Consulta fictícia antiga: vínculo posteriormente revogado'
FROM patients p CROSS JOIN dentists d WHERE p.cpf = '00000000012';

INSERT INTO clinical_access_links (clinic_id, patient_id, dentist_id, status, version)
SELECT p.clinic_id, p.id, d.id, 'ACTIVE', 1
FROM patients p CROSS JOIN dentists d WHERE p.cpf = '00000000011';

INSERT INTO clinical_access_links (clinic_id, patient_id, dentist_id, status, version)
SELECT p.clinic_id, p.id, d.id, 'REVOKED', 2
FROM patients p CROSS JOIN dentists d WHERE p.cpf = '00000000012';

INSERT INTO clinical_access_events (
    link_id, action, actor_user_id, appointment_id, source,
    appointment_scheduled_at, link_version)
SELECT l.id, 'GRANTED', u.id, a.id, 'APPOINTMENT', a.scheduled_at, 1
FROM clinical_access_links l
JOIN appointments a ON a.patient_id = l.patient_id AND a.dentist_id = l.dentist_id
JOIN users u ON u.email = 'admin.demo@example.com';

INSERT INTO clinical_access_events (
    link_id, action, actor_user_id, source, link_version)
SELECT l.id, 'REVOKED', u.id, 'ADMIN', 2
FROM clinical_access_links l
JOIN users u ON u.email = 'admin.demo@example.com'
WHERE l.status = 'REVOKED';

INSERT INTO clinical_evolutions (medical_record_id, dentist_id, description)
SELECT r.id, d.id, 'Evolução fictícia em rascunho, sem consulta vinculada.'
FROM medical_records r
JOIN patients p ON p.id = r.patient_id
CROSS JOIN dentists d WHERE p.cpf = '00000000011';

INSERT INTO clinical_evolutions (
    medical_record_id, dentist_id, appointment_id, status, description, finalized_at)
SELECT r.id, a.dentist_id, a.id, 'FINALIZED',
    'Evolução fictícia finalizada para revisão do esquema.', now()
FROM medical_records r
JOIN patients p ON p.id = r.patient_id
JOIN appointments a ON a.patient_id = p.id
WHERE p.cpf = '00000000012';

INSERT INTO audit_logs (user_id, action, resource, details)
SELECT id, 'CREATE', 'DEMO_DATABASE',
    'Carga inteiramente fictícia para revisão em banco descartável.'
FROM users WHERE email = 'admin.demo@example.com';
COMMIT;
