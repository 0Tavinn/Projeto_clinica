# Reteste independente focado — N05-LOG

**Parecer: N05-LOG ENCERRADO no recorte da candidata e da configuração distribuída. Correção pronta com ressalvas de alcance.** As entradas fictícias não apareceram no stdout/stderr da API nos caminhos testados, e método, rota estática, status e eventos operacionais foram preservados. Não se declara aceite integrado, implantação, produção ou Sprint concluída.

**Executor: AGENTE DE QA. Data: 26/11/2026.** Não são resultados atribuídos a João Vitor nem reprodução dos números informados pelo Backend. A rodada anterior de 25/11 e sua finalização documental permanecem intactas.

## 1. Candidata, origem e diferença examinada

| Campo | Evidência |
|---|---|
| Fonte exclusiva | /home/paulinho/Work/lumina_odonto_correcao_N05_20261126 |
| Identificação | Pacote sem Git; **22 arquivos lógicos**; não existe SHA de commit desta entrega |
| Manifesto canônico SHA256 | **e3b28488163b174758f7e3782dbe916b0cc1cf8120cadf5a3cd5da79200e2825** |
| Cálculo | SHA256 do JSON do mapa caminho→SHA256, sort_keys=True, separators=(', ', ':') |
| Proveniência | Pacote anterior recebido de Tarcísio segundo Paulo; cópia N05 preparada pelo agente de Backend sob coordenação do Tech Lead e autorização de Paulo; sem autoria Git comprovada |
| Baseline de QA | Pacote987ee7199972977bc549346246d0ee5bf46d4611b9d15c3c8fc89fdfbd41fe40, ensaiado em 25/11 |
| Imagem principal construída/executada | sha256:94300c88ef7b4e4e19c41cf2124c4451d196592ba1f874f6d1ca4d0f94f6ad46 |
| Pasta desta evidência | /home/paulinho/Work/lumina-qa-evidence/2026-11-26-n05-log-qa-4c930a5405 |
| Referência do Backend, somente fonte auxiliar | /home/paulinho/Work/lumina-qa-evidence/2026-11-26-n05-log-backend-cfaac6e 1 |

Todos os bytes conferiram com o mapa final antes de iniciar. A candidata intermediária c2a4186… não foi construída, testada ou usada para aprovação. Não foram somados os 23 testes daquela tentativa do Backend, os 26 testes finais do Backend ou suas16 sondagens HTTP.

O diff independente confirmou **somente quatro caminhos**:
- app/logging_policy.py: módulo novo de filtros dos loggers Uvicorn.
- app/main.py: instala a política depois de registrar as rotas.
- tests/test_logging_policy.py: oito testes focados.
- README.md: contrato operacional e limites da política.

Dockerfile, CMD, pyproject.toml, SQL, regras clínicas, autorização, buscas, kernel e demais testes mantiveram os bytes do pacote anterior. Evidências: changes.json e candidate-vs-baseline.patch. Isso limita a superfície da regressão; não substitui o reteste de toda a aplicação nem transfere automaticamente o aceite antigo.

Os22 arquivos da candidata e os 40 arquivos do pacote original, incluindo Zone.Identifier, permaneceram iguais ao terminar. O pacote original não recebeu a correção.

## 2. Ambiente e execução real

| Componente | Identificação efetiva |
|---|---|
| Python | 3.12.16 |
| PostgreSQL principal | **16.16 (Debian 16.16-1.pgdg13+1)**, por SHOW server_version |
| FastAPI / Uvicorn | 0.165.0 / 0.54.0 |
| SQLAlchemy / psycopg / Pydantic | 2.1.9 / 3.3.9 / 2.14.4 |
| pytest / NumPy / PyOpenCL | 9.2.0 / 2.5.5 / 2026.1.5 |
| OpenCL real | PoCL 6.0+debian, OpenCL 3.0, CPU Intel i5-13420H, device_type 2 |
| Docker e Compose | Versões em docker-version.txt e compose-version.txt |
| Banco exclusivo | n05_qa_4c930a5405, usuário qa_n05 |
| Prefixo principal | lumina-n05-independent-4c930a5405 |
| API | Uvicorn HTTP real, mesma imagem e **CMD original** |
| CMD | uvicorn app.main: app --host 0.0.0.0 --port 8000 |
| Re de/volume | Próprios, com rótulo lumina.n05.independent e IDs conferidos |
| Portas públicas | Nenhuma |
| Dados | Seed recebido e uma evolução fictícia criada por HTTP |
| Segredos | Efêmeros, não publicados; arquivo temporário removido |

