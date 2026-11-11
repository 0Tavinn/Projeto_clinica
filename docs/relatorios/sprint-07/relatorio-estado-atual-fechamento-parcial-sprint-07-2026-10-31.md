# Lumina Odonto — Sprint 7: estado atual e fechamento parcial

**Data da consolidação:** 31/10/2026. **Destinatários:** Paulo Sérgio e Cassiano Augusto, para incorporação ao PDF cumulativo. **Situação:** fechamento técnico parcial; sem aceite integral da API ou da Sprint 7.

**Base publicada examinada:** branch `chore/sprint-07-docker-integration`, HEAD local `2f7dbfe6d0d7a747f57dbeeede3a716938adc5fa` (28/10). **Estado adicional:** correções de backend e SQL para QA-01/QA-02, guias e testes estão modificados localmente, sem commit; oito documentos de requisitos e regras continuam modificados, e os relatórios de 29/10 e de QA de 31/10 são arquivos locais não rastreados. Nenhuma dessas alterações pertence ao HEAD. O QA de 31/10 executou a base `2f7dbfe`, antes das correções locais.

**Fonte e método:** relatório e [matriz de QA](../qa/2026-10-31-2f7dbfe/matriz-testes.csv), dois repasses de backend fornecidos por Paulo nesta conversa em 31/10, [relatório técnico de 29/10](relatorio-tecnico-sprint-07-2026-10-29.md), [plano da Sprint 7](../../sprint/sprint-07.md), contratos HTTP, Git local e leitura estática dos arquivos alterados. Para a origem do dashboard, foi consultada a **minuta** `Relatorio_Geral_Sprint_06.pdf`, fornecida por Paulo, páginas físicas 73–82. Esta elaboração não executou testes, build, contêineres, banco ou navegador.

## 1. Resumo para a consolidação

A Sprint 7 integrou o ambiente Docker com PostgreSQL 16 e corrigiu a inicialização da API. A branch publicada acrescentou persistência das evidências de confirmação e realização, aplicou a autorização clínica na Agenda e no prontuário, reforçou algumas operações concorrentes e documentou onze rotas clínicas/de Agenda. A interface clínica e o dashboard já vinham de etapas anteriores. Os indicadores de consultas por situação e período, o relatório administrativo e o histórico funcional exigidos no plano da Sprint 7 não foram demonstrados pelo QA.

Em **31/10**, o agente de QA executou **209 verificações na base `2f7dbfe`: 197 aprovadas, 8 reprovadas, 1 bloqueada por decisão e 3 não executadas em navegador**. Detectou, entre outros pontos, escrita clínica após perda de autorização (QA-01) e sobrescrita silenciosa de rascunho (QA-02). Paulo conduziu correções de backend após esse ensaio. A leitura estática confirma que ambas estão nos arquivos locais; o backend **informou** 82 testes SQLite aprovados com 10 exclusivos de PostgreSQL pulados, 10 testes PostgreSQL aprovados em banco 16.15 descartável e ensaio de migração de versão aprovado após ajuste do nome do banco de teste. Esses números são relato do backend, não nova execução desta elaboração nem revalidação independente do QA.

**Decisão de Paulo:** a revalidação independente de QA-01 e QA-02 fica prevista para a próxima sprint. Portanto, a classificação é **“correção implementada e testada pelo backend; revalidação independente pendente”**. A previsão não atribui compromisso confirmado a João ou outro integrante. O parecer de QA para a versão testada continua “não pronta para aceite”; o conjunto local posterior ainda não tem parecer independente.

## 2. Evolução e rastreabilidade das entregas

