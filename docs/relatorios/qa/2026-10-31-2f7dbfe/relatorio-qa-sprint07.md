# QA da Sprint 7 — Lumina Odonto — 31/10/2026

**Parecer: não pronto para o aceite da Sprint 7.** O ambiente Docker exclusivo funcionou e os fluxos principais da API passaram em PostgreSQL 16. Há, porém, duas falhas de integridade clínica sob concorrência, uma incompatibilidade que impede a conclusão pela interface e entregas obrigatórias da Sprint ainda ausentes. A interface não foi testada em navegador nesta sessão. Este ensaio foi executado pelo agente de QA por autorização de Paulo Sérgio; **não é resultado de João**.

## 1. Versão, fontes e ambiente

| Item | Evidência desta execução |
| --- | --- |
| Repositório | `/home/paulinho/Work/Projeto_clinica`, branch `chore/sprint-07-docker-integration` |
| HEAD e referência remota | `2f7dbfe6d0d7a747f57dbeeede3a716938adc5fa`; `git ls-remote` confirmou o mesmo hash na branch remota e no head do PR #16 no início do ensaio |
| Trabalho local prévio preservado | Oito documentos de requisitos/regras modificados e quatro relatórios de 29/10 não rastreados. Nenhum arquivo funcional da API, frontend ou SQL estava modificado. Os artefatos desta pasta foram acrescentados; nada anterior foi alterado. |
| Período | 31/10/2026, 13:36:49–14:01:48 UTC, cerca de 25 minutos. Host em `-03:00`; API e PostgreSQL em UTC. |
| Ferramentas | Docker cliente/servidor 29.9.2; Compose v5.6.1; Python de teste 3.12.14; PostgreSQL 16.15 em `postgres:16-alpine`. |
| Versão executada | Imagens reconstruídas da árvore de código do HEAD: API `sha256:e2cde74d469a3426f2506291488f646b0e5db7333eb9719486c4e7f68f63f019`, frontend `sha256:6e0a2200186ba35e5f32cdebb9a8bd6bc2b766469fe4cc71bca416c09ddc6d0e`; PostgreSQL `sha256:f4610795587492cd4fb887c2dc3de301b813278bb6f616992061141b5f15ac36`. As alterações locais eram documentais e não entraram nas imagens. |
| Isolamento | Projeto `lumina_qa_20261031_2f7dbfe`, banco `lumina_qa_20261031_2f7dbfe_db`, volume `lumina_qa_20261031_2f7dbfe_pg16_data`, rede com mesmo prefixo; API/HTML apenas em `127.0.0.1:18128/18129`. Um override externo substituiu os nomes fixos de volume/rede do Compose. |
| Dados | Fictícios: duas clínicas, oito contas (admin, recepção A/B, dois dentistas A, dentista B, dentista sem perfil profissional, usuário inativo), 12 pacientes e 16 consultas controladas ao fim da matriz. A confirmação válida foi feita pela API. Uma consulta `CONFIRMED` criada diretamente sem procedência serviu somente de caso negativo. |

Fontes lidas: contratos `backend/app/appointments/README.md` e `backend/app/records/README.md`; repasses `docs/clinical-api-technical-handoff.md` e `docs/clinical-access-grants-handoff.md`; `docs/sprint/sprint-07.md`; RF-023/RF-024, RN-031/RN-032 e índice de decisões; código, suítes e scripts PostgreSQL versionados. Os resultados antigos desses repasses foram tratados como histórico, **não** como prova deste commit.

O PR publicado ainda traz a redação de 24/10 para RF-023/RN-031, que previa permanência após cancelamento ou ausência. A revisão local, registrada como aprovada por Paulo em 25/10, define preparação enquanto existir confirmação confiável ativa e continuidade após atendimento realizado com evidência. O código executado usa esta última política. A divergência entre requisito publicado, revisão local e implementação deve ser resolvida antes do aceite final. D02–D06 continuam abertos nos pontos indicados no índice local; este QA não os decidiu.

## 2. Execução e contagem

A [matriz completa](matriz-testes.csv) contém **209 linhas: 197 aprovadas, 8 reprovadas, 1 bloqueada e 3 não executadas**. Os cinco casos PostgreSQL pulados na rodada SQLite foram executados em PostgreSQL e contados uma vez. A rodada SQLite foi repetida para obter XML por teste; a repetição também não foi somada.