O build utilizou o Dockerfile original, sem editar configuração de logs no ensaio. Não se acrescentou --no-access-log, outro CMD ou servidor instrumentado para obter aprovação. A política testada veio **da própria candidata**.

A API e o cliente HTTP rodaram em contêineres separados da rede QA. O banco novo recebeu schema.sql e seed_demo.sql recebidos. Não houve instalação de dependências no Python global WSL, Compose diário, DDL em banco existente, migração ou escrita em serviços compartilhados.

As buscas cpu, auto e opencl retornaram 200 com o conteúdo fictício autorizado; os motores efetivos foram cpu, opencl e opencl. O teste OpenCL recebido também passou com runtime presente. Portanto a prova de OpenCL não é apenas fallback ou importação. Não houve benchmark nem repetição das corridas antigas.

Janela principal registrada: 2026-11-26T08:34:46.555618+00:00 até 2026-11-26T08:38:52.986920+00:00, equivalente a aproximadamente05:34–05:38 em America/Sao_Paulo. O complemento TRACE ocorreu depois, ainda em 26/11; a hora de arquivo de method-preservation.json identifica seu encerramento. Ver execution-window.json. A janela inclui preparação e limpeza, não representa soma de tempos de CPU.

## 3. Resultados e método de contagem

| Grupo desta execução independente | Aprovados | Reprovados de produto | Bloqueados | Não executados |
|---|---:|---:|---:|---:|
| Objetivos HTTP finais | **25** | 0 | 0 | 0 |
| Asserções transversais sobre logs dos mesmos caminhos | **23** | 0 | 0 | 0 |
| Comparação do OpenAPI | **1** | 0 | 0 | 0 |
| Testes recebidos anteriores | **18** | 0 | 0 | 0 |
| Testes recebidos focados em logging | **8** | 0 | 0 | 0 |

O processo pytest concluiu **26 aprovados, zero skips, 1 warning**. Os 18 anteriores e 8 focados são partes desse processo, não outra soma de26. As23 verificações de logs analisam as mesmas requisições dos25 objetivos HTTP: **não são23 percursos novos**. O OpenAPI também é uma verificação de contrato, não fluxo de usuário. Não se anuncia a soma dessas linhas como número de cenários distintos.

A matriz tem75 linhas:25 objetivos HTTP, 23 asserções de logs, 1 contrato e 26 testes recebidos. Contagens em totais.json. A primeira tentativa do método arbitrário foi preservada em tentativas.csv e não aumenta os totais finais. As 74 verificações independentes de 25/11 **não foram repetidas nem somadas**.

### Objetivos HTTP efetivamente exercitados

Pré-condição comum: API real da candidata final, cliente separado, dados fictícios, segredo e tokens mantidos somente em memória/contêiner descartável. Os erros devem omitir as entradas sensíveis; uma resposta 200 autorizada pode conter o dado clínico solicitado.

