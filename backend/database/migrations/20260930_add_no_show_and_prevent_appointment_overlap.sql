-- ============================================================================
-- MIGRAÇÃO: regras de horário da Agenda
--
-- Adiciona:
-- 1. Estado NO_SHOW;
-- 2. Período calculado do agendamento;
-- 3. Proteção contra horários sobrepostos para o mesmo dentista.
-- ============================================================================

BEGIN;

-- Necessária para combinar igualdade do dentista com intervalo de tempo.
CREATE EXTENSION IF NOT EXISTS btree_gist;


-- ============================================================================
-- ESTADOS DO AGENDAMENTO
-- ============================================================================

ALTER TABLE appointments
    DROP CONSTRAINT ck_appointments_status;

ALTER TABLE appointments
    ADD CONSTRAINT ck_appointments_status
    CHECK (
        status IN (
            'SCHEDULED',
            'CONFIRMED',
            'COMPLETED',
            'CANCELED',
            'NO_SHOW'
        )
    );


-- ============================================================================
-- PERÍODO OCUPADO PELO AGENDAMENTO
-- ============================================================================

-- Começa permitindo valor nulo para possibilitar a atualização dos registros
-- que já existem no banco.
ALTER TABLE appointments
    ADD COLUMN scheduled_period TSTZRANGE;

-- Calcula o período dos agendamentos já existentes.
UPDATE appointments
SET scheduled_period = tstzrange(
    scheduled_at,
    scheduled_at + make_interval(mins => duration_minutes),
    '[)'
);

-- Depois da atualização, o período passa a ser obrigatório.
ALTER TABLE appointments
    ALTER COLUMN scheduled_period SET NOT NULL;

ALTER TABLE appointments
    ADD CONSTRAINT ck_appointments_period_not_empty
    CHECK (NOT isempty(scheduled_period));


-- ============================================================================
-- PROTEÇÃO CONTRA CONFLITOS DE HORÁRIO
-- ============================================================================

ALTER TABLE appointments
    ADD CONSTRAINT ex_appointments_dentist_active_period
    EXCLUDE USING gist (
        dentist_id WITH =,
        scheduled_period WITH &&
    )
    WHERE (status IN ('SCHEDULED', 'CONFIRMED'));


-- ============================================================================
-- CÁLCULO AUTOMÁTICO DO PERÍODO
-- ============================================================================

CREATE OR REPLACE FUNCTION set_appointment_period()
RETURNS TRIGGER
AS $$
BEGIN
    NEW.scheduled_period := tstzrange(
        NEW.scheduled_at,
        NEW.scheduled_at
            + make_interval(mins => NEW.duration_minutes),
        '[)'
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_appointments_set_period
BEFORE INSERT OR UPDATE ON appointments
FOR EACH ROW
EXECUTE FUNCTION set_appointment_period();


COMMIT;
