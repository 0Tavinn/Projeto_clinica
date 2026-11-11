# Repasse técnico da API clínica — Sprint 7

**Base examinada:** `chore/sprint-07-docker-integration`, HEAD `ac180a7ddbec9f8a5db55c75c82110fa4f5fb3f9`, com alterações locais posteriores neste repasse. O prefixo configurado é `/api/v1`; `/health` fica fora dele. Este documento descreve o contrato técnico atual, sem declarar aprovadas as decisões clínicas pendentes.

## Contrato HTTP observado

| Método e caminho | Comportamento atual |
| --- | --- |
| `PATCH /api/v1/appointments/{id}/status` | `CONFIRMED` registra a confirmação; `COMPLETED` exige `care_occurred_at` com fuso horário e grava situação e evidência de atendimento na mesma transação. |
| `PATCH /api/v1/appointments/{id}` | A mudança de situação segue a mesma regra, inclusive o campo `care_occurred_at` para `COMPLETED`. |
| `GET /api/v1/patients/{id}/record` | Exige dentista elegível e vínculo válido; cria o prontuário se ainda não existir. Esse efeito de escrita permanece sujeito à decisão D02. A resposta inclui `general_notes`, portanto a autorização ocorre antes da leitura. |
| `GET /api/v1/patients/{id}/evolutions` | Exige o mesmo acesso; lista finalizadas e somente os rascunhos do próprio dentista. Responde 404 se o prontuário não existe. |
| `POST /api/v1/patients/evolutions` | Cria rascunho com autoria obtida da sessão. Quando há `appointment_id`, confere clínica, paciente e dentista responsável e preserva uma evolução por consulta. A abertura do prontuário e o rascunho são atômicos. |
| `PATCH /api/v1/patients/evolutions/{id}/draft` | Exige acesso vigente e autoria; bloqueia a linha antes da edição. |
| `POST /api/v1/patients/evolutions/{id}/finalize` | Exige acesso vigente e autoria; bloqueia a linha, registra `FINALIZED` e `finalized_at`. Não conclui a consulta. |

Exemplo de conclusão da consulta pelo dentista responsável, após confirmação confiável:

```json
{"status":"COMPLETED","care_occurred_at":"2026-10-26T14:30:00-03:00"}
```

As falhas usam `{"error":{"code":"...","message":"...","details":null}}`. Acesso negado responde 403; recurso ou consulta vinculada inexistente responde 404; duplicidade de evolução por consulta responde 409; transição inválida ou horário ausente/sem fuso responde 422. Valores clínicos inválidos não são reproduzidos na resposta de validação nem no log de erro. Não há rota comum de exclusão de evolução finalizada.

## Limites de regra clínica

- **D02:** o `GET` acima ainda abre prontuário. A decisão sobre novo contrato e sua migração no frontend segue pendente.
- **D03/D04:** a leitura permitida não aprova, por si só, criação ou finalização de evolução. Os estados da consulta que permitem essas escritas, atendimento sem agendamento e conteúdo mínimo ainda precisam de aprovação. O comportamento de escrita atual é herdado da API e requer revisão após essa decisão.
- **D05:** a resposta exibe nome e CRO atuais do cadastro profissional; preservação histórica, retificação e tratamento do legado ainda não foram definidos.
- **D06:** a regra para paciente inativo segue pendente. Usuário, clínica, perfil profissional e origem assistencial são verificados em cada requisição.
- A FK composta da evidência restringe troca de participantes de consulta. O backend traduz a falha conhecida em 409; correção controlada e concessões retroativas aguardam decisão.

## Verificação executada nesta etapa

- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 ENVIRONMENT=test DATABASE_URL=sqlite:///:memory: .venv/bin/python -m pytest -q -p no:cacheprovider --disable-warnings --tb=short` em `backend/`: **82 passaram, 5 pulados** (ensaios PostgreSQL), 12 avisos. SQLite não comprova restrições específicas do PostgreSQL.
- Uma verificação isolada com `TestClient` confirmou `import app.main`, `configure_mappers()`, `GET /health` com 200 e as rotas clínicas e o campo `care_occurred_at` no OpenAPI.
- `bash tests/run_clinical_pg16.sh` em `backend/`: PostgreSQL **16.15** em contêiner e volume exclusivos, inicializados por `backend/database/schema.sql`: **5 passaram**, 8 avisos. Cobriu fluxo HTTP com reinício da API e persistência, confirmação/conclusão concorrentes, bloqueio contra edição após finalização, cancelamento enquanto a criação aguardava bloqueio e rollback da abertura quando o rascunho falhou. O script remove somente os recursos que criou.
- `git diff --check`, `bash -n backend/tests/run_clinical_pg16.sh` e análise sintática dos quatro arquivos Python alterados: sem falhas.

Nenhuma migração foi executada no PostgreSQL existente; o volume `lumina_s07_docker_review_20261023` não foi usado. `/health` prova inicialização, não substitui os ensaios clínicos e de persistência acima.

## Repasse por responsável

- **Caio:** `frontend/src/api.ts` ainda envia apenas `{status}` em `appointmentsApi.updateStatus`; para `COMPLETED`, incluir `care_occurred_at` com fuso e ajustar a interface para coleta/validação do horário. `recordsApi.getOrOpen` chama o `GET` que cria prontuário; aguardar D02 antes de mudar esse fluxo. Apresentar o envelope de erro sem expor texto clínico.
- **Otávio/Tech Lead e Paulo:** fechar D02–D06, sobretudo condições de escrita de rascunho/finalização, atendimento avulso e conteúdo mínimo. Só então validar a política clínica de escrita e o contrato definitivo para o frontend.
- **João:** revisar os ensaios HTTP, perfis, clínica, autoria, concorrência e privacidade; acrescentar casos de escrita quando D03/D04 forem aprovadas. Os testes técnicos atuais não atestam essas regras futuras.
- **DBA:** manter uma estratégia única para bancos existentes, revisar o contrato ORM/SQL e executar a migração preparada apenas em ambiente autorizado. O ensaio desta etapa partiu de esquema limpo e descartável; não comprova migração de banco com dados reais.