| Camada na matriz | Aprovado | Reprovado | Bloqueado | Não executado |
| --- | ---: | ---: | ---: | ---: |
| TestClient/serviço com SQLite | 82 | 0 | 0 | 0 |
| Testes de API versionados em PostgreSQL 16, mais duas finalizações | 6 | 0 | 0 | 0 |
| HTTP na API/serviços de QA | 99 | 1 | 0 | 0 |
| Disputas e persistência PostgreSQL/HTTP | 3 | 3 | 0 | 0 |
| SQL e ensaio DBA descartável | 7 | 1 | 0 | 0 |
| Inspeção de código/contrato da Sprint | 0 | 3 | 1 | 0 |
| Interface visual em navegador | 0 | 0 | 0 | 3 |
| **Total** | **197** | **8** | **1** | **3** |

Evidências principais:

- [Suíte SQLite](pytest-sqlite-junit.log): `82 passed, 5 skipped` em SQLite em memória; [XML individual](pytest-sqlite.xml). A primeira tentativa dentro do isolamento de processo ficou sem saída no primeiro `TestClient` e foi interrompida; uma tentativa limitada a 45 s repetiu o bloqueio. Fora desse isolamento, a suíte terminou em 12,66 s. Isso foi um limite do ambiente de execução, não uma falha atribuída à aplicação.
- [API/PostgreSQL 16](pytest-pg16-junit.log): cinco testes versionados passaram em banco descartável, cobrindo fluxo HTTP e reinício da API, duas confirmações/conclusões da Agenda, edição contra finalização, revogação durante **criação** de rascunho e rollback. [XML](pytest-pg16.xml). Esses testes não cobriam perda de autorização durante **edição/finalização** nem duas edições do mesmo rascunho; tais cenários foram executados separadamente abaixo.
- [Duas finalizações da mesma evolução](two-finalizations-pg16.log): em outro PostgreSQL 16 descartável, respostas `200/422`, uma evolução `FINALIZED` íntegra. Isso é diferente das duas **conclusões de consulta** testadas na suíte versionada.
- [Ensaio SQL DBA](sql-pg16.log): esquema novo, duas rotas de atualização descartáveis, recusa de reaplicação, catálogo equivalente e uma concessão sob disputa passaram. Nenhuma migração foi aplicada a volume existente.
- [Matriz HTTP](http-results.json), [concorrência](concurrency-results.json), [sondagens adicionais](additional-results.json), [segunda clínica](second-clinic-results.json), [persistência](persistence-result.json) e [inspeção do bundle/OpenAPI](feature-inspection.json). Os logs correspondentes e os scripts auxiliares estão nesta pasta.

### Comportamentos comprovados nesta versão

- API importada com mapeadores válidos e `SELECT 1` real pelo contêiner da API; `/health`, frontend HTML, bundle, CORS e OpenAPI responderam. O bundle servido apontava para `http://localhost:18128/api/v1`.
- Autenticação, refresh, inativação posterior de token, filtros combinados da Agenda, confirmação pela recepção, conclusão pelo dentista responsável em rota específica e `PATCH` genérico. Administrador, recepção e outro dentista foram recusados na conclusão. `care_occurred_at` sem fuso, futuro ou ausente foi recusado; valor `-03:00` válido representou o mesmo instante armazenado em UTC.
- Prontuário autorizado com `general_notes`; rascunho próprio criado, editado e finalizado; finalizadas compartilhadas entre dois dentistas autorizados, rascunhos privados; edição e nova finalização de registro finalizado recusadas; duplicidade por consulta `409`; vínculos de paciente, dentista e clínica incompatíveis recusados. Erros seguiram o envelope e uma sentinela clínica fictícia não voltou no `422`.
- Administrador, recepção, dentista sem perfil profissional, dentista sem fundamento e outra clínica não leram conteúdo clínico. O dentista B, após confirmação real por sua recepção, abriu o prontuário B (`200`) e continuou sem acesso ao paciente A (`403`). Conta inativa não fez login e token/refresh anteriormente válidos passaram a `401` após inativação.
- Primeira confirmação cancelada ou marcada como ausência retirou acesso quando não havia outro fundamento. Outra confirmação manteve a preparação após cancelar uma das consultas; cancelar a última retirou o acesso. Atendimento concluído com evidência manteve a continuidade após cancelamento ou ausência posterior. `CONFIRMED` legado sem procedência não concedeu acesso.
- Abertura simultânea por dois GETs retornou o mesmo ID e deixou um prontuário; rollback simulado pela suíte PostgreSQL não deixou prontuário/evolução residual; confirmação e conclusão simultâneas produziram uma evidência consistente.
- Reinícios da API e do PostgreSQL no mesmo volume preservaram contagens, IDs e histórico. Recriação dos três contêineres **sem remover o volume** preservou as mesmas contagens e GETs clínicos `200`. Isso não demonstra migração ou recuperação de um banco de equipe.

