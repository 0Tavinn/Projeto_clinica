# Correção Backend N05-LOG — 26/11/2026

## Candidata e resultado

Correção implementada e testada pelo Backend na cópia:
**/home/paulinho/Work/lumina_odonto_correcao_N05_20261126**

É pacote avulso sem Git; não há commit ou branch desta candidata.
22 arquivos lógicos, sem .env privado e sem Zone.Identifier.
Manifesto SHA-256 canônico:
**e3b28488163b174758f7e3782dbe916b0cc1cf8120cadf5a3cd5da79200e2825**.
Mapa de arquivos em candidate-files-sha256.json e identidade em candidate-identity.json.
Imagem exata executada:
sha256:66df38568fedc56c15e39a176c01593a60894e2d677fba3195df4c0818e16c5d.

A política removeu as sentinelas dos logs nos caminhos exercitados e
preservou registros operacionais. A correção ainda precisa de reteste
independente do QA nesta nova identidade. Não se transfere o parecer
anterior nem se declara aceite de integração ou Sprint.

## Fonte e diagnóstico

Fonte exclusiva do pacote:
 /home/paulinho/Work/lumina_odonto_corrigido_QA/lumina_odonto_atualizado

Manifesto lógico original:
987ee7199972977bc549346246d0ee5bf46d4611b9d15c3c8fc89fdfbd41fe40.
Os20 arquivos lógicos foram conferidos contra o manifesto do QA.
Os40 arquivos recebidos, contando20 Zone.Identifier, foram preservados.

O QA de25/11 havia comprovado corpo422 sanitizado, mas query_sentinel_in_logs=true
no CMD original Uvicorn, sem prova de acesso por terceiros. Fontes lidas:
relatorio.md, privacy-log-check.json, api-sanitized.log, reproducao.md e
candidate-files-sha256.json na pasta de QA anterior.
Não reconstruí a imagem original para repetir o defeito: a evidência anterior
já identificava precisamente o access log como origem.

## Arquivos e solução mínima

| Arquivo | Alteração |
|---|---|
| app/logging_policy.py | Novo módulo com filtros dos loggers uvicorn.access, uvicorn.error e uvicorn. |
| app/main.py | Instala a política após registrar as rotas, antes de receber requisições. |
| tests/test_logging_policy.py | Oito testes focados de mensagem/args/exceção, valores de caminho/query e versões HTTP1.0/1.1. |
| README.md | Documenta política distribuída, operação e limites. |

candidate-vs-original.patch contém o diff completo desses quatro caminhos.
Dockerfile, dependências, busca, autorização, locks, versionamento, fallback,
kernel, frontend e SQL permaneceram com os bytes recebidos.

O access filter reconstrói msg/args antes do formatter Uvicorn, usando método,
rota estática e status. Não emite querystring, valores de parâmetros de
caminho, endereço do cliente ou mensagem original. Rotas inexistentes viram
[unmatched]. Mantém os cinco argumentos esperados por AccessFormatter e a
versão HTTP válida, sem exigir troca do formatter distribuído.

O filtro do servidor mantém nível e evento operacional. Descarta mensagem
arbitrária, args, exc_info, exc_text, stack_info e color_message, impedindo
que traceback ou formatter colorido reintroduza a entrada original.
Isso reduz o detalhamento de exceções no stdout/stderr. A investigação de
falhas deve usar reprodução controlada com dados fictícios.

A implementação usa somente logging da biblioteca padrão.
Não houve dependência nova nem flag externa de QA para esconder o log.
O CMD do Dockerfile foi preservado e conferido:
uvicorn app.main:app --host 0.0.0.0 --port8000.
A API de teste foi iniciada sem comando adicional após a imagem, herdando
exatamente esse CMD. A importação documentada uvicorn app.main:app também
instala a política.

## Ambiente e isolamento

Docker, imagem Python3.12.16, PostgreSQL16.16 em rede/volume exclusivos.
FastAPI0.165.0, Uvicorn0.54.0, SQLAlchemy2.1.9, psycopg3.3.9,
Pydantic2.14.4, pytest9.2.0, NumPy2.5.5 e PyOpenCL2026.1.5.
OpenCL real em CPU Intel i5-13420H/PoCL; buscas opencl/auto retornaram
engine=opencl. Não se apresenta fallback como prova de kernel real.

Nenhuma porta publicada. A sondagem HTTP rodou de outro contêiner da mesma
rede, sem TestClient para a prova de distribuição. O PostgreSQL novo recebeu
schema.sql e seed_demo.sql do pacote, seguidos de evolução fictícia por HTTP.
Não houve DDL ou migração em banco existente. Python global WSL só orquestrou
Docker e arquivos, sem instalar dependências.

## Testes executados nesta revisão

| Grupo | Resultado | Evidência |
|---|---|---|
| Testes fornecidos |18 aprovados, sem skips |tests.log; os18 permanecem separados dos novos testes |
| Logging focado |8 aprovados |tests.log; total do processo pytest26 aprovados,1 warning,1,77s |
| Sondagem HTTP real |16 verificações aprovadas |http-results.json e probe-execution.log |
| Erro real de servidor |500 e corpo sem eco, com log sanitizado |error-probe.log, api-sanitized.log |
| Política no stdout/stderr |Todas as verificações booleanas aprovadas |privacy-log-check.json |
| Preservação e limpeza |Originais/QA/Git/inventários conferidos; recursos próprios removidos |preservation.json, qa-evidence-preservation.json, git-before/after.json, cleanup.json |

A sondagem HTTP cobriu:
- Login e desbloqueio clínico normais com contas fictícias; criação de uma
  evolução usada como resultado autorizado.