| Versão e origem | Entrega observada | Arquivos e limite da evidência |
| --- | --- | --- |
| `e3d9393`, 25/09; Sprint 4 | Primeira versão de dashboard comprovada nesta linha local, com dados fixos de demonstração. | `frontend/src/App.tsx` histórico; minuta cumulativa, seção 4, p. 74, Figura 29. Não comprova indicadores reais de consultas. |
| `d806382`, 26/09; Sprint 4 | Dashboard passa a usar contagem de pacientes da API, perfil e equipe. | Histórico de `frontend/src/App.tsx`; a minuta da Sprint 4 relata navegação e integração, sem constituir teste atual. |
| `34b128f`, 18/10; herança da Sprint 6 | Agenda e prontuário entram na interface recebida pela Sprint 7. | `frontend/src/App.tsx` e `frontend/src/api.ts`; contrato de conclusão ainda não atendido pela interface. |
| `ab129d7`, 21/10 | Restaura inicialização e mapeamentos da API. | `backend/app/main.py`, modelos e histórico Git; QA posterior executou importação e consulta SQL no contêiner. |
| `9b26c81`, 23/10 | Integra Compose com PostgreSQL, API e frontend. | `docker-compose.yml`, Dockerfiles e [registro Docker](../../sprint/sprint-07-docker-integration.md); QA reconstruiu imagens do HEAD em ambiente exclusivo descartável. |
| `01a0157` de 24/10 e `be7c2f2` de 26/10 | Concessão persistente e campos de confirmação/realização. | `backend/database/schema.sql`, migrações SQL e [repasse DBA](../../clinical-access-grants-handoff.md); ensaios em PostgreSQL descartável, sem migração do banco existente. |
| `ac180a7` e `ef15a63`, 26/10 | Transições da Agenda, acesso clínico, transações e bloqueios delimitados. | `backend/app/appointments/`, `backend/app/records/`; QA executou HTTP/SQL em `2f7dbfe` e revelou QA-01/QA-02 ainda presentes nessa base. |
| `2f7dbfe`, 28/10 | Guias dos contratos HTTP da Agenda e do prontuário. | `backend/app/appointments/README.md`, `backend/app/records/README.md`; texto publicado anterior ao contrato local de versão. |
| Árvore local de 31/10, **sem commit** | Correções de QA-01 e QA-02, versão da evolução, migração incremental preparada, testes e guias atualizados. | `backend/app/records/{access_repository,models,schemas,service}.py`, `backend/database/schema.sql`, migração de 31/10, testes PostgreSQL/SQLite e READMEs. Resultados informados pelo backend; sem imagem Compose ou QA independente desta árvore. |

O [relatório técnico de 29/10](relatorio-tecnico-sprint-07-2026-10-29.md) descreve o estágio anterior a QA-01/QA-02 locais. Mantê-lo como fotografia histórica evita atribuir testes ou correções de 31/10 à versão de 29/10. Os oito documentos clínicos locais refletem decisões de Paulo de 25/10, mas ainda usam trechos como “implementação pendente” que precisam ser reconciliados com o código publicado em 26/10 e com as correções locais de 31/10. Decisão de produto, código, execução e aceite permanecem estados distintos.

## 3. QA independente de 31/10: execução e defeitos

O [relatório de QA](../qa/2026-10-31-2f7dbfe/relatorio-qa-sprint07.md) identifica a branch/commit, imagens reconstruídas, PostgreSQL 16.15 exclusivo, dados fictícios, limites e limpeza dos recursos. A [matriz CSV](../qa/2026-10-31-2f7dbfe/matriz-testes.csv) foi conferida como CSV separado por ponto e vírgula: **209 linhas**, com 197 `aprovado`, 8 `reprovado`, 1 `bloqueado` e 3 `não executado`. **O executor foi o agente de QA, não João Vitor.** Os resultados não foram repetidos aqui.

| Recorte da matriz | Aprovadas | Reprovadas | Bloqueadas | Não executadas |
| --- | ---: | ---: | ---: | ---: |
| TestClient/serviço SQLite | 82 | 0 | 0 | 0 |
| API PostgreSQL versionada e ensaio de duas finalizações | 6 | 0 | 0 | 0 |
| HTTP da API/serviços QA | 99 | 1 | 0 | 0 |
| Concorrência e persistência PostgreSQL/HTTP | 3 | 3 | 0 | 0 |
| SQL e ensaio DBA descartável | 7 | 1 | 0 | 0 |
| Inspeção de código/contrato | 0 | 3 | 1 | 0 |
| Interface visual em navegador | 0 | 0 | 0 | 3 |
| **Total** | **197** | **8** | **1** | **3** |

