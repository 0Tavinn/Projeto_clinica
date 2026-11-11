-- Concessões clínicas: atualização incremental do schema.sql anterior a esta
-- mudança. NÃO executa no caminho Alembic antigo, em esquema misto, nem no
-- volume de revisão sem inventário, backup restaurado e autorização específica.
-- Não infere confirmações antigas nem cria autorizações retroativas.
-- A FK composta bloqueia mudança dos participantes de consulta concedida;
-- esse comportamento ainda depende da aprovação de Paulo para aplicação.
-- Execute com psql -X -v ON_ERROR_STOP=1 -f <arquivo> no banco identificado.

BEGIN;
SET LOCAL search_path = public, pg_catalog;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '5min';

DO $preflight$
DECLARE
    table_name text;
BEGIN
    IF current_setting('server_version_num')::integer / 10000 <> 16 THEN
        RAISE EXCEPTION 'Migração preparada e ensaiada somente para PostgreSQL 16';
    END IF;
    IF to_regclass('public.alembic_version') IS NOT NULL THEN
        RAISE EXCEPTION 'Origem Alembic ou mista: reconciliação separada necessária';
    END IF;
    IF to_regclass('public.clinical_access_grants') IS NOT NULL THEN
        RAISE EXCEPTION 'clinical_access_grants já existe: não reaplicar';
    END IF;
    FOREACH table_name IN ARRAY ARRAY[
        'clinics', 'users', 'dentists', 'patients', 'appointments',
        'medical_records', 'clinical_evolutions', 'audit_logs'
    ] LOOP
        IF to_regclass(format('public.%I', table_name)) IS NULL THEN
            RAISE EXCEPTION 'Tabela obrigatória ausente: %', table_name;
        END IF;
    END LOOP;
END;
$preflight$;

-- A chave UNIQUE exige bloqueio de escrita na Agenda. Janela de manutenção
-- e tempo efetivo do índice devem ser avaliados previamente em cópia.
LOCK TABLE public.appointments IN ACCESS EXCLUSIVE MODE;
LOCK TABLE public.patients, public.dentists, public.users IN SHARE MODE;

DO $preflight$
DECLARE
    expected_constraints text[] := ARRAY[
        'pk_appointments', 'fk_appointments_clinic',
        'fk_appointments_patient', 'fk_appointments_dentist',
        'ck_appointments_status', 'ck_appointments_duration',
        'ck_appointments_period_not_empty',
        'ex_appointments_dentist_active_period'
    ];
    constraint_name text;
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_extension WHERE extname = 'btree_gist'
    ) THEN
        RAISE EXCEPTION 'Extensão btree_gist ausente; origem não corresponde ao schema.sql completo';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_attribute
        WHERE attrelid = 'public.appointments'::regclass
          AND attname = 'scheduled_period'
          AND atttypid = 'pg_catalog.tstzrange'::regtype
          AND attnotnull AND NOT attisdropped
    ) THEN
        RAISE EXCEPTION 'appointments.scheduled_period não corresponde ao schema.sql completo';
    END IF;
    IF (
        SELECT count(*) FROM pg_attribute
        WHERE attrelid = 'public.appointments'::regclass
          AND attname = ANY (ARRAY['id', 'clinic_id', 'patient_id', 'dentist_id'])
          AND atttypid = 'pg_catalog.int4'::regtype
          AND attnotnull AND NOT attisdropped
    ) <> 4 THEN
        RAISE EXCEPTION 'Chaves da consulta divergem do schema.sql completo';
    END IF;
    FOREACH constraint_name IN ARRAY expected_constraints LOOP
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conrelid = 'public.appointments'::regclass
              AND conname = constraint_name AND convalidated
        ) THEN
            RAISE EXCEPTION 'Restrição da Agenda ausente ou não validada: %', constraint_name;
        END IF;
    END LOOP;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'public.medical_records'::regclass
          AND conname = 'uq_medical_records_patient' AND convalidated
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'public.clinical_evolutions'::regclass
          AND conname = 'uq_clinical_evolutions_appointment' AND convalidated
    ) THEN
        RAISE EXCEPTION 'Estrutura clínica anterior não corresponde ao schema.sql completo';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgrelid = 'public.appointments'::regclass
          AND tgname = 'trg_appointments_set_period'
          AND tgenabled = 'O' AND NOT tgisinternal
    ) THEN
        RAISE EXCEPTION 'Gatilho de período da Agenda ausente ou desabilitado';
    END IF;
    IF EXISTS (
        SELECT 1
        FROM public.appointments AS a
        JOIN public.patients AS p ON p.id = a.patient_id
        JOIN public.dentists AS d ON d.id = a.dentist_id
        JOIN public.users AS u ON u.id = d.user_id
        WHERE a.clinic_id <> p.clinic_id OR a.clinic_id <> u.clinic_id
    ) THEN
        RAISE EXCEPTION 'Consultas antigas têm participantes de clínicas divergentes; corrigir antes da migração';
    END IF;
END;
$preflight$;

ALTER TABLE public.appointments
    ADD CONSTRAINT uq_appointments_access_origin
    UNIQUE (id, clinic_id, patient_id, dentist_id);

CREATE TABLE public.clinical_access_grants (
    appointment_id INTEGER NOT NULL,
    clinic_id INTEGER NOT NULL,
    patient_id INTEGER NOT NULL,
    dentist_id INTEGER NOT NULL,
    granted_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp(),

    CONSTRAINT pk_clinical_access_grants PRIMARY KEY (appointment_id),
    CONSTRAINT fk_clinical_access_grants_origin
        FOREIGN KEY (appointment_id, clinic_id, patient_id, dentist_id)
        REFERENCES public.appointments (id, clinic_id, patient_id, dentist_id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT
);

CREATE INDEX idx_clinical_access_grants_lookup
    ON public.clinical_access_grants (clinic_id, dentist_id, patient_id);

COMMIT;
