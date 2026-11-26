# QA independente — OpenCL na Agenda

**Parecer: pronto com ressalvas para a entrega local de OpenCL na Agenda, no snapshot identificado abaixo.**
A comparação de intervalos, fallback e proteção concorrente funcionaram nos testes. Não foram reproduzidos defeitos de produto neste recorte. A implantação do snapshot no ambiente diário permanece não executada. A implementação está local, fora do commit-base publicado.

**Executor:** agente de QA. **Data:** 25/11/2026, America/Sao_Paulo.
**Checkout exclusivo:** /home/paulinho/Work/Projeto_clinica_clinical_2fa.
**Branch:** feat/paralelismo-agendamento.
**Commit-base:** f8f10c54a4a702b7d4feccbf5aeb98578db65909.
**Código efetivamente testado:** árvore local identificada por tested-source-hashes.json, tested-tracked.patch e source-snapshot/. Não atribuir os resultados ao PR18 puro nem à implementação de prontuários/OpenCL da branch de Tarcísio.

## 1. Identificação e preservação

O estado inicial tinha 17 arquivos preparados no índice para infraestrutura, seis arquivos rastreados com diferenças adicionais fora do índice e novos módulos/testes/documentação OpenCL não rastreados. Em arquivos como backend/Dockerfile, .env.example e compose.yml coexistiam camadas preparadas e locais. O ensaio usou os bytes da árvore local sem reorganizar o índice.

O SHA-256 dos bytes de git diff --cached --raw -z permaneceu, antes e depois:

41f728d17e0dcc8729b81db0f5abcf7ab900e8fd8249fa65dff173a07e8a4932

preservation.json confirma índice idêntico e 789 arquivos preexistentes conferidos por SHA-256, sem alteração ou desaparecimento. Os únicos arquivos novos desta revisão são artefatos QA e saídas do runner oficial. Não houve git add, reset, stash, checkout, switch, commit, push ou merge. A extração da base para comparar OpenAPI foi feita com git archive, sem mudar branch ou worktree.

## 2. Escopo e contrato aprovado

Detecção interna de sobreposição por clínica/dentista, um work-item OpenCL por intervalo, processamento em lotes e retorno à comparação sequencial quando necessário. Intervalos são semiabertos: fim igual ao início do próximo não conflita. OpenCL em CPU é educativo, sem requisito de ganho de velocidade.

O repositório mantém filtros de clínica, dentista, estados e exclusão do próprio ID. A validação de futuro/duração, o advisory lock e a exclusão GiST permanecem responsáveis pela consistência das gravações. Rotas, schemas HTTP, autorização e frontend não foram alterados pela implementação local examinada.

O guia docs/paralelismo-agendamento.md, fontes, configuração, Dockerfiles, pyproject, testes, runner e relatório histórico docs/relatorios/opencl-1795633269_5667a6d8-46a/ foram consultados. O histórico relata 65 direcionados e 97/1 na suíte completa, mas só os resultados da execução nova entram neste relatório.

## 3. Ambiente efetivo e isolamento

| Item | Verificação nova |
|---|---|
| Docker cliente/servidor | Conforme docker-version.txt |
| Python na imagem QA | 3.12.16 |
| PostgreSQL dos dois ensaios novos | 16.15, confirmado por SHOW server_version |
| NumPy | 2.2.6 |
| PyOpenCL | 2025.2.7 |
| FastAPI / SQLAlchemy | 0.141.1 / 2.0.52 |
| psycopg / Pydantic / pytest | 3.3.9 / 2.13.5 / 9.1.1 |
| Plataforma | Portable Computing Language |
| Dispositivo | cpu-haswell-13th Gen Intel(R) Core(TM) i5-13420H |
| Tipo / driver | CPU, reportado como ALL &#124; CPU / 6.0+debian |
| Banco | lumina_opencl_scratch, novo e exclusivo em cada ensaio |
| API do smoke | Uvicorn em contêiner próprio, acessível somente na rede QA |

O runner oficial criou imagens, rede, volume e contêineres com sufixo 1795639829_1da7510d-118. As sondagens independentes usaram qa-independent-351fa2e808, com rótulos de propriedade. A segunda tentativa reutilizou esses nomes somente depois de confirmar remoção de todos os recursos da primeira.

