#!/usr/bin/env bash
# PostgreSQL 16 exclusivo, com dados fictícios. Não usa Compose nem volume da revisão.
set -euo pipefail
cd "$(dirname "$0")/../../.."

docker info >/dev/null
work_dir="$(mktemp -d /tmp/lumina-acl25.XXXXXX)"
suffix="$(date +%s)_$$"
containers=()
volumes=()
cleanup() {
    local item
    for item in "${containers[@]}"; do docker rm -f "$item" >/dev/null 2>&1 || true; done
    for item in "${volumes[@]}"; do docker volume rm "$item" >/dev/null 2>&1 || true; done
    rm -rf -- "$work_dir"
}
trap cleanup EXIT

git show 698a3bd4d8d20af7efa828d7f78589e4ec4b7a5e:backend/database/schema.sql > "$work_dir/schema_base.sql"
git show 01a01573a42b09bcfb3c337561817693554e0459:backend/database/schema.sql > "$work_dir/schema_24.sql"

start_db() {
    local kind="$1" name="lumina_acl25_${1}_${suffix}" volume="lumina_acl25_${1}_${suffix}"
    local db="lumina_acl25_${kind}" i
    if docker container inspect "$name" >/dev/null 2>&1 || docker volume inspect "$volume" >/dev/null 2>&1; then
        echo "Recurso já existe: $name / $volume" >&2
        exit 1
    fi
    docker volume create "$volume" >/dev/null
    volumes+=("$volume")
    containers+=("$name")
    docker run -d --name "$name" --network none \
        --mount "type=volume,src=$volume,dst=/var/lib/postgresql/data" \
        -e "POSTGRES_DB=$db" -e POSTGRES_USER=clinic_app \
        -e POSTGRES_PASSWORD=scratch-only-not-secret postgres:16-alpine >/dev/null
    for i in $(seq 1 60); do
        # A imagem inicia e encerra um servidor temporário durante initdb.
        # Esperar a conclusão do entrypoint antes de aceitar pg_isready.
        if [[ "$(docker logs "$name" 2>&1)" == *'PostgreSQL init process complete; ready for start up.'* ]] \
           && docker exec "$name" pg_isready -U clinic_app -d "$db" >/dev/null 2>&1 \
           && docker exec "$name" psql -X -Atq -U clinic_app -d "$db" -c 'SELECT 1' >/dev/null 2>&1; then
            db_name="$name"
            db_volume="$volume"
            db_database="$db"
            return
        fi
        sleep 0.5
    done
    echo "PostgreSQL 16 não ficou pronto: $name" >&2
    exit 1
}

run_sql() {
    local name="$1" db="$2" file="$3"
    docker exec -i "$name" psql -X -q -v ON_ERROR_STOP=1 \
        -U clinic_app -d "$db" < "$file"
}

for kind in new upgrade base; do
    start_db "$kind"
    name="$db_name"
    volume="$db_volume"
    db="$db_database"
    server_version="$(docker exec "$name" psql -X -Atq -U clinic_app -d "$db" -c 'SHOW server_version')"
    [[ "$server_version" == 16.* ]] || { echo "Versão inesperada: $server_version" >&2; exit 1; }
    echo "Destino descartável: $name / $volume / $db / PostgreSQL $server_version"
    case "$kind" in
        new)
            run_sql "$name" "$db" backend/database/schema.sql
            run_sql "$name" "$db" backend/database/checks/20261025_clinical_access_seed.sql
            ;;
        upgrade)
            run_sql "$name" "$db" "$work_dir/schema_24.sql"
            run_sql "$name" "$db" backend/database/checks/20261025_clinical_access_seed.sql
            run_sql "$name" "$db" backend/database/migrations/20261025_add_clinical_access_evidence.sql
            if run_sql "$name" "$db" backend/database/migrations/20261025_add_clinical_access_evidence.sql > "$work_dir/reapply.log" 2>&1; then
                echo 'Reaplicação da migração foi aceita indevidamente' >&2
                exit 1
            fi
            [[ "$(cat "$work_dir/reapply.log")" == *'já existe'* ]] || {
                cat "$work_dir/reapply.log" >&2
                echo 'Reaplicação falhou por motivo inesperado' >&2
                exit 1
            }
            echo 'PASSOU: reaplicação da migração recusada'
            ;;
        base)
            run_sql "$name" "$db" "$work_dir/schema_base.sql"
            run_sql "$name" "$db" backend/database/migrations/20261024_add_clinical_access_grants.sql
            run_sql "$name" "$db" backend/database/checks/20261025_clinical_access_seed.sql
            run_sql "$name" "$db" backend/database/migrations/20261025_add_clinical_access_evidence.sql
            ;;
    esac
    run_sql "$name" "$db" backend/database/checks/20261025_clinical_access_exercise.sql
    docker restart "$name" >/dev/null
    for i in $(seq 1 60); do
        if docker exec "$name" pg_isready -U clinic_app -d "$db" >/dev/null 2>&1; then break; fi
        sleep 0.5
    done
    run_sql "$name" "$db" backend/database/checks/20261025_clinical_access_verify.sql
    echo "PASSOU: $kind"