Na rodada SQLite do QA, **82 passaram e 5 foram pulados por exigirem PostgreSQL**; os cinco foram executados separadamente. A linha PostgreSQL de seis aprovações inclui esses cinco e o ensaio adicional de duas finalizações da mesma evolução. A repetição da rodada SQLite para gerar XML não foi somada. O QA verificou fluxos HTTP, restrições por perfil/clínica, evidências de acesso, rollback e persistência no volume exclusivo após reinício e recriação sem removê-lo. **Nenhuma interação visual em navegador foi executada**; HTML, bundle e build não substituem esse teste. O ensaio SQL e o volume QA foram descartáveis, sem aplicação das migrações no banco existente da equipe.

| Defeito na base `2f7dbfe` | Reprodução resumida e impacto | Situação em 31/10 |
| --- | --- | --- |
| **QA-01 — crítica: escrita após perda de autorização** | Bloquear a evolução, iniciar edição ou finalização, cancelar a última consulta enquanto a mutação espera e liberar o bloqueio. QA obteve cancelamento `200` e mutação `200`; leitura posterior `403`. Risco de modificar conteúdo clínico sem fundamento vigente. | Correção local identificada e testes posteriores **informados pelo backend**; revalidação independente adiada. |
| **QA-02 — alta: sobrescrita de rascunho** | Duas edições da mesma versão aguardam o bloqueio; QA obteve `200/200` e somente o segundo texto permaneceu. Perda silenciosa de informação clínica. | Versionamento local identificado e testes posteriores **informados pelo backend**; revalidação independente adiada. |
| **QA-03 — alta: conclusão pela interface** | O frontend envia apenas `{status}`; a API exige `care_occurred_at` com fuso e devolveu `422` para esse corpo. Fluxo de conclusão pela interface incompatível com o contrato. | Sem ajuste local do frontend identificado; QA não clicou no navegador. |
| **QA-04 — média: limite de login** | Com `LOGIN_RATE_LIMIT=100/minute`, a sexta tentativa fictícia recebeu `429`; o código fixa cinco. Configuração operacional ignorada. | Sem correção local identificada. |
| **QA-05 — alta: histórico de operações** | Após operações reais no ambiente QA, `audit_logs=0` e não havia rota de leitura. Registro funcional exigido pelo plano ausente. | Sem correção local identificada; tabela SQL isolada não é histórico funcional. |
| **QA-06 — alta: indicadores do dashboard** | Inspeção do código e bundle mostrou pacientes/perfil/equipe, sem totalização de consultas por situação e período. Critério novo da Sprint 7 não atendido. | Dashboard anterior continua no código; melhoria da Sprint 7 sem prova de entrega. |
| **QA-07 — alta: relatório de agendamentos** | Não havia view de relatório nem rota correspondente no bundle/OpenAPI examinado. Entrega prevista no plano sem demonstração. | Sem correção local identificada. |

A **exportação CSV** ficou **bloqueada por decisão** na matriz: falta definir se será adotada ou justificar a inaplicabilidade no PDF, conforme o plano. As três linhas de navegador ficaram **não executadas**. Pesquisa local de pacientes e filtros HTTP da Agenda aparecem no código/ensaio, mas a experiência visual e o recorte acordado da Sprint não foram aceitos por esse motivo. Não se converteu proposta clínica D02–D06 em defeito sem critério aprovado.

## 4. Correções locais posteriores ao QA

### 4.1 QA-01 — autorização depois da espera

Nos arquivos locais, [access_repository.py](../../../backend/app/records/access_repository.py) seleciona e bloqueia, em ordem fixa, as consultas de origem da dupla clínica/paciente/dentista. Depois de obter o bloqueio da evolução, [service.py](../../../backend/app/records/service.py) bloqueia essas origens e chama novamente a verificação de acesso antes de editar ou finalizar. O bloqueio transacional busca impedir mudança concorrente da origem até commit ou rollback. Uma última origem cancelada deve levar a `403` sem mutação; outra confirmação ativa ou realização anterior comprovada pode sustentar a operação.