Foi aplicado backend/database/schema.sql do checkout apenas em bancos novos descartáveis. Não houve migração, stamp ou DDL em banco existente. As fixtures criaram dados fictícios, incluindo duas recepcionistas, dentista e pacientes distintos para a corrida. As autenticações da corrida usaram tokens válidos criados na fixture e um login HTTP real também foi exercitado. Não foram guardados tokens, senhas ou configurações sensíveis nos logs.

O Compose lumina_pr18_tarcisio, o volume lumina_pr18_tarcisio_postgres_data e demais recursos existentes foram preservados. Nenhum teste de escrita foi enviado às portas 18089/18088/55438. As sondagens independentes não publicaram portas no host.

## 4. Resultados sem duplicidade

| Execução nova | Resultado | Como contar |
|---|---|---|
| Runner oficial direcionado | 65 aprovados, 0 reprovados, 0 pulados | Subconjunto da coleta completa |
| Suíte completa do runner | 97 aprovados, 0 reprovados, 1 pulado | Mesmo conjunto coletado contém 98 IDs |
| União dos testes fornecidos | 98 IDs únicos aprovados em ao menos uma execução válida | O teste PG pulado na completa passou no direcionado |
| Sondagens adicionais do comparador | 5 testes aprovados | 37 comparações internas e chamadas paralelas não viram testes extras |
| Smoke HTTP/SQL independente | 11 verificações aprovadas | Diferencia HTTP implantado e SQL persistido |
| Contrato e empacotamento | 2 verificações aprovadas | Não são dois fluxos funcionais adicionais |
| Matriz consolidada | 116 itens aprovados, 0 reprovados, 0 bloqueados; 2 não executados fora do escopo | 118 linhas com granularidades identificadas |

Não somar 65+97. Os 65 IDs direcionados também aparecem na suíte completa; 64 passaram nas duas, enquanto o único teste PostgreSQL foi pulado apenas na execução sem URL PG. full-collection.txt, targeted-collection.txt e totais.json registram a reconciliação por ID.

O pulado é tests/test_opencl_pg.py::test_http_race_and_gist_authority, por ausência intencional de LUMINA_OPENCL_PG_URL na execução completa SQLite. Ele foi executado e aprovado no PostgreSQL no runner direcionado. Não há teste fornecido pendente por causa desse skip.

## 5. Kernel real, equivalência e falhas

Os testes direcionados exigem LUMINA_REQUIRE_OPENCL=1. As sondagens adicionais também exigiram engine=opencl, fallback=false e kernel_ns>0 nos casos não vazios. Assim, fallback não foi usado como prova de execução OpenCL.

Cobertura executada:
- Lista vazia sem kernel, adjacência nas duas bordas, igualdade, sobreposição parcial/total, inclusão e ausência de sobreposição.
- Lotes de diferentes tamanhos, inclusive cauda final e mais de 65 mil intervalos.
- Normalização UTC, fuso -03:00 equivalente, datas sem fuso interpretadas como UTC e precisão exata de um microssegundo. Sondagem adicional incluiu épocas anteriores a1970 e datas distantes suportadas por int64.
- Filtros do repositório em auto/sequential: mesma clínica/dentista, SCHEDULED/CONFIRMED contando, CANCELED/COMPLETED/NO_SHOW excluídos e próprio ID excluído na atualização.
- Falhas simuladas de importação, plataforma, dispositivo, construção/compilação e kernel, mantendo a regra sequencial.
- Falha em segundo lote, depois de primeiro lote OpenCL real, com conflito encontrado no terceiro lote sequencial. Resultado mixed, fallback=true, três lotes consumidos, sem perda do lote falho ou dos posteriores.
- Oito primeiras chamadas simultâneas após limpar o cache em processo QA: uma criação/compilação do programa, resultados corretos e eventos de kernel positivos.
- Filas, buffers e kernels por chamada em paralelo, sem resultado incorreto nos casos executados.
- Limites de lote inválidos e configuração inválida recusados conforme os testes.
- Falha no método build seguida de recuperação real em nova chamada.
- Mensagem de fallback inclui apenas a classe da exceção. A sentinela usada na exceção simulada não apareceu no log de fallback.