## 3. Defeitos reproduzidos e bloqueios

Todos os defeitos abaixo referem-se à branch e ao hash da seção 1. Os passos usam somente a base fictícia PostgreSQL 16.15 exclusiva. Os responsáveis são **propostas de encaminhamento**, não atribuição de execução a João.

### QA-01 — Crítica — escrita após perda da última autorização

**Reprodução:** executar `qa_concurrency.py`: confirmar uma consulta pela API, criar rascunho, manter a linha da evolução bloqueada em outra conexão, iniciar `PATCH /draft` ou `POST /finalize`, comprovar espera por lock em `pg_stat_activity`, cancelar pela recepção a única consulta que sustenta acesso, liberar o lock e ler o resultado. **Esperado:** mutação negada (`403`), rascunho inalterado. **Obtido:** nos dois casos o cancelamento foi `200` e a mutação pendente também foi `200`; a edição alterou a descrição e a finalização gravou `FINALIZED`. Um GET posterior foi `403`, comprovando que o fundamento já não existia. [Evidência](concurrency-results.json); o serviço verifica acesso antes do bloqueio em `backend/app/records/service.py:140-151` e não reconfere depois. **Impacto:** alteração de conteúdo clínico sem autorização vigente. **Correção proposta:** backend, sob coordenação de Paulo/Tech Lead; reconferir a origem após a espera, repetir ambos os cenários e regressões de cancelamento/continuidade.

### QA-02 — Alta — duas edições sobrescrevem o mesmo rascunho

**Reprodução:** com rascunho autorizado, bloquear sua linha; disparar dois PATCHs concorrentes com descrições fictícias A e B; confirmar as duas esperas; liberar o lock. **Esperado:** conflito explícito ou outra política aprovada que evite sobrescrita silenciosa (RF-024-CA10). **Obtido:** `200/200`, texto final B; nenhuma resposta sinalizou que A foi substituída. [Evidência](concurrency-results.json). **Impacto:** perda silenciosa de informação clínica. **Correção proposta:** backend; definir e aplicar controle de versão/conflito e repetir sob PostgreSQL.

### QA-03 — Alta — contrato da conclusão não é atendido pelo frontend

**Reprodução:** examinar o bundle reconstruído e `frontend/src/api.ts:408-413`; a chamada atual envia apenas `{status}`. Enviar esse mesmo corpo à rota `PATCH /appointments/{id}/status` após confirmação confiável. **Esperado:** para concluir, a interface coleta e envia `care_occurred_at` com fuso. **Obtido:** API `422` para o corpo usado pelo frontend; a API concluiu com `200` quando recebeu o horário válido no ensaio HTTP. [Evidência HTTP](http-results.json), [inspeção](feature-inspection.json). **Limite:** não houve clique real em navegador; a falha é comprovada na integração de contrato, não como captura visual. **Impacto:** caminho de conclusão pela interface bloqueado. **Correção proposta:** frontend (Caio/Otávio), com regressão de contrato e fluxo visual.

### QA-04 — Média — configuração do limite de login ignorada

**Reprodução:** configurar `LOGIN_RATE_LIMIT=100/minute` no contêiner QA e executar seis logins fictícios do mesmo IP em menos de um minuto. **Esperado:** o limite configurado permitiria a sexta tentativa. **Obtido:** `429` na sexta; `backend/app/security/rate_limit.py:46` fixa `5` em código. [Evidência](http-results.json). A sondagem aguardou 61 s e prosseguiu. **Impacto:** configuração operacional ineficaz e bloqueio de usuários/testes em IP compartilhado. **Correção proposta:** backend.

### QA-05 — Alta — histórico de operações não funcional

**Reprodução:** executar login, confirmações, conclusão, cancelamento, prontuário e evoluções no ambiente QA; consultar `audit_logs` e OpenAPI. **Esperado:** principais ações registradas com ator, horário, recurso e resultado, com leitura autorizada, conforme planejamento da Sprint. **Obtido:** `audit_logs=0` após essas operações; não há rota de leitura no OpenAPI. A tabela existe no schema (`backend/database/schema.sql:515`), sem comprovar um histórico funcional. [Evidências](additional-results.json), [OpenAPI](feature-inspection.json). **Impacto:** requisito obrigatório da Sprint sem evidência. **Correção proposta:** Paulo definir recorte de eventos/perfis; backend e frontend implementarem e testarem.

### QA-06 — Alta — dashboard sem indicadores de consultas