| ID | Cenário | Obtido | Situação | Evidência |
|---|---|---|---|---|
| F01-authentication | Login e desbloqueio clínico | 200 / 200; tokens obtidos | Aprovado | http-results.json; probe-execution.log |
| F02-create-fixture | Criação de evolução fictícia autorizada | 201 | Aprovado | http-results.json; probe-execution.log |
| F03-valid-cpu | Busca válida CPU | 200; engine=cpu; conteúdo autorizado presente | Aprovado | http-results.json; probe-execution.log |
| F03-valid-auto | Busca válida auto | 200; engine=opencl; conteúdo autorizado presente | Aprovado | http-results.json; probe-execution.log |
| F03-valid-opencl | Busca válida OpenCL | 200; engine=opencl; conteúdo autorizado presente | Aprovado | http-results.json; probe-execution.log |
| F04-original-422 | Reprodução original: q sem patient_id | 422; sem eco | Aprovado | http-results.json; probe-execution.log |
| F05-unicode-encoded | Termo Unicode percent-encoded | 422; sem eco | Aprovado | http-results.json; probe-execution.log |
| F06-double-encoded | Termo com dupla codificação | 422; sem eco | Aprovado | http-results.json; probe-execution.log |
| F07-sensitive-param-name | Nome de parâmetro sensível | 422; sem eco | Aprovado | http-results.json; probe-execution.log |
| F08-invalid-patient | patient_id inválido | 422; sem eco | Aprovado | http-results.json; probe-execution.log |
| F09-invalid-engine | Motor inválido | 422; sem eco | Aprovado | http-results.json; probe-execution.log |
| F10-clinical-body-422 | Corpo clínico incompleto | 422; sem eco | Aprovado | http-results.json; probe-execution.log |
| F11-password-body-422 | Senha de tipo inválido | 422; sem eco | Aprovado | http-results.json; probe-execution.log |
| F12-no-auth | Sem autenticação | 401; sem eco | Aprovado | http-results.json; probe-execution.log |
| F13-invalid-token | Token inválido | 401; sem eco | Aprovado | http-results.json; probe-execution.log |
| F14-no-link | Paciente sem vínculo | 403; sem eco | Aprovado | http-results.json; probe-execution.log |
| F15-unknown-route | Rota inexistente com caminho/query arbitrários | 404; sem eco | Aprovado | http-results.json; probe-execution.log |
| F16-unknown-unicode | Rota inexistente com Unicode | 404; sem eco | Aprovado | http-results.json; probe-execution.log |
| F17-parametrized-invalid | Valor de caminho inválido em rota parametrizada | 422; sem eco | Aprovado | http-results.json; probe-execution.log |
| F18-parametrized-authorized | Rota parametrizada autorizada | 200 | Aprovado | http-results.json; probe-execution.log |
| F19-real-sql-error | Exceção PostgreSQL real com entrada fictícia | 500 sem eco; contagem de evoluções intacta | Aprovado | http-results.json; probe-execution.log |
| F20-http-1.0 | Requisição HTTP/1.0 | 200; sem eco | Aprovado | http-results.json; probe-execution.log |
| F20-http-1.1 | Requisição HTTP/1.1 | 200; sem eco | Aprovado | http-results.json; probe-execution.log |
| F21-malformed-http | Requisição HTTP malformada | 400; sem eco | Aprovado | http-results.json; probe-execution.log |
| F22-recognized-trace | TRACE reconhecido; redação para OTHER | 405; log OTHER /health; sem eco | Aprovado | method-result.json; method-api-sanitized.log |

O complemento TRACE usa outra API da mesma candidata, com CMD original e rede própria, **sem banco**, pois o405 é produzido pelo roteamento antes de executar dependências SQL. Isso não é uma segunda prova de integração com PostgreSQL. Não repetiu as buscas, o erro SQL ou a suíte.

## 4. Reteste do defeito e provas dos logs

**Defeito anterior:** na identidade987ee71999…, GET /api/v1/clinical/search?q=<sentinela>, sem patient_id, devolvia422 protegido, mas gravava a entrada no access log.

**Resultado atual:** mesma finalidade de reprodução emF04 retorna422 sem eco; a captura em memória do stdout e do stderr não contém query, valores de caminho, nomes de parâmetros arbitrários, conteúdo de corpo, sentinelas de headers ou tokens. Também foram verificadas entradas Unicode, percent-encoded e double-encoded.

As verificações de erro examinam o corpo das respostas; sentinelas dos headers enviados também são procuradas nos logs. Não houve auditoria completa dos headers de resposta em todos os casos.

Não foi corrigida a privacidade pelo auxiliar: run_focused.py primeiro verifica os streams reais em memória e só depois persiste extratos sanitizados. A sanitização de distribuição não altera os booleanos observados. Caso uma sentinela aparecesse, a linha seria omitida do artefato e a verificação registraria falha; não seria apagada da conclusão. Nenhum log clínico bruto foi gravado na pasta de evidências.

Extratos operacionais reais:

~~~text
INFO:     - - "GET /api/v1/clinical/search HTTP/1.1" 422 Unprocessable Entity
INFO:     - - "GET /api/v1/patients/{patient_id}/record HTTP/1.1" 200 OK
INFO:     - - "GET [unmatched] HTTP/1.1" 404 Not Found
INFO:     - - "POST /api/v1/evolutions HTTP/1.1" 500 Internal Server Error
ERROR:    server_event=server_error
WARNING:  server_event=invalid_http_request
INFO:     - - "OTHER /health HTTP/1.1" 405 Method Not Allowed
~~~