done

# A tabela resultante deve ter o mesmo catálogo nos três caminhos.
catalog_sql="SELECT attnum, attname, format_type(atttypid, atttypmod), attnotnull
  FROM pg_attribute WHERE attrelid = 'public.clinical_access_grants'::regclass
    AND attnum > 0 AND NOT attisdropped ORDER BY attnum;
SELECT conname, pg_get_constraintdef(oid)
  FROM pg_constraint WHERE conrelid = 'public.clinical_access_grants'::regclass
  ORDER BY conname;"
for kind in new upgrade base; do
    docker exec "lumina_acl25_${kind}_${suffix}" psql -X -Atq -F '|' \
        -U clinic_app -d "lumina_acl25_${kind}" -c "$catalog_sql" > "$work_dir/catalog_${kind}.txt"
done
cmp "$work_dir/catalog_new.txt" "$work_dir/catalog_upgrade.txt"
cmp "$work_dir/catalog_new.txt" "$work_dir/catalog_base.txt"
echo 'PASSOU: catálogo da concessão equivalente nos três caminhos'

# Duas sessões disputam a mesma consulta; a segunda aguarda a primeira e
# ON CONFLICT impede uma segunda concessão. Este é um ensaio SQL, não HTTP.
name="lumina_acl25_new_${suffix}"
db=lumina_acl25_new
docker exec "$name" psql -X -q -v ON_ERROR_STOP=1 -U clinic_app -d "$db" -c \
    "INSERT INTO appointments (clinic_id, patient_id, dentist_id, scheduled_at, notes)
     SELECT clinic_id, patient_id, dentist_id,
            TIMESTAMPTZ '2026-10-26 09:00:00+00', 'ACL25 concurrent'
       FROM appointments WHERE notes = 'ACL25 completed'" >/dev/null
sql_prefix="BEGIN; SELECT id FROM appointments WHERE notes = 'ACL25 concurrent' FOR UPDATE;
UPDATE appointments SET status = 'CONFIRMED' WHERE notes = 'ACL25 concurrent';
INSERT INTO clinical_access_grants
    (appointment_id, clinic_id, patient_id, dentist_id, confirmed_by_user_id)
SELECT a.id, a.clinic_id, a.patient_id, a.dentist_id, d.user_id
  FROM appointments a JOIN dentists d ON d.id = a.dentist_id
 WHERE a.notes = 'ACL25 concurrent' ON CONFLICT (appointment_id) DO NOTHING;"
docker exec "$name" psql -X -q -v ON_ERROR_STOP=1 -U clinic_app -d "$db" \
    -c "$sql_prefix SELECT pg_sleep(1); COMMIT;" > "$work_dir/first.log" 2>&1 & first_pid=$!
sleep 0.15
docker exec "$name" psql -X -q -v ON_ERROR_STOP=1 -U clinic_app -d "$db" \
    -c "$sql_prefix COMMIT;" > "$work_dir/second.log" 2>&1 & second_pid=$!
wait "$first_pid"
wait "$second_pid"
docker exec "$name" psql -X -q -v ON_ERROR_STOP=1 -U clinic_app -d "$db" -c \
    "DO \$\$ BEGIN IF (SELECT count(*) FROM clinical_access_grants g
        JOIN appointments a ON a.id = g.appointment_id
        WHERE a.notes = 'ACL25 concurrent') <> 1
     THEN RAISE EXCEPTION 'Concorrência criou duplicidade'; END IF; END \$\$;" >/dev/null
echo 'PASSOU: concorrência, uma concessão por origem'
echo 'Todos os recursos exclusivos serão removidos pelo trap de saída.'
