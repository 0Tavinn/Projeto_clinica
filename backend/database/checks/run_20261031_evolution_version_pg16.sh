#!/usr/bin/env bash
# Ensaia somente a migração de versão em PostgreSQL 16 descartável.
set -euo pipefail
cd "$(dirname "$0")/../../.."

docker info >/dev/null
suffix="$(date +%s)_$$"
name="lumina_evolution_version_${suffix}"
volume="lumina_evolution_version_${suffix}"
database="lumina_acl25_new"
work_dir="$(mktemp -d /tmp/lumina-evolution-version.XXXXXX)"

cleanup() {
    docker rm -f "$name" >/dev/null 2>&1 || true
    docker volume rm "$volume" >/dev/null 2>&1 || true
    rm -rf -- "$work_dir"
}
trap cleanup EXIT

if docker container inspect "$name" >/dev/null 2>&1 \
    || docker volume inspect "$volume" >/dev/null 2>&1; then
    echo "Recurso exclusivo já existe: $name" >&2
    exit 1
fi

# Commit anterior à coluna, já com as evidências clínicas de 25/10.
git show be7c2f25a12c7f0d182e7aeae2e5f7ebbaddc948:backend/database/schema.sql \
    > "$work_dir/schema_previous.sql"
docker volume create "$volume" >/dev/null
docker run -d --name "$name" --network none \
    --mount "type=volume,src=$volume,dst=/var/lib/postgresql/data" \
    -e "POSTGRES_DB=$database" -e POSTGRES_USER=clinic_app \
    -e POSTGRES_PASSWORD=scratch-only-not-secret postgres:16-alpine >/dev/null

ready=false
for _ in $(seq 1 80); do
    if [[ "$(docker logs "$name" 2>&1)" == *'PostgreSQL init process complete; ready for start up.'* ]] \
        && docker exec "$name" pg_isready -U clinic_app -d "$database" >/dev/null 2>&1; then
        ready=true
        break
    fi
    sleep 0.5
done
[[ "$ready" == true ]] || { echo 'PostgreSQL temporário não ficou pronto' >&2; exit 1; }

run_sql() {
    docker exec -i "$name" psql -X -q -v ON_ERROR_STOP=1 \
        -U clinic_app -d "$database" < "$1"
}

run_sql "$work_dir/schema_previous.sql"
run_sql backend/database/checks/20261025_clinical_access_seed.sql
before="$(docker exec "$name" psql -X -Atq -U clinic_app -d "$database" \
    -c 'SELECT count(*) FROM clinical_evolutions')"
[[ "$before" =~ ^[1-9][0-9]*$ ]] || { echo 'Seed sem evolução existente' >&2; exit 1; }

run_sql backend/database/migrations/20261031_add_clinical_evolution_version.sql
result="$(docker exec "$name" psql -X -Atq -U clinic_app -d "$database" \
    -c 'SELECT count(*), min(version), max(version) FROM clinical_evolutions')"
[[ "$result" == "$before|1|1" ]] || { echo "Dados migrados inesperados: $result" >&2; exit 1; }

if run_sql backend/database/migrations/20261031_add_clinical_evolution_version.sql \
    > "$work_dir/reapply.log" 2>&1; then
    echo 'Reaplicação aceita indevidamente' >&2
    exit 1
fi
if docker exec "$name" psql -X -Atq -v ON_ERROR_STOP=1 -U clinic_app -d "$database" \
    -c 'UPDATE clinical_evolutions SET version=0' > "$work_dir/invalid.log" 2>&1; then
    echo 'Versão inválida aceita indevidamente' >&2
    exit 1
fi
echo "PostgreSQL 16: $before evolução(ões) preservada(s) em versão 1; reaplicação e versão 0 recusadas"
