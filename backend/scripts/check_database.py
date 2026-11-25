"""Confere por leitura o contrato PostgreSQL exigido pela execução local."""
import argparse
import os
import sys
from sqlalchemy import create_engine, text

REVISION = "a6e8f0b2c4d6"
TABLES = {
    "clinics", "users", "patients", "dentists", "appointments",
    "medical_records", "clinical_evolutions", "clinical_access_links",
    "clinical_access_events", "audit_logs", "alembic_version",
}
CONSTRAINTS = {
    "uq_medical_records_patient", "uq_clinical_evolutions_appointment",
    "ck_clinical_evolutions_version", "ck_clinical_evolutions_description",
    "ck_clinical_evolutions_finalization", "uq_clinical_access_links_scope",
    "uq_clinical_access_events_appointment", "uq_clinical_access_events_link_version",
    "ex_appointments_dentist_active_period", "ck_users_session_version",
    "ck_users_clinical_version",
}
TRIGGERS = {
    "trg_appointments_set_period", "trg_clinical_access_events_preserve",
    "trg_clinical_evolutions_set_updated_at",
}

def check(mode):
    engine = create_engine(os.environ["DATABASE_URL"], connect_args={"connect_timeout": 5})
    with engine.connect() as db:
        db.exec_driver_sql("BEGIN READ ONLY")
        db.exec_driver_sql("SET LOCAL statement_timeout = '5s'")
        db.exec_driver_sql("SET LOCAL lock_timeout = '1s'")
        version = int(db.exec_driver_sql("SHOW server_version_num").scalar_one())
        if version // 10000 != 16:
            raise ValueError("Execução preparada para PostgreSQL 16.")
        tables = set(db.execute(text("""
            SELECT tablename FROM pg_tables
            WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
        """)).scalars())
        if mode == "empty":
            if tables:
                raise ValueError("Banco preenchido. init/seed recusado.")
            print("OK: banco vazio para provisionamento explícito.")
            return
        if tables != TABLES:
            raise ValueError("Catálogo divergente. Reconciliar a origem antes de iniciar a aplicação.")
        revision = db.exec_driver_sql("SELECT version_num FROM public.alembic_version").scalars().all()
        if revision != [REVISION]:
            raise ValueError("Linhagem desconhecida ou revisão divergente. Migração automática recusada.")
        constraints = set(db.execute(text("""
            SELECT conname FROM pg_constraint c JOIN pg_namespace n ON n.oid=c.connamespace
            WHERE n.nspname='public' AND convalidated
        """)).scalars())
        triggers = set(db.execute(text("""
            SELECT tgname FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
            JOIN pg_namespace n ON n.oid=c.relnamespace
            WHERE n.nspname='public' AND NOT tgisinternal AND tgenabled='O'
        """)).scalars())
        if not CONSTRAINTS <= constraints or not TRIGGERS <= triggers:
            raise ValueError("Constraints/gatilhos esperados ausentes ou desabilitados.")
        if not db.exec_driver_sql("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname='btree_gist')").scalar():
            raise ValueError("Extensão btree_gist ausente.")
        columns = set(db.execute(text("""
            SELECT table_name || '.' || column_name FROM information_schema.columns
            WHERE table_schema='public'
        """)).scalars())
        required = {
            "appointments.scheduled_period", "clinical_evolutions.version",
            "users.session_version", "users.clinical_version", "users.clinical_password_hash",
            "clinical_access_links.version", "clinical_access_events.link_version",
        }
        if not required <= columns:
            raise ValueError("Campos esperados ausentes.")
        database, server = db.exec_driver_sql(
            "SELECT current_database(), current_setting('server_version')"
        ).one()
        print(f"OK: banco={database}; PostgreSQL={server}; revisão={REVISION}; catálogo conferido.")
        db.rollback()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["ready", "empty"], default="ready", nargs="?")
    try:
        check(parser.parse_args().mode)
    except ValueError as error:
        sys.exit(str(error))
    except Exception as error:
        sys.exit(f"Falha na conferência do banco ({type(error).__name__}). Verifique conexão/configuração.")