No primeiro repasse, o backend informou testes com conexões independentes e espera observada em `pg_stat_activity`: perda da última origem negada, descrição/estado preservados, outra origem permitida e regressão de edição aguardando finalização. O código e os casos adicionais em [test_clinical_pg16.py](../../../backend/tests/test_clinical_pg16.py) sustentam o desenho relatado. **Não há repetição independente de QA-01 após a alteração local.**

### 4.2 QA-02 — versão obrigatória do rascunho

A árvore local acrescenta `version INTEGER NOT NULL DEFAULT 1` e `CHECK (version >= 1)` ao [schema.sql](../../../backend/database/schema.sql) e ao modelo. O schema de entrada usa inteiro estrito positivo; o `PATCH /patients/evolutions/{id}/draft` exige a versão lida pelo cliente. Depois do bloqueio da evolução e da reconferência de acesso, o serviço compara a versão atual. Edição aceita incrementa a versão; versão antiga recebe `409` sem gravar conteúdo; versão ausente, nula, zero, negativa ou textual recebe `422`/`VALIDATION_ERROR`. A finalização continua sem corpo e incrementa a versão ao gravar `FINALIZED`. Respostas de criação/listagem/edição incluem a versão. Consulte o [guia clínico local](../../../backend/app/records/README.md).

A [migração incremental de 31/10](../../../backend/database/migrations/20261031_add_clinical_evolution_version.sql) está **preparada, não aplicada ao banco existente**. Ela se limita a PostgreSQL 16 da linhagem SQL clínica de 25/10, recusa esquema Alembic/misto e reaplicação e dá versão 1 a linhas antigas como base do novo protocolo, sem inventar o número de edições passadas. No segundo repasse, o backend informou ensaio em banco 16.15 descartável: uma primeira tentativa falhou pelo nome exigido pelo seed; após ajustar o nome do banco exclusivo, a execução passou, preservou uma evolução antiga e recusou versão zero/reaplicação. Isso não comprova backup, restauração ou migração do volume existente.

O backend informou **82 testes SQLite aprovados, 10 pulados exclusivos de PostgreSQL e 10 testes PostgreSQL 16.15 aprovados** na etapa local final, além do ensaio da migração acima. Esses totais pertencem ao repasse posterior, **não** às 209 linhas do QA anterior e **não** foram executados nesta consolidação. A evidência de backend cobre, conforme o repasse, duas edições com `200/409`, versão antiga/atual, entradas inválidas, finalização, autoria, clínica, rollback e os cenários QA-01. Logs finais dessa rodada não estão anexados a este relatório; a matriz e o parecer de QA continuam referidos à base anterior.

**Impacto de contrato:** o [frontend atual](../../../frontend/src/api.ts) ainda envia somente descrição/procedimento/notas em `recordsApi.updateDraft`; [App.tsx](../../../frontend/src/App.tsx) também não passa `version`. Se o banco for migrado e esta API local ativada sem ajustar o cliente, a edição receberá `422`. O consumidor deve conservar a versão retornada, enviá-la no PATCH e tratar `409` com recarga e decisão explícita do usuário antes de reenviar. **Nenhuma adaptação de frontend foi encontrada.** Além disso, o [README da Agenda local](../../../backend/app/appointments/README.md) ainda diz que QA-02 não tem controle de versão, enquanto o guia clínico e o código local já o descrevem; a divergência documental precisa de correção em etapa própria.

## 5. Origem e limite do dashboard

Paulo informou que o dashboard existia antes da Sprint 7. O **primeiro commit comprovado nesta linha do histórico local** é `e3d9393` de **25/09/2026**, com componente `Dashboard` em `frontend/src/App.tsx`. Esse primeiro código exibia valores de demonstração fixos, como “Consultas hoje”, “Total de pacientes” e “Prontuários atualizados”, além de próximas consultas fictícias; não há prova de que esses números fossem agregados do banco. O commit `d806382`, de **26/09/2026**, passou a apresentar a contagem de pacientes carregados da API, perfil autenticado e equipe. Não se afirma que `e3d9393` seja a primeira versão absoluta fora do histórico disponível.

