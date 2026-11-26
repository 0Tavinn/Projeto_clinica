# Reprodução segura e índice das evidências

Execuções originais:25/11/2026. Documento preparado em 26/11. **Os comandos abaixo são roteiro para uma futura repetição**, não uma execução nova em 26/11. Parte do roteiro reúne comandos históricos em sequência mais fácil de repetir; os logs originais permanecem como prova do que foi executado.

## 1. Não misturar versões e bancos

Fonte exclusiva:/home/paulinho/Work/lumina_odonto_corrigido_QA/lumina_odonto_atualizado.
Não fazer checkout/switch nem copiar correções de outro backend. O pacote não é Git.
Verificar os 20 hashes de candidate-files-sha256.json antes do build. Os 40 arquivos, incluindo Zone.Identifier, estão nos inventários integrais.
Não usar Compose diário, nem suas portas18088/18089/55438, nem volume lumina_pr18_tarcisio_postgres_data.
O Compose recebido publica5432/8000; por isso não executar docker compose up diretamente no pacote.

Ferramentas usadas: Docker com acesso autorizado no WSL, Python 3 apenas para orquestração stdlib. Dependências Python funcionais ficam na imagem Python 3.12. Não instalar NumPy/PyOpenCL no Python global.

## 2. Comandos observados e artefatos

| Etapa efetivamente executada em 25/11 | Comando/roteiro | Saída |
|---|---|---|
| Build original | docker build --label lumina.corrected.qa=<prefixo> -t <prefixo>: source <pasta-original> | build-exact.log |
| Config isolada | docker compose -p <prefixo> -f <fonte>/docker-compose.yml -f <evidencias>/compose.qa.override.yml config --quiet | compose-config.log |
| Rede, volume, banco e API | python3 setup_and_core.py | resources.json, seed.log, sql-constraints.log, logs de inicialização |
| Testes recebidos | python -m pytest -v -ra --junitxml=/tmp/provided.xml --disable-warnings --tb=short, na imagem QA | provided-tests.log/xml |
| HTTP inicial | docker exec <prefixo>-driver python /qa/core_probe.py | core_probe.py.log |
| Concorrência | docker exec <prefixo>-driver python /qa/concurrency_replay.py | concurrency-replay.log; correção de pré-condição em appointment-race-final.log |
| Instrumentação | python /qa/instrumented_server.py em outro contêiner QA; instrumentation_probe.py no cliente | instrumentation-probe.log |
| Volume/paginação/Unicode/rollback | docker exec <prefixo>-driver python /qa/advanced_probe.py | advanced_probe.py.log |
| Resets | docker exec <prefixo>-driver python /qa/reset_probe.py | reset_probe.py.log |
| Revogação/preservação administrativa | final_probe.py; status_probe.py para a tentativa corrigida | final_probe.py.log, status_probe.py.log |
| Persistência | snapshot_db.py antes/depois; docker restart apenas <prefixo>-api e<prefixo>-db | persistence-*.json, persistence-http.log |
| Limpeza exclusiva | python3 cleanup_qa.py | cleanup.json, cleanup.log |

O script setup_and_core.py cria o arquivo de segredo efêmero e a configuração externa; cada recurso é identificado no resources.json. O arquivo de segredo **não** faz parte da entrega final. A aplicação recebeu seu schema por inicialização do PostgreSQL em volume vazio e o seed recebido por psql. O verificador SQL terminou com ROLLBACK intencional das suas próprias provas.

## 3. Preparar uma NOVA repetição sem sobrescrever evidências

**Esta sequência preparada em 26/11 não foi executada nesta data.** Ela reutiliza os auxiliares originais, com nomes exclusivos e somente dependências efetivas da entrega. A fonte recebida fica intacta. Necessário conferir o inventário de serviços antes de começar.

~~~bash
export QA_SOURCE=/home/paulinho/Work/lumina_odonto_corrigido_QA/lumina_odonto_atualizado
export QA_TEMPLATE=/home/paulinho/Work/lumina-qa-evidence/2026-11-25-pacote-corrigido-987ee71999-bd315
export QA_OUTPUT="$(mktemp -d /home/paulinho/Work/lumina-qa-evidence/repro-pacote-corrigido-XXXXXX)"

python3 - <<'PY'
from pathlib import Path
import os,json,hashlib,secrets,shutil
source=Path(os.environ["QA_SOURCE"])
template=Path(os.environ["QA_TEMPLATE"])
target=Path(os.environ["QA_OUTPUT"])
manifest=json.loads((template/"candidate-files-sha256.json").read_text())
for name,expected in manifest.items():
    assert hashlib.sha256((source/name).read_bytes()).hexdigest()==expected,name
