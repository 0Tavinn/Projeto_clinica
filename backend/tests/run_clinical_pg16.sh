#!/usr/bin/env bash
# API + PostgreSQL 16 temporários; nunca usa Compose ou o volume da revisão.
set -euo pipefail
cd "$(dirname "$0")/.."

docker info >/dev/null
suffix="$(date +%s)_$$"
container="lumina_clinical_api_${suffix}"
volume="lumina_clinical_api_${suffix}"
database="lumina_clinical_api_scratch"

cleanup() {
    docker rm -f "$container" >/dev/null 2>&1 || true
    docker volume rm "$volume" >/dev/null 2>&1 || true
}
trap cleanup EXIT

if docker container inspect "$container" >/dev/null 2>&1 \
    || docker volume inspect "$volume" >/dev/null 2>&1; then
    echo "Recurso exclusivo já existe; ensaio cancelado: $container" >&2
    exit 1
fi

docker volume create "$volume" >/dev/null
docker run -d --name "$container" \
    --mount "type=volume,src=$volume,dst=/var/lib/postgresql/data" \
    -p 127.0.0.1::5432 \
    -e "POSTGRES_DB=$database" \
    -e POSTGRES_USER=clinic_app \
    -e POSTGRES_HOST_AUTH_METHOD=trust \
    postgres:16-alpine >/dev/null

ready=false
for _ in $(seq 1 80); do
    # O entrypoint inicia um servidor temporário; esperar o servidor definitivo.
    if [[ "$(docker logs "$container" 2>&1)" == *'PostgreSQL init process complete; ready for start up.'* ]] \
        && docker exec "$container" pg_isready -U clinic_app -d "$database" >/dev/null 2>&1 \
        && docker exec "$container" psql -X -Atq -U clinic_app -d "$database" -c 'SELECT 1' >/dev/null 2>&1; then
        ready=true
        break
    fi
    sleep 0.5
done
if [[ "$ready" != true ]]; then
    echo "PostgreSQL temporário não ficou pronto: $container" >&2
    exit 1
fi

version="$(docker exec "$container" psql -X -Atq -U clinic_app -d "$database" -c 'SHOW server_version')"
[[ "$version" == 16.* ]] || { echo "Versão inesperada: $version" >&2; exit 1; }
port="$(docker port "$container" 5432/tcp)"
port="${port##*:}"
[[ "$port" =~ ^[0-9]+$ ]] || { echo 'Porta temporária inválida' >&2; exit 1; }

docker exec -i "$container" psql -X -q -v ON_ERROR_STOP=1 \
    -U clinic_app -d "$database" < database/schema.sql

url="postgresql+psycopg://clinic_app@127.0.0.1:${port}/${database}"
echo "Ensaio de API em $container / PostgreSQL $version"
ENVIRONMENT=test SECRET_KEY=pg16-scratch-test-only \
    DATABASE_URL="$url" LUMINA_CLINICAL_PG16_URL="$url" \
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
    .venv/bin/python -m pytest -q -p no:cacheprovider \
    tests/test_clinical_pg16.py --disable-warnings --tb=short

echo 'Ensaio concluído; o contêiner e o volume exclusivos serão removidos.'
