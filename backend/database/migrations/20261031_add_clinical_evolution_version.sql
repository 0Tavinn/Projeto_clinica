-- Controle otimista dos rascunhos; somente PostgreSQL 16 da linhagem
-- schema.sql com evidências de 25/10. Inventariar e restaurar uma cópia antes
-- de aplicar a um banco existente autorizado. Não inventa revisões antigas.
BEGIN;
SET LOCAL search_path = public, pg_catalog;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '5min';

DO $preflight$
BEGIN
    IF current_setting('server_version_num')::integer / 10000 <> 16 THEN
        RAISE EXCEPTION 'Migração preparada somente para PostgreSQL 16';
    END IF;
    IF to_regclass('public.alembic_version') IS NOT NULL THEN
        RAISE EXCEPTION 'Esquema Alembic ou misto exige reconciliação específica';
    END IF;
    IF to_regclass('public.clinical_evolutions') IS NULL
       OR to_regclass('public.clinical_access_grants') IS NULL THEN
        RAISE EXCEPTION 'Esquema clínico completo de 25/10 ausente';
    END IF;
    IF EXISTS (
        SELECT 1 FROM pg_attribute
        WHERE attrelid = 'public.clinical_evolutions'::regclass
          AND attname = 'version' AND NOT attisdropped
    ) THEN
        RAISE EXCEPTION 'Coluna version já existe; não reaplicar';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'public.clinical_evolutions'::regclass
          AND conname = 'ck_clinical_evolutions_status' AND convalidated
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'public.clinical_evolutions'::regclass
          AND conname = 'uq_clinical_evolutions_appointment' AND convalidated
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_attribute
        WHERE attrelid = 'public.clinical_access_grants'::regclass
          AND attname = 'care_recorded_by_user_id' AND NOT attisdropped
    ) THEN
        RAISE EXCEPTION 'Estrutura anterior não corresponde à entrega de 25/10';
    END IF;
END;
$preflight$;

-- ADD COLUMN com DEFAULT constante inicializa linhas antigas em 1. Esse valor
-- representa apenas a base do novo protocolo, não o número de edições passadas.
ALTER TABLE public.clinical_evolutions
    ADD COLUMN version INTEGER NOT NULL DEFAULT 1,
    ADD CONSTRAINT ck_clinical_evolutions_version CHECK (version >= 1);

COMMIT;