- Buscas válidas cpu/opencl/auto, com engine e resultado conferidos.
  O conteúdo clínico autorizado apareceu no200, como esperado.
- Query clínica sem patient_id, Unicode percent-encoded, nomes de parâmetros
  diferentes, patient_id textual inválido, engine_name inválido e corpo
  clínico incompleto:422 sem eco das sentinelas.
- Token ausente e inválido:401. Paciente sem vínculo:403.
- Rota inexistente com sentinela no caminho e na query:404; log [unmatched].
- Rota parametrizada autorizada:200; log da rota com {patient_id}, sem seu valor.
- Requisição HTTP malformada:400 e evento operacional invalid_http_request.

Para exercitar traceback real, o ensaio parou **somente seu PostgreSQL
descartável**, enviou requisição com token clínico válido e recebeu500.
O access log manteve status500, e o error log registrou server_error,
sem mensagem/args/traceback clínico. O banco QA foi reiniciado depois;
todos os recursos próprios foram removidos ao final.

Extratos reais do log final, que não contêm termos clínicos:

~~~text
INFO:     - - "GET /api/v1/clinical/search HTTP/1.1" 422 Unprocessable Entity
INFO:     - - "GET /api/v1/clinical/search HTTP/1.1" 403 Forbidden
INFO:     - - "GET [unmatched] HTTP/1.1" 404 Not Found
INFO:     - - "GET /api/v1/clinical/search HTTP/1.1" 500 Internal Server Error
ERROR:    server_event=server_error
~~~

Não foi gravado log clínico bruto. O log do contêiner foi capturado em
memória, conferido contra as sentinelas e suas formas percent-encoded e
persistido somente por rotina de sanitização. O arquivo api-sanitized.log
tem o resultado operacional. Termos/tokens de teste não entram no resumo
dos resultados HTTP. Fixtures e sentinelas reconhecíveis permanecem somente
nos scripts de reprodução, sem dados reais.

## Tentativa inicial e limites

A primeira validação passou com23 testes (18 fornecidos+5 focados) e as
sondagens HTTP. A revisão identificou que a política normalizava a versão
HTTP para1.1 no registro. Antes de fechar a entrega, foi ajustada para manter
HTTP1.0/1.1 válido e foram ampliados os testes. Essa candidata final recebeu
nova imagem,26 testes aprovados e repetição das sondagens. A validação inicial
está arquivada em initial-validation/ e não é somada à contagem final.

Um warning de recuperação repetida de kernel do pacote permanece no log,
sem termo clínico. Não foi alterado: está fora do N05-LOG. A política não
oculta todos os logs nem promete cobrir futuras chamadas print/logging de
terceiros.

As alegações cobrem somente os loggers e os caminhos exercitados com a
configuração distribuída. Proxy, coletor, SQL echo e configurações externas
posteriores exigem revisão própria. Nenhum proxy/coletor foi fornecido ou
homologado. O500 testado é falha de conexão ao banco QA; não representa todas
as exceções possíveis da aplicação. Os testes focados também cobrem exceção
contendo sentinela e mensagem colorida, como complemento controlado.

As74 verificações independentes antigas e seus73 resultados aprovados não
foram repetidos nem somados. O reteste desta correção não comprova migração,
restauração, navegador ou integração com frontend.

## Preservação

original-files-before.json e original-files-after.json são idênticos:
40 arquivos do original, incluindo metadados Windows.
qa-evidence-preservation.json conferiu114 arquivos contra o manifesto
preexistente do QA, sem divergência.

Os dois checkouts protegidos mantiveram HEAD, status e índice idênticos:
- /home/paulinho/Work/Projeto_clinica:
  feat/paralelismo-agendamento, e49a3ce22f899ad64d971a50e8d7fd9c99cb5b3a.
- /home/paulinho/Work/Projeto_clinica_clinical_2fa:
  detached HEAD, e49a3ce22f899ad64d971a50e8d7fd9c99cb5b3a.

Nenhum checkout foi usado como fonte da correção.
Inventários de contêineres/imagens em uso/portas/inícios/reinícios,
volumes e redes são idênticos antes/depois do ensaio final.
cleanup.json confirma remoção de3 contêineres,1 volume,1 rede e1 imagem/tag,
sempre após conferir rótulo de propriedade. Não houve prune, implantação,
rebuild/restart dos serviços diários, stage ou commit.

## Repasse ao Tech Lead e QA

A nova candidata está implementada e testada pelo Backend para N05-LOG,
aguardando revisão independente. Comparar primeiro os22 hashes de
candidate-files-sha256.json com a pasta corrigida e conferir o manifesto
e3b28488163b174758f7e3782dbe916b0cc1cf8120cadf5a3cd5da79200e2825.

Para repetição sem sobrescrever esta evidência, criar uma pasta nova sob
/home/paulinho/Work/lumina-qa-evidence/ e copiar verify_candidate.py,
probe_privacy.py e paths.json desta pasta. O runner usa a pasta do próprio
script para saídas, gera nomes/rótulos novos e exige a candidata corrigida.
Executar python3 <nova-pasta>/verify_candidate.py. Não executar o runner
diretamente nesta pasta de evidências históricas.

Verificar de forma independente: CMD original da imagem, log útil,
ausência de termos/encoding/nome de parâmetro nos logs, erros401/403/422/404,
casos200 autorizados cpu/opencl/auto, erro500 e descarte de traceback.
O QA pode reutilizar as sentinelas fictícias ou criar outras, sem publicar
o log clínico bruto. O Tech Lead decidirá os encaminhamentos de integração
e publicação após essa revisão.