As falhas foram injetadas por mocks na sondagem, sem modificar código funcional. Isso demonstra os caminhos de recuperação, sem afirmar que houve queda real de driver ou falta física de CPU.

## 6. Concorrência PostgreSQL e smoke HTTP

O teste fornecido usa TestClient com sessões PostgreSQL independentes. Ele comprova duas esperas reais em pg_stat_activity, 201/409, uma gravação correspondente ao vencedor, conflito GiST mesmo com has_conflict contornado no harness, rollback e nova consulta adjacente201.

A sondagem independente subiu Uvicorn e chamou a API por HTTP real de outro contêiner QA:
- Health200, OpenAPI200, rota sem autenticação401 e login200 com access_token presente.
- Duas recepcionistas e pacientes diferentes disputaram o mesmo dentista/intervalo.
- pg_stat_activity registrou PIDs107 e109 em wait_event_type=Lock e wait_event=advisory antes da liberação.
- Respostas201/409 e uma linha persistida, pertencente ao paciente da resposta201.
- Atualização do próprio ID no mesmo instante com fuso equivalente retornou200.
- Horário adjacente retornou201.
- Deslocar a consulta em um microssegundo, invadindo a adjacente, retornou409. O horário persistido permaneceu o original.
- Uma inserção SQL sem pré-verificação recebeu SQLSTATE23P01 da GiST e rollback, mantendo duas linhas após a tentativa.

O health por si só é liveness e não comprova banco. As gravações e consultas SQL acima comprovaram comunicação real com PostgreSQL. Nenhuma dessas provas é teste de navegador.

## 7. Contrato HTTP e kernel empacotado

O runner verificou ausência de diff de routers/schemas/frontend e comparou o hash OpenAPI fornecido historicamente. Essa comparação isolada dependeria da identificação do baseline. Por isso, o QA extraiu a árvore backend do commit PR18 com git archive, importou-a em processo separado e gerou seu OpenAPI diretamente da fonte.

Resultado novo em independent-openapi-comparison.json:
- 18 caminhos na fonte PR18 e18 no código local.
- Objetos OpenAPI idênticos.
- SHA-256 canônico comum b959aa6f36ddcd38c350eac94d34ba3a51fa177f8fb3b0ff1f1084bd2290dba3.
- configure_mappers concluiu nos dois processos.

installed-package.json foi produzido com diretório de trabalho /tmp. O módulo e o kernel vieram de site-packages, não de um bind mount de fontes. O arquivo .cl consta dos arquivos da distribuição instalada. SHA-256 do kernel:
168dc63a66a964c4bcd6691ac38b9f6ef43e2edbd59b14682c8da157acb8f96b
Ele é idêntico ao snapshot do fonte examinado.

## 8. Pylance e Python local

O Python global WSL é3.14.4 e a consulta importlib não encontrou NumPy/PyOpenCL nesse interpretador. O projeto declara Python>=3.11,<3.13, e a imagem usa3.12.16 com as dependências requeridas presentes e executadas. Isso explica o alerta se o Pylance estiver configurado para o interpretador global.

A seleção efetiva do interpretador do editor não foi alterada nem comprovada nesta rodada. Não foram instalados pacotes no Python global. A ausência local não corresponde a falha de importação na imagem testada.

## 9. Benchmark educativo, separado do aceite

Executado scripts.benchmark_conflicts com dados fictícios, cinco repetições e mediana, excluindo SQL, HTTP e rede. Cache do driver pode existir. Inicialização separada do runtime:1,242418s no ensaio independente. O tempo de kernel foi obtido por profiling de eventos. O total inclui preparo NumPy, filas, buffers, cópias, lançamento, espera e redução.

| Intervalos | Sequencial total mediano | OpenCL total mediano | Kernel mediano |
|---|---:|---:|---:|
| 0 | 0,002886ms | 0,001511ms (modo auto sem kernel) | 0 |
| 32 | 0,004749ms | 0,914514ms | 0,003604ms |
| 4096 | 0,177614ms | 1,921062ms | 0,051549ms |
| 65536 | 3,342075ms | 43,976108ms | 1,431625ms |

