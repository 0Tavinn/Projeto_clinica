"""Unifica o esquema e adiciona vínculos clínicos auditáveis.

Não concede acesso por consultas antigas nem repara conteúdo clínico.
Dados incompatíveis interrompem a transação para revisão explícita.
"""
from alembic import op

revision = "a6e8f0b2c4d6"
down_revision = "9d3e5f7a1b2c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Preserva as revisões publicadas e incorpora garantias do SQL original.
    op.execute("""
        ALTER TABLE users
            ADD COLUMN session_version INTEGER NOT NULL DEFAULT 1,
            ADD COLUMN clinical_version INTEGER NOT NULL DEFAULT 1,
            ADD CONSTRAINT ck_users_session_version CHECK (session_version >= 1),
            ADD CONSTRAINT ck_users_clinical_version CHECK (clinical_version >= 1),
            ADD CONSTRAINT ck_users_role
                CHECK (role IN ('ADMINISTRATOR', 'RECEPTIONIST', 'DENTIST'));
        ALTER TABLE clinical_evolutions
            ADD COLUMN version INTEGER NOT NULL DEFAULT 1,
            ADD CONSTRAINT ck_clinical_evolutions_version CHECK (version >= 1),
            ADD CONSTRAINT ck_clinical_evolutions_description
                CHECK (description ~ '[^[:space:]]'),
            ADD CONSTRAINT ck_clinical_evolutions_finalization CHECK (
                (status = 'DRAFT' AND finalized_at IS NULL)
                OR (status = 'FINALIZED' AND finalized_at IS NOT NULL)
            );
        CREATE INDEX ix_clinical_evolutions_medical_record_id
            ON clinical_evolutions (medical_record_id);
        CREATE INDEX ix_clinical_evolutions_dentist_id
            ON clinical_evolutions (dentist_id);

        CREATE TABLE clinical_access_links (
            id SERIAL PRIMARY KEY,
            clinic_id INTEGER NOT NULL REFERENCES clinics(id) ON DELETE RESTRICT,
            patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE RESTRICT,
            dentist_id INTEGER NOT NULL REFERENCES dentists(id) ON DELETE RESTRICT,
            status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
            version INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_clinical_access_links_scope
                UNIQUE (clinic_id, patient_id, dentist_id),
            CONSTRAINT ck_clinical_access_links_status
                CHECK (status IN ('ACTIVE', 'REVOKED')),
            CONSTRAINT ck_clinical_access_links_version CHECK (version >= 1)
        );
        CREATE INDEX ix_clinical_access_links_dentist_id
            ON clinical_access_links (dentist_id);
        CREATE TABLE clinical_access_events (
            id SERIAL PRIMARY KEY,
            link_id INTEGER NOT NULL REFERENCES clinical_access_links(id) ON DELETE RESTRICT,
            action VARCHAR(20) NOT NULL,
            actor_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
            appointment_id INTEGER REFERENCES appointments(id) ON DELETE RESTRICT,
            source VARCHAR(20) NOT NULL,
            appointment_scheduled_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            link_version INTEGER NOT NULL,
            CONSTRAINT uq_clinical_access_events_appointment UNIQUE (appointment_id),
            CONSTRAINT uq_clinical_access_events_link_version UNIQUE (link_id, link_version),
            CONSTRAINT ck_clinical_access_events_action
                CHECK (action IN ('GRANTED', 'REVOKED', 'REACTIVATED')),
            CONSTRAINT ck_clinical_access_events_source CHECK (
                (source = 'APPOINTMENT' AND appointment_id IS NOT NULL
                    AND appointment_scheduled_at IS NOT NULL
                    AND action IN ('GRANTED', 'REACTIVATED'))
                OR (source = 'ADMIN' AND appointment_id IS NULL
                    AND appointment_scheduled_at IS NULL)
            ),
            CONSTRAINT ck_clinical_access_events_link_version CHECK (link_version >= 1)
        );
        CREATE INDEX ix_clinical_access_events_actor_user_id
            ON clinical_access_events (actor_user_id);
        CREATE INDEX ix_clinical_access_events_link_created_at
            ON clinical_access_events (link_id, created_at);
        CREATE TABLE audit_logs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
            action VARCHAR(50) NOT NULL,
            resource VARCHAR(100) NOT NULL,
            ip_address VARCHAR(45),
            details TEXT,
            occurred_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_audit_logs_user_id ON audit_logs (user_id);
        CREATE INDEX ix_audit_logs_occurred_at ON audit_logs (occurred_at);

        CREATE EXTENSION IF NOT EXISTS btree_gist;
        ALTER TABLE appointments ADD COLUMN scheduled_period TSTZRANGE;
        UPDATE appointments SET scheduled_period = tstzrange(
            scheduled_at, scheduled_at + make_interval(mins => duration_minutes), '[)'
        );
        ALTER TABLE appointments
            ALTER COLUMN scheduled_period SET NOT NULL,
            ADD CONSTRAINT ck_appointments_period_not_empty
                CHECK (NOT isempty(scheduled_period)),
            ADD CONSTRAINT ex_appointments_dentist_active_period
                EXCLUDE USING gist (dentist_id WITH =, scheduled_period WITH &&)
                WHERE (status IN ('SCHEDULED', 'CONFIRMED'));
        CREATE INDEX ix_appointments_dentist_scheduled_at
            ON appointments (dentist_id, scheduled_at);

        CREATE FUNCTION set_updated_at() RETURNS TRIGGER LANGUAGE plpgsql AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$;
        CREATE FUNCTION set_appointment_period() RETURNS TRIGGER LANGUAGE plpgsql AS $$
        BEGIN
            NEW.scheduled_period := tstzrange(
                NEW.scheduled_at,
                NEW.scheduled_at + make_interval(mins => NEW.duration_minutes), '[)'
            );
            RETURN NEW;
        END;
        $$;
        CREATE TRIGGER trg_appointments_set_period
            BEFORE INSERT OR UPDATE ON appointments
            FOR EACH ROW EXECUTE FUNCTION set_appointment_period();

        CREATE FUNCTION preserve_clinical_access_event() RETURNS TRIGGER
        LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'O histórico de acesso clínico não pode ser alterado ou excluído.'
                USING ERRCODE = '23514';
        END;
        $$;
        CREATE TRIGGER trg_clinical_access_events_preserve
            BEFORE UPDATE OR DELETE ON clinical_access_events
            FOR EACH ROW EXECUTE FUNCTION preserve_clinical_access_event();

        INSERT INTO medical_records (patient_id)
            SELECT p.id FROM patients p
            WHERE NOT EXISTS (
                SELECT 1 FROM medical_records r WHERE r.patient_id = p.id
            );
    """)
    for table in (
        "clinics", "users", "patients", "dentists", "appointments",
        "medical_records", "clinical_evolutions", "clinical_access_links",
    ):
        op.execute(f"""
            CREATE TRIGGER trg_{table}_set_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION set_updated_at()
        """)


