-- Esquema canônico do Lumina para PostgreSQL 16.
-- Equivalente à cadeia Alembic até a revisão a6e8f0b2c4d6.
-- Execute somente em banco vazio. Para banco existente, use Alembic.
-- O serviço cria Patient e MedicalRecord na mesma transação.
-- Vínculos são concedidos apenas pela aplicação; consultas antigas não concedem acesso.
-- Eventos preservam ator, origem e data original do agendamento e são imutáveis.
-- A agenda mantém período calculado, exclusão GiST e gatilhos de atualização.
-- Este arquivo não marca uma revisão em alembic_version.
-- Comparação verificável: pg_dump --schema-only, desconsiderando alembic_version.

BEGIN;

CREATE TABLE clinics (
    id SERIAL NOT NULL,
    name VARCHAR(150) NOT NULL,
    cnpj VARCHAR(14) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(255) NOT NULL,
    address TEXT,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT uq_clinics_cnpj UNIQUE (cnpj),
    CONSTRAINT uq_clinics_email UNIQUE (email)
);

CREATE TABLE users (
    id SERIAL NOT NULL,
    clinic_id INTEGER NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    cpf VARCHAR(11) NOT NULL,
    phone VARCHAR(20),
    role VARCHAR(20) NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(clinic_id) REFERENCES clinics (id),
    CONSTRAINT uq_users_email UNIQUE (email),
    CONSTRAINT uq_users_cpf UNIQUE (cpf)
);

CREATE INDEX ix_users_clinic_id ON users (clinic_id);

CREATE TABLE patients (
    id SERIAL NOT NULL,
    clinic_id INTEGER NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    cpf VARCHAR(11) NOT NULL,
    medical_record_number VARCHAR(30) NOT NULL,
    birth_date DATE NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(255),
    address TEXT,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(clinic_id) REFERENCES clinics (id) ON DELETE RESTRICT,
    CONSTRAINT uq_patients_clinic_cpf UNIQUE (clinic_id, cpf),
    CONSTRAINT uq_patients_clinic_record UNIQUE (clinic_id, medical_record_number)
);

CREATE INDEX ix_patients_clinic_id ON patients (clinic_id);

CREATE TABLE dentists (
    id SERIAL NOT NULL,
    user_id INTEGER NOT NULL,
    cro_number VARCHAR(30) NOT NULL,
    cro_state VARCHAR(2) NOT NULL,
    specialty VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT uq_dentists_user UNIQUE (user_id),
    CONSTRAINT uq_dentists_cro UNIQUE (cro_number, cro_state)
);

CREATE INDEX ix_dentists_user_id ON dentists (user_id);

CREATE TABLE appointments (
    id SERIAL NOT NULL,
    clinic_id INTEGER NOT NULL,
    patient_id INTEGER NOT NULL,
    dentist_id INTEGER NOT NULL,
    scheduled_at TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) DEFAULT 'SCHEDULED' NOT NULL,
    notes TEXT,
    duration_minutes INTEGER DEFAULT '30' NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(clinic_id) REFERENCES clinics (id) ON DELETE RESTRICT,
    FOREIGN KEY(patient_id) REFERENCES patients (id) ON DELETE RESTRICT,
    FOREIGN KEY(dentist_id) REFERENCES dentists (id) ON DELETE RESTRICT,
    CONSTRAINT ck_appointments_status CHECK (status IN ('SCHEDULED', 'CONFIRMED', 'COMPLETED', 'CANCELED', 'NO_SHOW')),
    CONSTRAINT ck_appointments_duration CHECK (duration_minutes > 0)
);

CREATE INDEX ix_appointments_clinic_id ON appointments (clinic_id);

CREATE INDEX ix_appointments_patient_id ON appointments (patient_id);

CREATE INDEX ix_appointments_dentist_id ON appointments (dentist_id);

CREATE INDEX ix_appointments_scheduled_at ON appointments (scheduled_at);

CREATE TABLE medical_records (
    id SERIAL NOT NULL,
    patient_id INTEGER NOT NULL,
    opened_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    general_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(patient_id) REFERENCES patients (id) ON DELETE RESTRICT,
    CONSTRAINT uq_medical_records_patient UNIQUE (patient_id)
);

CREATE TABLE clinical_evolutions (
    id SERIAL NOT NULL,
    medical_record_id INTEGER NOT NULL,
    dentist_id INTEGER NOT NULL,
    appointment_id INTEGER,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    status VARCHAR(20) DEFAULT 'DRAFT' NOT NULL,
    description TEXT NOT NULL,
    procedure_performed TEXT,
    notes TEXT,
    finalized_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(medical_record_id) REFERENCES medical_records (id) ON DELETE RESTRICT,
    FOREIGN KEY(dentist_id) REFERENCES dentists (id) ON DELETE RESTRICT,
    FOREIGN KEY(appointment_id) REFERENCES appointments (id) ON DELETE RESTRICT,
    CONSTRAINT uq_clinical_evolutions_appointment UNIQUE (appointment_id),
    CONSTRAINT ck_clinical_evolutions_status CHECK (status IN ('DRAFT', 'FINALIZED'))
);

ALTER TABLE users ADD COLUMN clinical_password_hash VARCHAR(255);

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
            );;

CREATE TRIGGER trg_clinics_set_updated_at
            BEFORE UPDATE ON clinics
            FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_users_set_updated_at
            BEFORE UPDATE ON users
            FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_patients_set_updated_at
            BEFORE UPDATE ON patients
            FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_dentists_set_updated_at
            BEFORE UPDATE ON dentists
            FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_appointments_set_updated_at
            BEFORE UPDATE ON appointments
            FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_medical_records_set_updated_at
            BEFORE UPDATE ON medical_records
            FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_clinical_evolutions_set_updated_at
            BEFORE UPDATE ON clinical_evolutions
            FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_clinical_access_links_set_updated_at
            BEFORE UPDATE ON clinical_access_links
            FOR EACH ROW EXECUTE FUNCTION set_updated_at();

COMMIT;