A minuta `Relatorio_Geral_Sprint_06.pdf` fornecida por Paulo situa o dashboard na **Sprint 4**: seção 4 na página física 73, **Figura 29 — Dashboard após autenticação do administrador** na página física 74, relato de navegação na página 81 e situação do produto na página 82. É fonte documental histórica, não revalidação atual da figura. O [plano da Sprint 4](../../sprint/sprint-04.md) também previa a tela. A versão atual em [App.tsx](../../../frontend/src/App.tsx) mostra pacientes ativos, perfil e equipe. O [plano da Sprint 7](../../sprint/sprint-07.md) exigiu a **melhoria** de indicadores de consultas por situação e período, coerentes com a Agenda; o QA marcou esse critério como QA-06. Para o cumulativo, Cassiano deve apresentar **dashboard existente desde a Sprint 4** e **melhoria da Sprint 7 ainda pendente de comprovação**, sem dizer que o módulo nasceu nesta sprint.

## 6. Estado atual por frente

| Entrega ou defeito | Evidência e versão | Situação atual | Limitação | Próxima ação |
| --- | --- | --- | --- | --- |
| Docker com PostgreSQL | `9b26c81`; QA em `2f7dbfe` | Serviços, health, API e persistência básica passaram em ambiente descartável. | Não comprova imagem com correções locais nem banco da equipe. | Reconstruir versão identificada para revalidação futura. |
| Inicialização/mapeamento da API | `ab129d7`; QA `2f7dbfe` | Importação e consulta real do contêiner passaram no QA. | Sem aceite da API clínica completa. | Preservar regressão na nova versão. |
| Agenda, evidências e leitura clínica | `be7c2f2`, `ac180a7`, `ef15a63`; QA `2f7dbfe` | Fluxos HTTP principais e isolamento passaram; QA-01/QA-02 falharam nessa versão. | Banco persistente e decisões D02–D06 não fechados. | Revalidar código local com QA e fechar decisões necessárias. |
| QA-01 e QA-02 | Código local sem commit; dois repasses do backend | Correções implementadas e testadas segundo backend. | Sem revisão independente posterior; logs finais não anexados; sem imagem Compose. | Incluir em versão identificada e reexecutar cenários no próximo ciclo. |
| Migração `version` | SQL local e repasse do backend | Preparada e ensaiada em banco descartável segundo backend. | Não aplicada nem restaurada em banco existente; Alembic/misto exige desenho. | DBA inventariar destino, backup/restauração e plano autorizado. |
| QA-03 e consumidor de `version` | QA `2f7dbfe`; `frontend/src/api.ts`, `App.tsx` atuais | Conclusão ainda sem horário com fuso; edição de rascunho ainda sem versão. | Contratos incompatíveis após ativação do backend local. | Frontend alinhar payloads e testar no navegador. |
| Dashboard e QA-06 | `e3d9393`, `d806382`; QA `2f7dbfe` | Dashboard antigo presente; indicadores novos ausentes. | Não houve teste visual no QA. | Implementar agregações e comparar com a Agenda. |
| Relatório e histórico, QA-05/QA-07 | Matriz QA `2f7dbfe` | Relatório sem view/rota; `audit_logs=0` no ensaio. | Tabela existente não comprova função. | Definir escopo, implementar e validar com dados fictícios. |
| QA-04, CSV e interface visual | Matriz QA `2f7dbfe` | Limite de login ignorou configuração; CSV bloqueado por decisão; 3 casos sem navegador. | Sem correções ou aceite visual comprovados. | Corrigir limite; decidir CSV; executar cenários visuais. |
| Requisitos e regras locais | Oito arquivos modificados sem commit | Política de Paulo de 25/10 registrada localmente. | Resumos de “implementação pendente” conflitam com entregas técnicas posteriores. | Reconciliar textos com versão e evidência, sem aprovar propostas por extensão. |