def downgrade() -> None:
    # Reversão estrutural explícita; não é executada automaticamente.
    for table in (
        "clinics", "users", "patients", "dentists", "appointments",
        "medical_records", "clinical_evolutions", "clinical_access_links",
    ):
        op.execute(f"DROP TRIGGER trg_{table}_set_updated_at ON {table}")
    op.execute("""
        DROP TRIGGER trg_appointments_set_period ON appointments;
        DROP FUNCTION set_appointment_period();
        DROP FUNCTION set_updated_at();
        DROP TABLE clinical_access_events;
        DROP FUNCTION preserve_clinical_access_event();
        DROP TABLE clinical_access_links;
        DROP TABLE audit_logs;
        DROP INDEX ix_appointments_dentist_scheduled_at;
        ALTER TABLE appointments
            DROP CONSTRAINT ex_appointments_dentist_active_period,
            DROP CONSTRAINT ck_appointments_period_not_empty,
            DROP COLUMN scheduled_period;
        DROP INDEX ix_clinical_evolutions_medical_record_id;
        DROP INDEX ix_clinical_evolutions_dentist_id;
        ALTER TABLE clinical_evolutions
            DROP CONSTRAINT ck_clinical_evolutions_version,
            DROP CONSTRAINT ck_clinical_evolutions_description,
            DROP CONSTRAINT ck_clinical_evolutions_finalization,
            DROP COLUMN version;
        ALTER TABLE users
            DROP CONSTRAINT ck_users_session_version,
            DROP CONSTRAINT ck_users_clinical_version,
            DROP CONSTRAINT ck_users_role,
            DROP COLUMN session_version,
            DROP COLUMN clinical_version;
    """)
    # A extensão pode ser compartilhada com outros objetos; permanece instalada.