OpenCL foi mais lento no total para todos os lotes não vazios medidos. A diferença entre total e kernel contém custos do host/transferência e outras etapas; essas parcelas individuais não foram cronometradas isoladamente. Não inferir latência HTTP nem ganho da aplicação a partir desse benchmark.

## 10. Falhas de roteiro e limites

Não houve defeito de produto reproduzido. A primeira tentativa das sondagens independentes foi inconclusiva e está preservada em tentativa-1/:
1. O script de fixture HTTP não importou todos os modelos ORM relacionados e parou antes da corrida por InvalidRequestError.
2. A extração do OpenAPI misturou um aviso de depreciação com o JSON e interrompeu o pós-processamento.

Foram corrigidos somente probe_http.py e run_independent.py no diretório QA. O código auditado não foi modificado. A tentativa incompleta não foi contada como aprovação, e seus testes repetidos não foram somados à execução válida. As duas correções estão declaradas e os arquivos anteriores foram preservados.

Os avisos restantes incluem depreciação de constante HTTP422 e outras advertências do conjunto fornecido. Não impediram as verificações. Logs completos permitem revisão.

Não executados fora do escopo: implantação deste snapshot nos serviços diários e teste de navegador. Esta revisão não autorizou nem executou essa implantação. O resultado não avalia o sistema de prontuários/OpenCL de Tarcísio.

## 11. Recursos e preservação final

O runner oficial removeu seus recursos de acordo com os rótulos de propriedade. A limpeza independente removeu contêineres API/PG, volume, rede e duas tags de imagens QA. independent-cleanup.json confirma removed=true para todos esses recursos. official-cleanup.txt ficou vazio para os nomes do runner.

Inventários de antes/depois de contêineres (nomes, imagens e portas), volumes e redes foram idênticos. Isso confirma o inventário desses recursos; não foi feito dump ou consulta aos dados dos bancos diários. Os scripts só enviaram SQL aos bancos novos próprios.

O índice tem o mesmo SHA-256 e nenhum dos789 arquivos preexistentes comparados mudou. Logs do backend anteriores e trabalhos preparados para infraestrutura foram preservados.

## 12. Reprodução

No checkout autorizado:
~~~bash
cd /home/paulinho/Work/Projeto_clinica_clinical_2fa
bash backend/tests/run_opencl_qa.sh
~~~

O runner cria uma nova pasta opencl-<id>, recursos únicos e limpeza por rótulo. Foi executado com limite externo de480s. Não executar Compose diário.

Para reproduzir as sondagens independentes sem sobrescrever esta rodada:
~~~bash
python3 docs/relatorios/qa/2026-11-25-f8f10c5-opencl-agenda/reproduzir_sondagens.py
~~~

O script confere hashes do snapshot, cria nova pasta de evidências e rótulos únicos, constrói as imagens do mesmo código local, extrai baseline por git archive e executa run_independent.py com limpeza em finally. Python global só orquestra Docker e lê arquivos; não importa NumPy/PyOpenCL. Builds têm limite de360s; a orquestração independente,480s. Se a fonte já tiver mudado, identificar a nova candidata antes do reteste, em vez de atribuir-lhe os resultados antigos.

Os comandos HTTP, locks, consultas SQL e asserções estão em probe_http.py. Testes do comparador em test_independent_opencl.py. Os logs estão vinculados por ID em matriz.csv.

## 13. Resumo para Paulo e relatório acadêmico

O agente de QA validou em25/11/2026 a implementação LOCAL de OpenCL da Agenda na branch feat/paralelismo-agendamento, sobre a base PR18 f8f10c54a4a702b7d4feccbf5aeb98578db65909. O kernel executou realmente em CPU POCL, manteve os resultados da regra sequencial nos casos testados e retornou com segurança ao cálculo sequencial sob falhas simuladas. PostgreSQL16.15 recusou gravações concorrentes conflitantes, preservando uma consulta e aceitando adjacência. A API HTTP exclusiva também passou no smoke. O contrato OpenAPI permaneceu idêntico à fonte PR18. Não foram reproduzidos defeitos de produto. Parecer pronto com ressalvas para esse snapshot local, com implantação diária ainda não executada. OpenCL foi mais lento no tempo total das amostras, compatível com o objetivo educativo. Índice, código e recursos existentes foram preservados.
