#!/usr/bin/env bash
# Valida apenas recursos descartáveis próprios. Nunca usa compose ou volumes.
set -Eeuo pipefail

script_dir="$(cd -- "$(dirname -- "$0")" && pwd)"
backend_dir="$(cd -- "$script_dir/.." && pwd)"
migration_image="$(printenv DB_MIGRATION_IMAGE || printf 'lumina-db-migrations:local')"
postgres_image="$(printenv DB_POSTGRES_IMAGE || printf 'postgres:16-alpine')"
resource_key="lumina-db-check-$(date +%Y%m%d%H%M%S)-$$-$RANDOM"
pg_name="$resource_key-pg"
runner_name="$resource_key-runner"
network_name="$resource_key-net"
test_password="disposable-$RANDOM-$RANDOM"
artifact_dir="$(mktemp -d -t lumina-db-check.XXXXXXXX)"
owns_network=0
owns_pg=0
owns_runner=0

cleanup() {
    exit_status=$?
    trap - EXIT
    if [[ "$owns_runner" == 1 ]]; then
        docker rm -f "$runner_name" >/dev/null 2>&1 || true
    fi
    if [[ "$owns_pg" == 1 ]]; then
        docker rm -f "$pg_name" >/dev/null 2>&1 || true
    fi
    if [[ "$owns_network" == 1 ]]; then
        docker network rm "$network_name" >/dev/null 2>&1 || true
    fi
    # Diretório temporário criado exclusivamente por esta execução.
    if [[ "$artifact_dir" == /tmp/lumina-db-check.* && -d "$artifact_dir" ]]; then
        rm -rf -- "$artifact_dir"
    fi
    exit "$exit_status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

if ! docker image inspect "$migration_image" >/dev/null 2>&1; then
    if [[ -n "$(printenv DB_MIGRATION_IMAGE || true)" ]]; then
        printf 'Imagem alternativa de migração ausente: %s\n' "$migration_image" >&2
        exit 2
    fi
    docker build -f "$script_dir/Dockerfile.migrations" -t "$migration_image" "$script_dir"
fi
docker network create "$network_name" >/dev/null
owns_network=1
docker run --rm -d --name "$pg_name" --network "$network_name" --network-alias db \
    -e POSTGRES_PASSWORD="$test_password" -e POSTGRES_DB=alembic_fresh \
    "$postgres_image" >/dev/null
owns_pg=1
ready=0
for attempt in {1..30}; do
    if docker exec "$pg_name" pg_isready -h 127.0.0.1 -U postgres -d alembic_fresh >/dev/null 2>&1; then
        ready=1
        break
    fi
    sleep 1
done
[[ "$ready" == 1 ]] || { printf 'PostgreSQL descartável não ficou pronto.\n' >&2; exit 1; }

create_db() { docker exec "$pg_name" createdb -U postgres "$1"; }
psql_db() { docker exec -i "$pg_name" psql -X -U postgres -v ON_ERROR_STOP=1 -d "$1"; }
sql_file() { psql_db "$1" < "$script_dir/$2"; }
migrate() {
    local database="$1"
    shift
    owns_runner=1
    if docker run --rm --name "$runner_name" --network "$network_name" \
        --mount "type=bind,src=$backend_dir,dst=/app,readonly" -w /app \
        -e PYTHONDONTWRITEBYTECODE=1 \
        -e DATABASE_URL="postgresql+psycopg://postgres:$test_password@db:5432/$database" \
        "$migration_image" alembic -c /app/alembic.ini "$@"; then
        owns_runner=0
        return 0
    else
        local migration_status=$?
        owns_runner=0
        return "$migration_status"
    fi
}
expect_rejected_upgrade() {
    local database="$1"
    local expected_constraint="$2"
    if migrate "$database" upgrade head >"$artifact_dir/rejected.log" 2>&1; then
        printf 'Falhou: migração aceitou dados inválidos em %s\n' "$database" >&2
        exit 1
    fi
    if ! grep -q "$expected_constraint" "$artifact_dir/rejected.log"; then
        cat "$artifact_dir/rejected.log" >&2
        printf 'Falhou por motivo diferente da restrição esperada.\n' >&2
        exit 1
    fi
    psql_db "$database" <<'SQL'
DO $$
BEGIN
    IF (SELECT version_num FROM alembic_version) <> '9d3e5f7a1b2c'
        OR EXISTS (SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'users'
                AND column_name = 'session_version') THEN
        RAISE EXCEPTION 'Falhou: migração rejeitada deixou alterações parciais';
    END IF;
END;
$$;
SQL
    printf 'OK: migração rejeitou %s e reverteu integralmente.\n' "$expected_constraint"
}

printf 'Validando Alembic desde banco vazio...\n'
migrate alembic_fresh upgrade head
sql_file alembic_fresh check_clinical_schema.sql
migrate alembic_fresh downgrade 9d3e5f7a1b2c
migrate alembic_fresh upgrade head

printf 'Validando schema.sql e equivalência estrutural integral...\n'
create_db sql_fresh
sql_file sql_fresh schema.sql
sql_file sql_fresh check_clinical_schema.sql
docker exec "$pg_name" pg_dump -U postgres -d alembic_fresh --schema-only \
    --no-owner --no-privileges --restrict-key=LuminaDisposableSchemaCheck \
    --exclude-table=public.alembic_version > "$artifact_dir/alembic.sql"
docker exec "$pg_name" pg_dump -U postgres -d sql_fresh --schema-only \
    --no-owner --no-privileges --restrict-key=LuminaDisposableSchemaCheck \
    > "$artifact_dir/standalone.sql"
diff -u "$artifact_dir/alembic.sql" "$artifact_dir/standalone.sql"
printf 'OK: pg_dump idêntico entre SQL e Alembic, exceto tabela de controle Alembic.\n'

printf 'Validando atualização com histórico fictício da revisão B...\n'
create_db legacy_upgrade
migrate legacy_upgrade upgrade 9d3e5f7a1b2c
sql_file legacy_upgrade fixture_9d3e5f7a1b2c.sql
migrate legacy_upgrade upgrade head
psql_db legacy_upgrade <<'SQL'
DO $$
BEGIN
    IF (SELECT count(*) FROM medical_records) <> 2
        OR NOT EXISTS (SELECT 1 FROM medical_records
            WHERE general_notes = 'Conteúdo legado preservado')
        OR NOT EXISTS (SELECT 1 FROM clinical_evolutions
            WHERE description = 'Evolução legada preservada'
                AND version = 1 AND finalized_at = '2026-10-01 12:00:00+00')
        OR EXISTS (SELECT 1 FROM clinical_access_links)
        OR EXISTS (SELECT 1 FROM clinical_access_events)
        OR EXISTS (SELECT 1 FROM users WHERE session_version <> 1 OR clinical_version <> 1)
        OR EXISTS (SELECT 1 FROM appointments WHERE scheduled_period IS NULL) THEN
        RAISE EXCEPTION 'Falhou: atualização não preservou dados/regras legadas';
    END IF;
    RAISE NOTICE 'OK: histórico preservado, prontuário ausente criado, acesso antigo não concedido';
END;
$$;
SQL
sql_file legacy_upgrade check_clinical_schema.sql

printf 'Validando rejeição segura de dados legados incompatíveis...\n'
create_db bad_evolution
migrate bad_evolution upgrade 9d3e5f7a1b2c
sql_file bad_evolution fixture_9d3e5f7a1b2c.sql
printf 'UPDATE clinical_evolutions SET finalized_at = NULL;\n' | psql_db bad_evolution
expect_rejected_upgrade bad_evolution ck_clinical_evolutions_finalization

create_db bad_agenda
migrate bad_agenda upgrade 9d3e5f7a1b2c
sql_file bad_agenda fixture_9d3e5f7a1b2c.sql
psql_db bad_agenda <<'SQL'
INSERT INTO appointments (clinic_id, patient_id, dentist_id, scheduled_at)
SELECT clinic_id, patient_id, dentist_id, scheduled_at + interval '15 minutes'
FROM appointments;
SQL
expect_rejected_upgrade bad_agenda ex_appointments_dentist_active_period

printf 'Validando carga demonstrativa independente da API...\n'
sql_file sql_fresh seed_demo.sql
psql_db sql_fresh <<'SQL'
DO $$
BEGIN
    IF (SELECT count(*) FROM patients) <> 3
        OR (SELECT count(*) FROM medical_records) <> 3
        OR (SELECT count(*) FROM clinical_access_links) <> 2
        OR (SELECT count(*) FROM clinical_access_events) <> 3
        OR (SELECT count(*) FROM clinical_evolutions) <> 2
        OR (SELECT count(*) FROM audit_logs) <> 1
        OR EXISTS (SELECT 1 FROM users
            WHERE role <> 'DENTIST' AND clinical_password_hash IS NOT NULL) THEN
        RAISE EXCEPTION 'Falhou: carga demonstrativa incompleta';
    END IF;
END;
$$;
SQL
if sql_file sql_fresh seed_demo.sql > "$artifact_dir/seed-rejected.log" 2>&1; then
    printf 'Falhou: carga demonstrativa repetida foi aceita.\n' >&2
    exit 1
fi
grep -q 'exige banco descartável vazio' "$artifact_dir/seed-rejected.log"
printf 'OK: carga fictícia válida e repetição recusada sem sobrescrever dados.\n'
printf 'Validando persistência após reinício e backup/restauração fictícios...\n'
docker exec "$pg_name" pg_dump -U postgres -d sql_fresh --format=custom \
    --no-owner --no-privileges > "$artifact_dir/demo.dump"
docker exec "$pg_name" pg_dump -U postgres -d sql_fresh --data-only \
    --no-owner --no-privileges --restrict-key=LuminaDisposableSchemaCheck \
    > "$artifact_dir/before-restart.sql"
docker restart "$pg_name" >/dev/null
ready=0
for attempt in {1..30}; do
    if docker exec "$pg_name" pg_isready -h 127.0.0.1 -U postgres -d sql_fresh >/dev/null 2>&1; then
        ready=1
        break
    fi
    sleep 1
done
[[ "$ready" == 1 ]] || { printf 'PostgreSQL não voltou após reinício.\n' >&2; exit 1; }
create_db restored_demo
docker exec -i "$pg_name" pg_restore -U postgres -d restored_demo \
    --exit-on-error --no-owner --no-privileges < "$artifact_dir/demo.dump"
docker exec "$pg_name" pg_dump -U postgres -d sql_fresh --data-only \
    --no-owner --no-privileges --restrict-key=LuminaDisposableSchemaCheck \
    > "$artifact_dir/after-restart.sql"
docker exec "$pg_name" pg_dump -U postgres -d restored_demo --data-only \
    --no-owner --no-privileges --restrict-key=LuminaDisposableSchemaCheck \
    > "$artifact_dir/after-restore.sql"
diff -u "$artifact_dir/before-restart.sql" "$artifact_dir/after-restart.sql"
diff -u "$artifact_dir/after-restart.sql" "$artifact_dir/after-restore.sql"
sql_file restored_demo check_clinical_schema.sql
printf 'OK: reinício e restauração preservaram dados integralmente; garantias SQL verificadas na restauração.\n'
printf 'OK: todas as verificações passaram; removendo somente recursos descartáveis próprios.\n'