## 7. Pendências objetivas para a próxima sprint

1. **QA independente:** repetir QA-01 e QA-02 na mesma versão resultante, em PostgreSQL 16 isolado, com espera real, perda de origem, `403`, `200/409`, estado persistido, outra origem válida, autoria, clínica e rollback. A revisão está **prevista**, sem compromisso individual confirmado.
2. **Versão de entrega:** criar uma referência verificável quando autorizado, reconstruir API/Compose e associar logs, imagens e banco à mesma árvore. Não usar o HEAD antigo como prova das correções locais.
3. **Banco existente:** inventariar a linhagem, preparar backup protegido e restauração de ensaio, avaliar Alembic/misturas e então decidir a aplicação das migrações. Manter dados clínicos reais fora das evidências.
4. **Frontend:** alinhar conclusão com `care_occurred_at` com fuso e edição de rascunho com `version`; tratar `403/409/422`, estados e perfis; executar o fluxo em navegador.
5. **Entregas da Sprint 7:** demonstrar indicadores de consultas no dashboard, relatório de agendamentos, histórico funcional, pesquisa/filtros no recorte aprovado e decidir/justificar CSV.
6. **Defeitos e decisões restantes:** tratar QA-04; fechar D02–D06 somente nos pontos necessários, sem supor aprovação de abertura, conteúdo mínimo, retificação, paciente inativo ou IA; alinhar os catálogos e o README da Agenda com o código efetivamente incorporado.
7. **Consolidação acadêmica:** Cassiano inserir esta fotografia após o capítulo da Sprint 6, revisar numeração de figuras e referências e obter evidências visuais, resultados independentes e arquivo editável do cumulativo antes de fechar o PDF. A minuta de Sprints 1–6 fornecida é fonte histórica, não comprova aceite atual. Sua capa lista cinco integrantes e omite Caio Cesar, que consta no [README do projeto](../../../README.md); a identificação da equipe deve ser conferida.

## 8. Fontes e limites de uso

| Fonte | Uso neste relatório | Limite |
| --- | --- | --- |
| [Relatório de QA de 31/10](../qa/2026-10-31-2f7dbfe/relatorio-qa-sprint07.md), [matriz](../qa/2026-10-31-2f7dbfe/matriz-testes.csv) e logs da mesma pasta | Contagem, versão testada, reproduções e parecer. | Executados antes das correções locais; agente de QA, não João. |
| Dois repasses de backend fornecidos por Paulo nesta conversa, 31/10 | Desenho das correções e resultados posteriores informados. | Relato do executor; logs finais e revisão independente ainda não anexados. |
| [Relatório técnico de 29/10](relatorio-tecnico-sprint-07-2026-10-29.md), [plano](../../sprint/sprint-07.md), [guia da Agenda](../../../backend/app/appointments/README.md) e [guia clínico](../../../backend/app/records/README.md) | Histórico, metas e contratos. | Plano não é entrega; guias locais posteriores não integram o HEAD. |
| Git local, `frontend/src/App.tsx`, `frontend/src/api.ts`, código/SQL/testes locais de records | Primeira versão rastreável do dashboard e implementação presente na árvore. | Leitura estática; código modificado sem commit não é versão executada. |
| `Relatorio_Geral_Sprint_06.pdf`, minuta entregue por Paulo, páginas físicas 73–82 | Referência histórica da Sprint 4 e Figura 29. | O arquivo não foi alterado nem revisado como relatório final; o editável cumulativo não foi fornecido. |

**Conclusão:** há uma base clínica publicada que funcionou em vários ensaios de QA, mas o próprio QA encontrou oito reprovações e não recomendou aceite da Sprint 7. As duas falhas de concorrência receberam correções locais posteriores, descritas e testadas pelo backend; **permanecem abertas para revalidação independente**. A interface, as entregas administrativas e a migração do banco existente ainda exigem trabalho e evidências. Este documento registra **fechamento parcial**, sem declarar conclusão integral da API ou da Sprint 7.