**Reprodução:** ler `frontend/src/App.tsx:1140-1168` no código usado no build e inspecionar o bundle servido. **Esperado:** indicadores de consultas por situação e período coerentes com a Agenda. **Obtido:** estatísticas de pacientes, perfil e equipe; nenhuma agregação de consultas alimenta o Dashboard. [Inspeção](feature-inspection.json). **Limite:** não houve teste visual. **Impacto:** destaque obrigatório da Sprint ausente. **Correção proposta:** frontend (Caio), com conferência dos números contra a Agenda em navegador.

### QA-07 — Alta — relatório de agendamentos ausente

**Reprodução:** ler as views/navegação em `frontend/src/App.tsx:51-61,971-978` e os caminhos do OpenAPI do contêiner QA. **Esperado:** consulta organizada/relatório de agendamentos e resumo conforme planejamento. **Obtido:** sem view de relatório e sem rota correspondente. [Inspeção](feature-inspection.json). **Impacto:** outra entrega obrigatória sem demonstração. **Correção proposta:** frontend (Otávio/Caio) e backend se o contrato de relatório exigir rota própria.

## 4. Decisões e limites que não são defeitos confirmados

- **D02:** `GET /patients/{id}/record` cria o prontuário após autorização; isso foi comprovado e é o contrato implementado, com o frontend chamando `recordsApi.getOrOpen`. Separar leitura e abertura é proposta ainda dependente de decisão e alteração coordenada; o GET atual não foi marcado como falha de teste.
- **D03/D04:** estados permitidos para criar/finalizar evolução, atendimento sem agendamento e conteúdo mínimo da descrição ainda exigem decisão. Não foi inventado critério de aceite para esses casos. O código aceita descrição vazia e `appointment_id:null`; isso foi registrado como comportamento atual, não aprovado clinicamente.
- **D05/D06:** identificação histórica de nome/CRO, retificação e política para paciente inativo permanecem em aberto. A inativação de **usuário** foi testada; não equivale à política de paciente inativo.
- A pesquisa de pacientes existe no código como filtro local por nome/CPF/telefone; filtros combinados da Agenda funcionaram por HTTP. O comportamento visual e o recorte acordado para pesquisa/filtro por paciente não foram comprovados. CSV não foi encontrado; como o planejamento condiciona exportação à decisão de aplicabilidade ou justificativa no PDF, a linha correspondente ficou **bloqueada por decisão**, sem supor obrigatoriedade não aprovada.
- Não havia navegador automatizável nesta sessão (`playwright` ausente e nenhum executável de navegador localizado). Login, Agenda, prontuário, permissões de botões, mensagens de erro, dashboard, relatório, pesquisa e filtros **não foram executados visualmente**. HTML `200`, bundle e build aprovados não substituem essas capturas.
- O ensaio DBA validou três bancos **descartáveis**. Não houve acesso, migração ou escrita nos volumes `lumina_execucao_20261029_postgres_data` e `lumina_s07_docker_review_20261023`; a compatibilidade com um banco real da equipe continua não verificada.

## 5. Prontidão e próximos passos

| Frente | Parecer | Condição para avançar |
| --- | --- | --- |
| Docker/integração de serviços | **Pronto no ambiente descartável testado** | Reproduzir na versão de entrega identificada; não reutilizar imagens antigas como prova. |
| API clínica | **Não pronta para aceite** | Corrigir QA-01 e QA-02; repetir concorrência, autorização, rollback e fluxos relacionados em PostgreSQL. |
| Interface | **Não pronta para aceite** | Corrigir QA-03, implementar/verificar dashboard e relatório; executar fluxo em navegador com capturas. |
| Sprint 7/aceite final | **Não pronto** | Resolver QA-01 a QA-07 conforme prioridade, alinhar a revisão local de RF-023/RN-031 com o PR, fechar decisões clínicas necessárias e registrar decisão/justificativa do CSV. |

**Recursos:** os três contêineres QA, a rede, o volume e as duas imagens criadas nesta execução foram removidos; os contêineres/volumes preexistentes permaneceram. Os contêineres e volumes temporários dos scripts PostgreSQL também foram removidos. [Registro de limpeza](cleanup-summary.log). Senhas, chaves e tokens temporários não foram escritos nos artefatos; os arquivos temporários de configuração foram apagados. Capturas visuais não existem, pois o navegador não foi executado.

Para reproduzir, usar os scripts desta pasta **somente em banco/serviços descartáveis com os nomes QA indicados e segredo de teste via variável de ambiente**. O arquivo `qa_fixture.py` recusa banco com nome diferente. `qa_http_probe.py` recusa API diferente de `127.0.0.1:18128`. Consultar [ambiente](ambiente.json), [matriz](matriz-testes.csv) e logs antes de executar; não apontar esses scripts ao banco da equipe.