Os seis primeiros provêm da execução principal; o último, do complemento TRACE. Os arquivos preservam os streams separadamente na rodada principal.

**Erro500 real:** um gatilho temporário no PostgreSQL exclusivo lançou uma exceção com a descrição fictícia. A requisição válida de criação retornou500 sem eco; a contagem de evoluções permaneceu igual, e o gatilho/função foram removidos. O stderr registrou server_event=server_error, sem traceback, parâmetros SQL ou marcador clínico. Não foi uma exceção falsa aplicada ao logger nem monkeypatch da API. A prova cobre essa família de exceção; não demonstra todos os erros possíveis.

**Observabilidade preservada:** método de operação suportado, rota estática/template, status, HTTP/1.0/1.1 e eventos de início/erro/parser foram encontrados. O formatter não apresentou erro. Os oito testes focados complementam a prova real com registros contendo exc_info, color_message e mensagens arbitrárias; a ausência de stack_info também é afirmada, sem prova específica com stack_info previamente preenchido; não substituem a execução servida.

Evidências centrais: privacy-log-check-final.json, api-stdout-sanitized.log, api-stderr-sanitized.log e method-api-sanitized.log. O arquivo privacy-log-check.json é a captura da primeira rodada, com dois campos falsos porque o método inventado não alcançou o caminho 405; foi preservado, não reescrito.

## 5. Tentativas de QA e distinção de defeitos

1. **Auxiliar com quebra de linha:** houve SyntaxError antes de iniciar Docker; o arquivo foi preservado em probe-attempt-1.txt. Corrigiu-se somente o auxiliar de QA. Isso não é falha do produto nem aprovação.
2. **Método arbitrário:** F22-unrecognized-method esperava405/OTHER, mas recebeu 400 sem eco. O parser rejeitou a requisição antes do roteamento ASGI e gerou invalid_http_request; não havia contrato aprovado exigindo405 para qualquer método inventado. A tentativa prova rejeição sem eco, mas **não prova** a redação OTHER do access log.
3. **Complemento necessário e restrito:** TRACE foi reconhecido pelo parser, chegou ao roteamento, recebeu 405 e gerou OTHER /health. O resultado está em method-result.json. A candidata não foi modificada. A suíte inteira não foi repetida.
4. A consolidação indica qual evidência complementa os dois campos originalmente falsos. As tentativas originais e seus resultados brutos **resumidos/sanitizados** continuam em http-results.json, privacy-log-check.json e tentativas.csv. Não foram convertidos silenciosamente em aprovação.

Não restou defeito de produto reproduzido no escopo N05-LOG exercitado. Essa afirmação não elimina defeitos não testados em outros módulos.

## 6. Contrato, comparação e limites

O OpenAPI servido porHTTP é estruturalmente **igual** ao JSON gerado da candidata anterior noQA25/11. Evidência: openapi-comparison.json eopenapi-http.json. A comparação é contra fonte identificada, não contra serviço diário possivelmente antigo. Login, desbloqueio, criação e buscas constituem as regressões focadas exercitadas.

A política reduz o diagnóstico disponível: exceções passam a ter evento genérico, sem mensagem, classe ou stacktrace. Isso protege a entrada clínica nos três loggers tratados, mas limita a investigação por logs. Uma futura estratégia de correlação/diagnóstico seguro pode ser definida pela equipe. Não é defeito novo contra o critério solicitado, pois método/rota/status/evento úteis foram preservados. Não se recomenda reativar tracebacks ou SQL echo com dados reais para compensar a redução.

O warning RepeatedKernelRetrieval apareceu no stderr e no pytest sem conteúdo clínico. Não foi alterado e não impediu a execução real de OpenCL. Mostra também que **warnings da biblioteca não são filtrados por essa política de Uvicorn**; a correção não é um filtro universal de saída do processo.

Não foram homologados: proxy, coletor, SQL echo, handlers externos, configuração de logging posterior à importação, logger de terceiros, prints futuros, outras famílias de exceção e rotas futuras. Os filtros cobrem uvicorn.access, uvicorn.error euvicorn na configuração distribuída. Ausência de marcador nos testes não comprova privacidade global para fontes não ensaiadas.

