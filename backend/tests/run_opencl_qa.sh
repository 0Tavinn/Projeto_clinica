#!/usr/bin/env bash
# Recursos exclusivos por execução; nunca usa Compose nem URLs do ambiente principal.
set -euo pipefail
cd "$(dirname "$0")/.."
suffix="$(date +%s)_$(cat /proc/sys/kernel/random/uuid | cut -c1-12)"
app_image="lumina-opencl-app-qa:$suffix"
qa_image="lumina-opencl-tests-qa:$suffix"
network="lumina_opencl_qa_$suffix"
db="lumina_opencl_db_$suffix"
volume="lumina_opencl_data_$suffix"
api="lumina_opencl_test_$suffix"
report="../docs/relatorios/opencl-$suffix"
mkdir -p "$report"
# Nomes livres e rótulo de propriedade impedem a remoção de recursos alheios.
for resource in "$api" "$db"; do
    if docker container inspect "$resource" >/dev/null 2>&1; then exit 1; fi
done
if docker volume inspect "$volume" >/dev/null 2>&1 \
    || docker network inspect "$network" >/dev/null 2>&1 \
    || docker image inspect "$app_image" >/dev/null 2>&1 \
    || docker image inspect "$qa_image" >/dev/null 2>&1; then exit 1; fi
cleanup() {
    for resource in "$api" "$db"; do
        if [[ "$(docker container inspect -f '{{index .Config.Labels "lumina.opencl.qa"}}' "$resource" 2>/dev/null)" == "$suffix" ]]; then
            docker rm -f "$resource" >/dev/null
        fi
    done
    if [[ "$(docker volume inspect -f '{{index .Labels "lumina.opencl.qa"}}' "$volume" 2>/dev/null)" == "$suffix" ]]; then
        docker volume rm "$volume" >/dev/null
    fi
    if [[ "$(docker network inspect -f '{{index .Labels "lumina.opencl.qa"}}' "$network" 2>/dev/null)" == "$suffix" ]]; then
        docker network rm "$network" >/dev/null
    fi
    for resource in "$qa_image" "$app_image"; do
        if [[ "$(docker image inspect -f '{{index .Config.Labels "lumina.opencl.qa"}}' "$resource" 2>/dev/null)" == "$suffix" ]]; then
            docker image rm "$resource" >/dev/null
        fi
    done
    return 0
}
trap cleanup EXIT
# Registra somente nomes/estados; nunca credenciais ou conteúdo do banco.
docker ps --format '{{.Names}} {{.Status}}' > "$report/containers-before.txt"
git diff --cached --raw -z | sha256sum > "$report/staged-before.sha256"
tar -cf - Dockerfile pyproject.toml README.md alembic.ini app alembic scripts tests database \
    | docker build --label "lumina.opencl.qa=$suffix" -t "$app_image" - > "$report/build-app.log" 2>&1
tar -cf - tests database scripts \
    | docker build --label "lumina.opencl.qa=$suffix" -f tests/opencl-qa.Dockerfile --build-arg "APP_IMAGE=$app_image" -t "$qa_image" - > "$report/build-qa.log" 2>&1
docker network create --label "lumina.opencl.qa=$suffix" "$network" >/dev/null
docker volume create --label "lumina.opencl.qa=$suffix" "$volume" >/dev/null
docker run -d --label "lumina.opencl.qa=$suffix" --name "$db" --network "$network" --network-alias pg \
    --mount "type=volume,src=$volume,dst=/var/lib/postgresql/data" \
    -e POSTGRES_DB=lumina_opencl_scratch -e POSTGRES_USER=opencl_qa \
    -e POSTGRES_PASSWORD=exclusive-qa-only postgres:16-alpine >/dev/null
ready=false
for _ in $(seq 1 90); do
    if docker exec "$db" pg_isready -h 127.0.0.1 -U opencl_qa -d lumina_opencl_scratch >/dev/null 2>&1; then
        ready=true
        break
    fi
    sleep 1
done
[[ "$ready" == true ]]
docker exec "$db" psql -X -At -U opencl_qa -d lumina_opencl_scratch -c 'SHOW server_version' > "$report/postgres-version.txt"
grep -q '^16\.' "$report/postgres-version.txt"
docker exec -i "$db" psql -X -q -v ON_ERROR_STOP=1 -U opencl_qa -d lumina_opencl_scratch < database/schema.sql > "$report/schema.log" 2>&1
# O ensaio dirigido exige auto explicitamente; a suíte completa usa o default sequential.
docker run --rm --label "lumina.opencl.qa=$suffix" --name "$api" --network "$network" \
    -e APPOINTMENT_CONFLICT_ENGINE=auto \
    -e LUMINA_OPENCL_PG_URL=postgresql+psycopg://opencl_qa:exclusive-qa-only@pg/lumina_opencl_scratch \
    "$qa_image" python -m pytest -q -p no:cacheprovider tests/test_opencl_conflicts.py tests/test_appointments.py tests/test_opencl_repository.py tests/test_opencl_pg.py --disable-warnings --tb=short \
    | tee "$report/targeted.log"
# Rotas e schemas mantêm os mesmos arquivos versionados no HEAD.
git diff HEAD --exit-code -- app/*/router.py app/*/schemas.py ../frontend/src > "$report/http-contract-diff.txt"
docker run --rm "$qa_image" python -c 'from app.main import app; from sqlalchemy.orm import configure_mappers; import json; configure_mappers(); print(json.dumps(app.openapi(), sort_keys=True))' > "$report/openapi.json"
# Hash canônico do OpenAPI PR18 obtido por GET pelo Tech Lead em 25/11.
python3 - "$report/openapi.json" > "$report/openapi-check.txt" <<'PY'
import hashlib, json, sys
document = json.load(open(sys.argv[1]))
digest = hashlib.sha256(json.dumps(document, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
assert digest == "b959aa6f36ddcd38c350eac94d34ba3a51fa177f8fb3b0ff1f1084bd2290dba3", digest
print(digest, len(document["paths"]), "paths; idêntico ao baseline PR18")
PY
docker run --rm "$qa_image" python -m scripts.benchmark_conflicts > "$report/benchmark.json"
docker run --rm "$qa_image" python -m pytest -q -p no:cacheprovider --disable-warnings --tb=short | tee "$report/full-suite.log"
git diff --cached --raw -z | sha256sum > "$report/staged-after.sha256"
cmp "$report/staged-before.sha256" "$report/staged-after.sha256"
cleanup
trap - EXIT
docker ps --format '{{.Names}} {{.Status}}' > "$report/containers-after.txt"
docker ps -a --filter "name=$suffix" --format '{{.Names}}' > "$report/cleanup.txt"
docker volume ls --filter "name=$volume" --format '{{.Name}}' >> "$report/cleanup.txt"
docker network ls --filter "name=$network" --format '{{.Name}}' >> "$report/cleanup.txt"
echo "Evidências em $report"
