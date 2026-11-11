#!/usr/bin/env bash
# PostgreSQL 16 exclusivo; remove somente o contêiner e o volume que criou.
set -euo pipefail
cd /home/paulinho/Work/Projeto_clinica/backend
suffix="$(date +%s)_$$"
container="lumina_qa_two_finalize_${suffix}"
volume="$container"
database=lumina_clinical_api_scratch
cleanup() {
  docker rm -f "$container" >/dev/null 2>&1 || true
  docker volume rm "$volume" >/dev/null 2>&1 || true
}
trap cleanup EXIT
if docker container inspect "$container" >/dev/null 2>&1 || docker volume inspect "$volume" >/dev/null 2>&1; then
  echo "Recurso já existe: $container" >&2
  exit 1
fi
docker volume create "$volume" >/dev/null
docker run -d --name "$container" --mount "type=volume,src=$volume,dst=/var/lib/postgresql/data" \
  -p 127.0.0.1::5432 -e "POSTGRES_DB=$database" -e POSTGRES_USER=clinic_app \
  -e POSTGRES_HOST_AUTH_METHOD=trust postgres:16-alpine >/dev/null
ready=false
for _ in $(seq 1 80); do
  if [[ "$(docker logs "$container" 2>&1)" == *'PostgreSQL init process complete; ready for start up.'* ]] \
    && docker exec "$container" pg_isready -U clinic_app -d "$database" >/dev/null 2>&1; then
    ready=true
    break
  fi
  sleep 0.5
done
[[ "$ready" == true ]] || { echo 'PostgreSQL temporário não ficou pronto' >&2; exit 1; }
version="$(docker exec "$container" psql -X -Atq -U clinic_app -d "$database" -c 'SHOW server_version')"
[[ "$version" == 16.* ]] || { echo "Versão inesperada: $version" >&2; exit 1; }
docker exec -i "$container" psql -X -q -v ON_ERROR_STOP=1 -U clinic_app -d "$database" < database/schema.sql
port="$(docker port "$container" 5432/tcp)"
port="${port##*:}"
url="postgresql+psycopg://clinic_app@127.0.0.1:${port}/${database}"
echo "QA duas finalizações: $container / PostgreSQL $version"
ENVIRONMENT=test SECRET_KEY=pg16-scratch-test-only DATABASE_URL="$url" \
  LUMINA_CLINICAL_PG16_URL="$url" PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -s -q -p no:cacheprovider \
  /home/paulinho/Work/Projeto_clinica/docs/relatorios/qa/2026-10-31-2f7dbfe/qa_two_finalizations_pg16.py \
  --disable-warnings --tb=short
echo 'QA duas finalizações: recursos exclusivos removidos pelo trap.'
