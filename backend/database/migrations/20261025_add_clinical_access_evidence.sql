-- Incremental sobre o schema.sql completo COM a estrutura publicada em 24/10.
-- PostgreSQL 16 apenas. Não usar em Alembic antigo, esquema misto/divergente
-- ou banco existente sem inventário, backup restaurado e autorização específica.
-- A migração preserva todas as concessões: campos novos ficam NULL nelas.
-- NULL em confirmed_by_user_id não comprova confirmação confiável.
-- Executar com psql -X -v ON_ERROR_STOP=1 -f <arquivo>.

BEGIN;
SET LOCAL search_path = public, pg_catalog;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '5min';

DO $preflight$
DECLARE
    column_name text;
    constraint_name text;
BEGIN
    IF current_setting('server_version_num')::integer / 10000 <> 16 THEN
        RAISE EXCEPTION 'Migração preparada somente para PostgreSQL 16';
    END IF;
    IF to_regclass('public.alembic_version') IS NOT NULL THEN
        RAISE EXCEPTION 'Origem Alembic ou mista requer reconciliação';
    END IF;
    IF to_regclass('public.clinical_access_grants') IS NULL
       OR to_regclass('public.appointments') IS NULL
       OR to_regclass('public.users') IS NULL THEN
        RAISE EXCEPTION 'Origem 24/10 incompleta';
    END IF;
    FOREACH column_name IN ARRAY ARRAY[
        'confirmed_by_user_id', 'care_occurred_at', 'care_recorded_at',
        'care_recorded_by_user_id'
    ] LOOP
        IF EXISTS (
            SELECT 1 FROM pg_attribute
            WHERE attrelid = 'public.clinical_access_grants'::regclass
              AND attname = column_name AND NOT attisdropped
        ) THEN
            RAISE EXCEPTION 'Coluna nova já existe: %; não reaplicar', column_name;
        END IF;
    END LOOP;
END;
$preflight$;

LOCK TABLE public.clinical_access_grants IN ACCESS EXCLUSIVE MODE;
LOCK TABLE public.appointments, public.users IN SHARE MODE;

DO $preflight$
DECLARE
    column_name text;
    constraint_name text;
BEGIN
    FOREACH column_name IN ARRAY ARRAY[
        'appointment_id', 'clinic_id', 'patient_id', 'dentist_id'
    ] LOOP
        IF NOT EXISTS (
            SELECT 1 FROM pg_attribute
            WHERE attrelid = 'public.clinical_access_grants'::regclass
              AND attname = column_name
              AND atttypid = 'pg_catalog.int4'::regtype
              AND attnotnull AND NOT attisdropped
        ) THEN
            RAISE EXCEPTION 'Chave da concessão divergente: %', column_name;
        END IF;
    END LOOP;
    IF NOT EXISTS (
        SELECT 1 FROM pg_attribute
        WHERE attrelid = 'public.clinical_access_grants'::regclass
          AND attname = 'granted_at'
          AND atttypid = 'pg_catalog.timestamptz'::regtype
          AND attnotnull AND NOT attisdropped
    ) THEN
        RAISE EXCEPTION 'granted_at divergente';
    END IF;
    FOREACH constraint_name IN ARRAY ARRAY[
        'pk_clinical_access_grants', 'fk_clinical_access_grants_origin'
    ] LOOP
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conrelid = 'public.clinical_access_grants'::regclass
              AND conname = constraint_name AND convalidated
        ) THEN
            RAISE EXCEPTION 'Restrição anterior ausente ou inválida: %', constraint_name;
        END IF;
    END LOOP;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'public.appointments'::regclass
          AND conname = 'uq_appointments_access_origin' AND convalidated
    ) OR to_regclass('public.idx_clinical_access_grants_lookup') IS NULL THEN
        RAISE EXCEPTION 'Chave composta ou índice da entrega 24/10 ausente';
    END IF;
END;
$preflight$;

ALTER TABLE public.clinical_access_grants
    ADD COLUMN confirmed_by_user_id INTEGER,
    ADD COLUMN care_occurred_at TIMESTAMP WITH TIME ZONE,
    ADD COLUMN care_recorded_at TIMESTAMP WITH TIME ZONE,
    ADD COLUMN care_recorded_by_user_id INTEGER,
    ADD CONSTRAINT fk_clinical_access_grants_confirmed_by
        FOREIGN KEY (confirmed_by_user_id) REFERENCES public.users (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    ADD CONSTRAINT fk_clinical_access_grants_care_recorded_by
        FOREIGN KEY (care_recorded_by_user_id) REFERENCES public.users (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    ADD CONSTRAINT ck_clinical_access_grants_care_complete
        CHECK (
            (care_occurred_at IS NULL AND care_recorded_at IS NULL
             AND care_recorded_by_user_id IS NULL)
            OR
            (confirmed_by_user_id IS NOT NULL
             AND care_occurred_at IS NOT NULL AND care_recorded_at IS NOT NULL
             AND care_recorded_by_user_id IS NOT NULL)
        );

COMMIT;