names=["setup_and_core.py","qa_common.py","fixture.py","core_probe.py",
       "concurrency_probe.py","instrumented_server.py","instrumentation_probe.py",
       "advanced_probe.py","reset_probe.py","final_probe_reproduce.py",
       "snapshot_db.py","persistence_verify.py","cleanup_qa.py"]
for name in names:
    shutil.copyfile(template/name,target/name)
(target/"resource-prefix.txt").write_text("lumina-corrected-qa-"+secrets.token_hex(6))
(target/"resources.json").write_text("[]")
print("Manifesto conferido; auxiliares copiados para",target)
PY

export QA_PREFIX="$(cat "$QA_OUTPUT/resource-prefix.txt")"
docker ps -a --format '{{.Names}} {{.Image}} {{.Ports}}' > "$QA_OUTPUT/containers-initial.txt"
docker volume ls --format '{{.Name}}' > "$QA_OUTPUT/volumes-initial.txt"
docker network ls --format '{{.Name}}' > "$QA_OUTPUT/networks-initial.txt"

docker build --label "lumina.corrected.qa=$QA_PREFIX"   -t "$QA_PREFIX:source" "$QA_SOURCE" > "$QA_OUTPUT/build-exact.log" 2>&1
# Conferir o código de saída do build;se falhar,não adaptar o pacote para esconder a falha.
python3 "$QA_OUTPUT/setup_and_core.py"
# Conferir também os arquivos de saída:setup preserva códigos individuais de pytest/sondagens.
~~~

Os comandos operam em recursos descartáveis novos. Se houver erro, parar a etapa dependente, registrar a saída e executar a limpeza exclusiva do capítulo6. Não interpretar ausência de saída ou exceção de roteiro como aprovação.

### Concorrência e instrumentação

Executar concurrency_probe.py **uma vez no banco novo** antes de repetir testes em mesmo intervalo. A repetição de 25/11 exigiu novos pacientes eoutro horário; os auxiliares concurrency_replay.py eappointment_race_final.py preservam essa história e não devem ser usados indiscriminadamente sobre banco já alterado.

~~~bash
docker exec "$QA_PREFIX-driver" python /qa/concurrency_probe.py > "$QA_OUTPUT/concurrency.log" 2>&1

docker run -d --label "lumina.corrected.qa=$QA_PREFIX"   --name "$QA_PREFIX-instrumented" --network "$QA_PREFIX-net"   --network-alias qa-instrumented   --env-file "$QA_OUTPUT/.qa-ephemeral.env"   --mount "type=bind,src=$QA_OUTPUT,dst=/qa,readonly"   -e PYTHONPATH=/app:/qa "$QA_PREFIX:source"   python /qa/instrumented_server.py > "$QA_OUTPUT/instrumentation-start.log"

# Registrar imediatamente o contêiner próprio para a limpeza.
python3 - <<'PY'
import os,json
from pathlib import Path
p=Path(os.environ["QA_OUTPUT"])
items=json.loads((p/"resources.json").read_text())
items.append({"kind":"container","name":os.environ["QA_PREFIX"]+"-instrumented"})
(p/"resources.json").write_text(json.dumps(items,indent=2))
PY

# Aguardar health somente no contêiner exclusivo;tempo máximo aproximado de10s.
docker exec -i "$QA_PREFIX-driver" python - <<'PY'
import httpx,time
for _ in range(50):
    try:
        r=httpx.get("http://qa-instrumented:8000/health",timeout=1)
        if r.status_code==200:
            break
    except httpx.HTTPError:
        pass
    time.sleep(.2)
else:
    raise RuntimeError("API instrumentada indisponivel")
PY

docker exec "$QA_PREFIX-driver" python /qa/instrumentation_probe.py > "$QA_OUTPUT/instrumentation-probe.log" 2>&1
docker exec "$QA_PREFIX-driver" python /qa/advanced_probe.py > "$QA_OUTPUT/advanced-probe.log" 2>&1
docker exec "$QA_PREFIX-driver" python /qa/reset_probe.py > "$QA_OUTPUT/reset-probe.log" 2>&1
docker exec "$QA_PREFIX-driver" python /qa/final_probe_reproduce.py > "$QA_OUTPUT/final-probe.log" 2>&1
python3 "$QA_OUTPUT/persistence_verify.py"
~~~