## 7. Preservação e limpeza

Preservados byte a byte:
- Candidata final22 arquivos.
- Pacote original40 arquivos, incluindo metadados.
- Artefatos históricos de QA25/11 e doBackend26/11.
- HEAD, status e SHA256 da saída de git diff --cached --raw -z dos dois checkouts protegidos (estado de alterações preparadas, não checksum do arquivo binário .git/index).

Os checkouts inventariados permaneceram em e49a3ce22f899ad64d971a50e8d7fd9c99cb5b3a: principal feat/paralelismo-agendamento; alternativo com HEAD destacado. Nenhum foi fonte do build ou alvo de alteração.

A rodada principal criou/removeu4 contêineres, 1 volume, 1 rede e 1 imagem/tag. O complemento criou/removeu2 contêineres, 1 rede e 1 imagem/tag, sem volume/banco. **Total removido:6 contêineres, 1 volume, 2 redes e 2 imagens/tags próprias.** Identidade e rótulo foram conferidos antes de remover; não houve prune.

Inventários antes/depois registram mesmos IDs de serviços preexistentes, imagens em uso, portas, inícios e contagem de reinícios. O Compose lumina_pr18_tarcisio e os ambientes históricos permaneceram intactos. Arquivo de segredos removido; nenhum token, senha real ou hash de senha é publicado. Não houve commit, push, merge, mudança de índice, implantação ouPDF.

Provas: preservation.json, preservation-final.json, git-before/after.json, inventory-before/after.json, cleanup.json, method-cleanup.json emethod-preservation.json. Inventário não equivale a checksum dos bancos diários; esses bancos não foram usados para teste ou escrita.

## 8. Parecer e próximos passos

| Objetivo | Parecer |
|---|---|
| Correção N05-LOG na identidade final | **Encerrada no recorte executado; pronta com ressalvas de alcance** |
| Resposta422 e logs operacionais exercitados | Aprovados; sem eco das sentinelas, com método/rota/status/eventos úteis |
| Preservação do contrato HTTP declarado | OpenAPI igual e regressões focadas aprovadas |
| Repetição das74 provas antigas | **Não executada nesta rodada** |
| Frontend/percurso no navegador | **Não executado; sem aceite** |
| Commit publicado desta correção | **Ausente; pacote sem Git** |
| Implantação, migrações, restauração | **Não executadas; planejamento/recursos correspondentes continuam pendentes** |
| Contratos propostos e decisões clínicas | Permanecem sujeitos ao alinhamento anterior; QA não os decidiu |
| Aceite integrado da entrega/Sprint | **Não concedido** |

Não é necessário manter N05-LOG aberto com base no log da identidade antiga: esse achado histórico foi corrigido nesta nova identidade e configuração testada. O parecer antigo permanece correto para o pacote antigo.

Próximo passo: TechLead/Paulo encaminhar a correção para publicação com referência verificável, conferir que o conteúdo publicado corresponde a estes 22 hashes e organizar integração com frontend identificado. As pendências de contrato da busca, migração/transição, D05/D06, exportação e rate limiting continuam separadas deste defeito. Não se deve usar este reteste como aprovação automática de um futuro commit diferente.

## Resumo para Cassiano

Em 26/11/2026, o AGENTE DE QA encerrou N05-LOG no recorte da candidata sem Git de manifesto e3b28488163b174758f7e3782dbe916b0cc1cf8120cadf5a3cd5da79200e2825. A imagem original foi servida em Uvicorn com PostgreSQL16.16 descartável e OpenCL real em CPU. Passaram25 objetivos HTTP finais, 23 verificações transversais dos mesmos logs e 1 comparação de OpenAPI; os 26 testes recebidos passaram sem skips, divididos em 18 anteriores e 8 focados. As contagens não representam soma de cenários distintos nem repetição das74 provas anteriores. Respostas e logs exercitados omitiram termos, corpos, caminhos, headers e tokens fictícios, preservando eventos úteis, inclusive erro SQL500 eHTTP/1.0/1.1. A expectativa indevida405 para método rejeitado com400 foi preservada e esclarecida; TRACE confirmou o caminho 405/OTHER. Não houve teste de navegador, aceite integrado, publicação ou implantação. Originais, Git e serviços existentes preservados; recursos próprios removidos.