No comando com Python recebendo heredoc, usar **docker exec -i** para encaminhar stdin. Essa forma correta está refletida na revisão final deste documento. Conferir cada código de saída; as rotinas case também podem registrar bloqueado/reprovado sem encerrar o processo com erro. Inspecionar as linhasQA_CASE.

final_probe_reproduce.py é auxiliar de QA preparado em 26/11 com somente a chave da resposta corrigida de id para appointment_id; ele não foi executado nessa data. O erro original e a repetição efetiva de 25/11 continuam nos arquivos históricos. persistence_verify.py reúne o reinício observado em 25/11 para futura reprodução; compile/syntax check não significa teste funcional novo.

### Como comprovar N01 corretamente

1. O script segura a linha do vínculo com outra conexãoSQL.
2. A requisição HTTP é iniciada; waitlocks() consulta pg_stat_activity até comprovar wait_event_type=Lock.
3. A mesma transação controladora revoga econfirma ocommit antes da resposta.
4. Conferir 403, ausência de results evínculoREVOKED. Para escrita, comparar descrição, notes, status, version efinalized_at antes/depois.
5. Na prova instrumentada OpenCL, conferir telemetry.events.event_before_commit=1, event_after_commit=1, kernel_really_completed=true. Somente esses sinais comprovam a janela RUNNING observada. Se hardware/carga fizerem o evento terminar cedo, registrar prova não obtida; um 403 sozinho não comprova revogação durante kernel.
6. O caso CPU revoga após a comparação real eantes de retornar à rota; não é prova de revogação durante instruçõesCPU. Não inserir atrasos artificiais e descrevê-los como kernel despachado.

### Como comprovar N07 corretamente

Bloquear o vínculo, iniciar duas requisições PATCH com mesma versão, demonstrar dois waiters, liberar econferir 200/409. Ler o banco e comparar description com o JSON da resposta 200; version deve subir uma vez. Não contar 422 por falta de versão como prova de concorrência.

## 4. Reprodução mínima de N05-LOG

No banco exclusivo, usar login edesbloqueio fictícios do fixture.py e API iniciada pelo CMD original do Dockerfile. Enviar GET /api/v1/clinical/search com q=sentinela fictícia esem patient_id. Conferir 422; procurar a sentinela em memória no corpo eno docker logs do contêineroriginal. **Não publicar o log bruto**, pois ele pode carregar a entrada fictícia; salvar apenas booleanos eum extrato redigido. Não usar o servidor instrumentado para esta prova: ele desabilita seu próprio access log.

Evidência de 25/11: privacy-log-check.json eapi-sanitized.log. Oresultado foi corpo sem eco, mas query_sentinel_in_logs=true. Nenhuma conexão extra ou instrumentação é necessária para reproduzir o log.

## 5. Contratos e leitura de resultados

openapi-baseline.json/openapi-candidate.json vieram de importações em processos isolados, sem consultar serviços diários. openapi-differences.json revela somente mudanças estruturais no GET da busca; não cobre sozinho mudanças de autorização, inteiro estrito e sanitização.

A matriz contém o último resultado válido porID. tentativas.csv preserva as tentativas coletadas, mas não é outra suíte. Não somar 18 unitários como novos cenários além das 74 sondagens. Datas de 26/11 emdocumentos ehelpers não mudam a data real das execuções originais.

## 6. Limpeza de recursos próprios

~~~bash
python3 "$QA_OUTPUT/cleanup_qa.py"
~~~

O auxiliar exige prefixo próprio erótulo lumina.corrected.qa idêntico antes de remover contêiner, volume, rede ouimagem. Não usa prune, nem down -v. Oarquivo efêmero de ambiente também é removido. Ao terminar, comparar inventários, hashes do pacote e estado Git somente porleitura.

A execução original já foi limpa em 25/11: cleanup.json registra todos os recursos removidos; preservation.json registra os inventários iguais. Não há necessidade derepetir limpeza nos serviços existentes.

## 7. Evidências reais versus ausentes

- Reais: logs resumidos HTTP, JUnit, telemetria OpenCL, pg_stat_activity, digests SQL, versões einventários.
- Ausentes: navegador, prints, vídeos, aceite visual, upgrade deste pacote, restauração desta rodada, prova de um futuro Git equivalente.
- Originais preservados: logs das tentativas, pacote recebido, relatórios de 23/11 echeckpoints anteriores.
