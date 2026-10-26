# Autorização clínica persistente — preparo e ensaio SQL

> **Atualização de 25/10/2026:** a entrega descrita abaixo foi publicada no
> commit `01a01573a42b09bcfb3c337561817693554e0459`. As afirmações de
> permanência por confirmação, os comandos e a indicação “sem commit” abaixo
> registram o ensaio **histórico de 24/10**, antes da revisão aprovada em
> RN-031/RF-023. A política e os ensaios atuais estão na seção de 25/10 ao fim
> deste documento. Os scripts de 24/10 não constituem aceite da nova política.

**Data:** 24/10/2026. **Branch:** `chore/sprint-07-docker-integration`.
**Base inicial:** `698a3bd4d8d20af7efa828d7f78589e4ec4b7a5e`.
**Estado:** proposta ensaiada em PostgreSQL 16 descartável; não aplicada ao
volume `lumina_s07_docker_review_20261023`. Sem commit ou publicação.

Para viabilizar o ensaio, o Docker Desktop foi iniciado. Nesse início, os
contêineres preexistentes de API e frontend da revisão subiram automaticamente;
o contêiner de banco da revisão ficou `Exited (127)`. Nenhum comando de teste,
DDL ou migração foi dirigido a esses contêineres ou ao volume da revisão.
Eles foram deixados no estado observado após a inicialização do Docker.

## Arquivos desta entrega

| Arquivo | Finalidade |
| --- | --- |
| `backend/database/schema.sql` | Provisiona banco novo com chave composta da Agenda, tabela de concessões e índice de busca. |
| `backend/database/migrations/20261024_add_clinical_access_grants.sql` | Atualização incremental explícita da origem `schema.sql` anterior. Não reexecutável. |
| `backend/database/checks/20261024_clinical_access_seed.sql` | Dados inteiramente fictícios, inclusive prontuário e evolução anteriores. |
| `backend/database/checks/20261024_clinical_access_exercise.sql` | Ensaio de restrições e permanência após mudanças de estado. |
| `backend/database/checks/20261024_clinical_access_verify.sql` | Verificação somente de leitura depois do reinício. |

`clinical_access_grants` possui uma linha por consulta de origem: `appointment_id`
é PK; `clinic_id`, `patient_id`, `dentist_id` e `granted_at` são obrigatórios.
Um paciente e dentista podem ter várias concessões de consultas diferentes.
A FK composta exige correspondência com a consulta, impede sua exclusão e
bloqueia troca de participantes depois da concessão. O índice
`(clinic_id, dentist_id, patient_id)` atende à verificação de leitura. Não há
FK para `medical_records`: a autorização pode surgir antes do prontuário.

**Limite de integridade:** a FK não prova que a consulta passou por confirmação
autorizada, nem que paciente e dentista de `appointments` pertencem à clínica
indicada. O backend deve validar isso na operação autorizada, bloquear a linha
da consulta e gravar estado e concessão na mesma transação. Deve ainda conferir
usuário ativo, perfil profissional, clínica e concessão em toda leitura. Um
writer SQL externo à operação da Agenda pode violar a regra de concessão;
restringir esse caminho ou projetar controle no banco antes de liberá-lo.
Rascunhos continuam visíveis só ao autor. A API atual **não** grava nem consulta
esta tabela; os ensaios abaixo são estruturais SQL, não testes HTTP ou aceite
funcional da API.

## Compatibilidade e pré-condições da migração

Suporta **somente** PostgreSQL 16 com o `schema.sql` completo anterior a esta
entrega, ainda sem `clinical_access_grants` nem `alembic_version`, após
comparação do catálogo do destino. O script exige oito tabelas, estruturas
centrais da Agenda e do prontuário, `btree_gist`, gatilho de período ativo e
ausência de consultas com clínicas divergentes dos participantes. Em
divergência detectada, encerra com erro e rollback. O preflight automático
verifica itens críticos, mas não comprova equivalência integral de colunas,
permissões, funções, gatilhos ou histórico; essa comparação é pré-condição
manual. Bancos da linha Alembic antiga, mistos, parcialmente migrados ou já
atualizados requerem plano próprio. A migração SQL de 30/09, isolada, não cria
o esquema clínico completo. Não fazer `stamp` para forçar equivalência.

O script toma `ACCESS EXCLUSIVE` em `appointments` para criar a chave `UNIQUE`
e bloqueios de leitura contra escrita em `patients`, `dentists` e `users`
durante a checagem de coerência. O `lock_timeout` é 5 segundos; medir duração
e escolher janela de manutenção no destino. Nenhuma autorização antiga é
preenchida: estado atual, autoria e agendamento não comprovam confirmação.
O bloqueio definitivo de mudança dos participantes após concessão ainda
depende de aprovação de Paulo; esta definição está preparada para revisão e
ensaio, não para aplicação automática.

## Reprodução dos dois ensaios

Executar a partir da raiz do repositório, com Docker disponível. Confirmar
antes que os quatro nomes exclusivos abaixo ainda não existam. São dois
contêineres sem rede publicada e dois volumes próprios, todos descartáveis.
Não usar Compose nem o volume de revisão.

```bash
git show 698a3bd4d8d20af7efa828d7f78589e4ec4b7a5e:backend/database/schema.sql > /tmp/lumina_acl_old_schema_20261024.sql
docker volume create lumina_acl_new_20261024
docker volume create lumina_acl_upgrade_20261024
docker run -d --name lumina_acl_new_20261024 --network none \
  --mount type=volume,src=lumina_acl_new_20261024,dst=/var/lib/postgresql/data \
  --mount type=bind,src="$PWD/backend/database/schema.sql",dst=/docker-entrypoint-initdb.d/001-schema.sql,readonly \
  -e POSTGRES_DB=lumina_acl_new_20261024 -e POSTGRES_USER=clinic_app \
  -e POSTGRES_PASSWORD=scratch-only-not-secret postgres:16-alpine
docker run -d --name lumina_acl_upgrade_20261024 --network none \
  --mount type=volume,src=lumina_acl_upgrade_20261024,dst=/var/lib/postgresql/data \
  --mount type=bind,src=/tmp/lumina_acl_old_schema_20261024.sql,dst=/docker-entrypoint-initdb.d/001-schema.sql,readonly \
  -e POSTGRES_DB=lumina_acl_upgrade_20261024 -e POSTGRES_USER=clinic_app \
  -e POSTGRES_PASSWORD=scratch-only-not-secret postgres:16-alpine
```

Confirmar `pg_isready` em ambos e executar com `ON_ERROR_STOP=1`:

```bash
docker exec lumina_acl_new_20261024 pg_isready -U clinic_app -d lumina_acl_new_20261024
docker exec lumina_acl_upgrade_20261024 pg_isready -U clinic_app -d lumina_acl_upgrade_20261024
docker exec -i lumina_acl_new_20261024 psql -X -v ON_ERROR_STOP=1 -U clinic_app -d lumina_acl_new_20261024 < backend/database/checks/20261024_clinical_access_seed.sql
docker exec -i lumina_acl_upgrade_20261024 psql -X -v ON_ERROR_STOP=1 -U clinic_app -d lumina_acl_upgrade_20261024 < backend/database/checks/20261024_clinical_access_seed.sql
docker exec -i lumina_acl_upgrade_20261024 psql -X -v ON_ERROR_STOP=1 -U clinic_app -d lumina_acl_upgrade_20261024 < backend/database/migrations/20261024_add_clinical_access_grants.sql
docker exec -i lumina_acl_new_20261024 psql -X -v ON_ERROR_STOP=1 -U clinic_app -d lumina_acl_new_20261024 < backend/database/checks/20261024_clinical_access_exercise.sql
docker exec -i lumina_acl_upgrade_20261024 psql -X -v ON_ERROR_STOP=1 -U clinic_app -d lumina_acl_upgrade_20261024 < backend/database/checks/20261024_clinical_access_exercise.sql
docker restart lumina_acl_new_20261024 lumina_acl_upgrade_20261024
docker exec -i lumina_acl_new_20261024 psql -X -v ON_ERROR_STOP=1 -U clinic_app -d lumina_acl_new_20261024 < backend/database/checks/20261024_clinical_access_verify.sql
docker exec -i lumina_acl_upgrade_20261024 psql -X -v ON_ERROR_STOP=1 -U clinic_app -d lumina_acl_upgrade_20261024 < backend/database/checks/20261024_clinical_access_verify.sql
```

Checagens adicionais feitas **somente** nos destinos descartáveis:

```bash
# Reaplicação: saída 3 é esperada; a tabela já existe.
docker exec -i lumina_acl_new_20261024 psql -X -v ON_ERROR_STOP=1 -U clinic_app -d lumina_acl_new_20261024 < backend/database/migrations/20261024_add_clinical_access_grants.sql

# Origem divergente: saída 3 é esperada, sem objetos parciais.
docker exec lumina_acl_upgrade_20261024 createdb -U clinic_app lumina_acl_divergent_20261024
docker exec -i lumina_acl_upgrade_20261024 psql -X -v ON_ERROR_STOP=1 -U clinic_app -d lumina_acl_divergent_20261024 < /tmp/lumina_acl_old_schema_20261024.sql
docker exec lumina_acl_upgrade_20261024 psql -X -v ON_ERROR_STOP=1 -U clinic_app -d lumina_acl_divergent_20261024 -c 'DROP TRIGGER trg_appointments_set_period ON appointments'
docker exec -i lumina_acl_upgrade_20261024 psql -X -v ON_ERROR_STOP=1 -U clinic_app -d lumina_acl_divergent_20261024 < backend/database/migrations/20261024_add_clinical_access_grants.sql
```

Disputa concorrente reproduzível no banco `new` (esperar um código `0` e um
`3`, este com violação de `pk_clinical_access_grants`):

```bash
docker exec lumina_acl_new_20261024 psql -X -v ON_ERROR_STOP=1 -U clinic_app -d lumina_acl_new_20261024 -c "INSERT INTO appointments (clinic_id,patient_id,dentist_id,scheduled_at,duration_minutes,status,notes) SELECT clinic_id,patient_id,dentist_id,TIMESTAMPTZ '2026-11-04 09:00:00+00',30,'CONFIRMED','Consulta fictícia concorrente' FROM appointments WHERE notes='Consulta fictícia A'"
grant_sql="INSERT INTO clinical_access_grants (appointment_id,clinic_id,patient_id,dentist_id) SELECT id,clinic_id,patient_id,dentist_id FROM appointments WHERE notes='Consulta fictícia concorrente'"
docker exec lumina_acl_new_20261024 psql -X -v ON_ERROR_STOP=1 -U clinic_app -d lumina_acl_new_20261024 -c "BEGIN; $grant_sql; SELECT pg_sleep(1); COMMIT;" > /tmp/lumina_acl_a.log 2>&1 & first_pid=$!
sleep 0.15
docker exec lumina_acl_new_20261024 psql -X -v ON_ERROR_STOP=1 -U clinic_app -d lumina_acl_new_20261024 -c "$grant_sql" > /tmp/lumina_acl_b.log 2>&1 & second_pid=$!
wait "$first_pid"; echo "primeiro: $?"
wait "$second_pid"; echo "segundo: $?"
docker exec lumina_acl_new_20261024 psql -X -U clinic_app -d lumina_acl_new_20261024 -Atqc "SELECT count(*) FROM clinical_access_grants WHERE appointment_id=(SELECT id FROM appointments WHERE notes='Consulta fictícia concorrente')"
docker exec lumina_acl_new_20261024 psql -X -v ON_ERROR_STOP=1 -U clinic_app -d lumina_acl_new_20261024 -c "BEGIN; DELETE FROM clinical_access_grants WHERE appointment_id=(SELECT id FROM appointments WHERE notes='Consulta fictícia concorrente'); DELETE FROM appointments WHERE notes='Consulta fictícia concorrente'; COMMIT;"
```

Após conferir os resultados, remover **somente** esses recursos de ensaio:

```bash
docker rm -f lumina_acl_new_20261024 lumina_acl_upgrade_20261024
docker volume rm lumina_acl_new_20261024 lumina_acl_upgrade_20261024
```

## Resultados observados

- PostgreSQL 16.15: provisionamento novo e migração sobre esquema anterior com
  dados fictícios concluíram com código 0. A migração deixou concessões vazias
  até o ensaio explicitamente inseri-las.
- Nos dois bancos, a PK recusou segunda concessão para a mesma consulta; duas
  consultas para a mesma dupla paciente–dentista foram aceitas. A FK recusou
  paciente ou dentista divergente da consulta de origem e impediu trocar esses
  participantes depois da concessão.
- A concessão existiu sem prontuário para o paciente A; três concessões
  persistiram depois de alterar consultas para `COMPLETED`, `CANCELED` e
  `NO_SHOW`. O prontuário e evolução fictícios anteriores para o paciente B
  permaneceram inalterados.
- Depois de reiniciar os dois contêineres, a verificação de leitura passou:
  1 clínica, 2 usuários, 2 dentistas, 2 pacientes, 3 consultas, 1 prontuário,
  1 evolução e 3 concessões em cada banco.
- Duas inserções simultâneas para uma quarta consulta descartável produziram
  uma concessão e um conflito na PK. O dado temporário foi removido. A
  migração foi ainda recusada ao tentar reaplicá-la no banco já atualizado
  (código `3`, sem alterar as 3 concessões).
- Uma cópia descartável do esquema anterior sem o gatilho de período também
  recusou a migração (código `3`); não restaram tabela ou chave parcial.
- Dumps de esquema de `appointments` e `clinical_access_grants` dos dois
  caminhos ficaram idênticos após remover apenas os tokens aleatórios
  `\\restrict`/`\\unrestrict` gerados pelo `pg_dump`.

## Antes de qualquer aplicação em banco existente

Identificar explicitamente host, banco, volume e origem do esquema; fazer
inventário de catálogo e contagens sem expor dados clínicos; resolver
divergências. Criar backup consistente (`pg_dump -Fc`) em local protegido e
capturar separadamente papéis/permissões se necessários. **Restaurar em outro
PostgreSQL 16 autorizado** e comparar contagens, constraints, índices,
gatilhos e leitura pela API antes de chamar recuperação de validada. Ensaiar
esta migração nessa restauração; medir locks e ter janela definida. Antes do
`COMMIT`, falha reverte a transação; após o `COMMIT`, não apagar concessões nem
restaurar por cima de escritas novas sem plano de reconciliação. Backup e
restauração do banco real não foram executados nesta etapa.

## Repasse ao backend e decisões pendentes

Centralizar todas as transições para `CONFIRMED` em uma operação autorizada que
bloqueie a consulta (`FOR UPDATE`), valide clínica/paciente/dentista, grave a
concessão e dê **um commit**. A rota de mudança de estado e o PATCH genérico
da Agenda devem seguir esse mesmo contrato; commits internos do repositório
atual precisam ser removidos ou contidos. Repetição e concorrência não podem
emitir nova concessão. A leitura clínica deve exigir a concessão persistida,
usuário ativo e perfil profissional elegível, retornando finalizadas de todos
os autores e só rascunhos do autor. Não exigir prontuário existente no momento
de confirmar e não inferir acesso pelo estado atual da consulta.

Paulo ainda precisa aprovar o bloqueio definitivo de troca de participantes
após concessão e definir correção excepcional de confirmação incorreta.
Tratamento de consultas antigas sem prova de confirmação, D02 (abertura),
D03 (estados de escrita e atendimento avulso) e D06 (paciente inativo)
continuam pendentes. Não há revogação administrativa nesta entrega.

## Atualização de 25/10 — preparação e continuidade

**Base publicada:** `01a01573a42b09bcfb3c337561817693554e0459`.
**Estado do ensaio de 25/10:** SQL preparado e ensaiado em PostgreSQL 16
descartável, sem aplicação no volume `lumina_s07_docker_review_20261023`.
Este relatório registra os testes SQL daquela data; alterações posteriores
da API exigem validação própria. As oito edições documentais locais de Paulo
em 25/10 foram preservadas.

Arquivos novos desta atualização:

| Arquivo | Uso |
| --- | --- |
| `backend/database/migrations/20261025_add_clinical_access_evidence.sql` | Acrescenta procedência e realização à estrutura publicada em 24/10. |
| `backend/database/checks/20261025_clinical_access_seed.sql` | Insere somente dados fictícios, inclusive concessão antiga sem responsável comprovado. |
| `backend/database/checks/20261025_clinical_access_exercise.sql` | Exercita restrições e consulta de elegibilidade de leitura. |
| `backend/database/checks/20261025_clinical_access_verify.sql` | Confere persistência após reinício, somente por leitura. |
| `backend/database/checks/run_20261025_clinical_access_pg16.sh` | Reproduz os três caminhos em recursos exclusivos e remove apenas os que criou. |

`backend/database/schema.sql` foi atualizado para bancos novos. A migração
publicada `20261024_add_clinical_access_grants.sql` **não foi modificada**.

### Campos, restrições e semântica

A PK por `appointment_id`, os participantes e o índice de busca permanecem.
`granted_at` registra o instante da concessão. `confirmed_by_user_id` aponta
para `users.id`, sem exigir que esse usuário continue ativo ou com o mesmo
perfil depois: sua identidade histórica não é a elegibilidade atual do
dentista leitor. O atendimento usa `care_occurred_at` (horário informado),
`care_recorded_at` (instante do registro) e `care_recorded_by_user_id` (ator do
registro). As duas referências de ator têm FK `ON UPDATE/DELETE RESTRICT`.

O `CHECK ck_clinical_access_grants_care_complete` exige os três campos de
realização juntos e exige `confirmed_by_user_id` não nulo quando há realização.
Os quatro campos novos são anuláveis para preservar linhas existentes. Assim,
uma linha antiga sem `confirmed_by_user_id`, ainda que sua consulta esteja
`CONFIRMED` ou `COMPLETED`, **não constitui confirmação confiável** e não
sustenta autorização pela consulta proposta. A migração não preenche atores
nem atendimentos antigos. Conferência de procedência e eventual tratamento de
legado precisam de decisão e evidência explícitas; não usar estado atual,
autoria de evolução ou horário agendado como substitutos.

FKs e `CHECK` protegem identidade referenciada, origem e completude dos campos.
**Não provam** quem estava autenticado, que o ator tinha permissão, que ocorreu
atendimento, que a clínica do ator correspondia, nem que `COMPLETED` foi
gravado junto da realização. Writers fora das operações autorizadas precisam
ser restringidos. A FK composta anterior continua bloqueando troca dos
participantes após concessão; a regra definitiva e a correção excepcional
seguem pendentes de Paulo.

### Compatibilidade e aplicação futura

1. **Banco novo e vazio:** usar somente `backend/database/schema.sql` atual.
2. **Banco com esquema completo anterior à entrega de 24/10:** após inventário
   do catálogo, aplicar a migração publicada de 24/10 e, depois, a migração de
   25/10. Não executar `schema.sql` sobre esse banco.
3. **Banco que já tem a estrutura publicada de 24/10:** após inventário, aplicar
   somente a migração de 25/10. Ela recusa reaplicação e estrutura ausente.

Esses caminhos exigem PostgreSQL 16 e a linhagem `schema.sql` completa,
confirmada no catálogo. O preflight automático verifica pontos críticos, mas
não comprova equivalência integral do banco, permissões ou histórico. Esquema
Alembic antigo, misto ou divergente requer reconciliação própria; não usar
`stamp` para simular equivalência. A migração nova toma `ACCESS EXCLUSIVE` em
`clinical_access_grants`, com `lock_timeout` de 5 segundos e transação única.
Medir locks e duração em restauração do destino antes de marcar janela.

Antes de qualquer aplicação em banco existente, identificar host, banco e
volume; fazer `pg_dump -Fc` em local protegido, preservar papéis/permissões
necessários e **restaurar em outro PostgreSQL 16 autorizado**. Comparar catálogo,
contagens e comportamento de leitura na restauração; só esse ensaio efetivo
valida recuperação. Depois do commit, não restaurar por cima de novas escritas
sem plano de reconciliação. Nada foi aplicado ao volume da revisão.

### Contrato para o backend

- **Confirmação:** bloquear a consulta (`FOR UPDATE`), validar ator autorizado,
  paciente, dentista e clínica; gravar `CONFIRMED` e uma concessão com
  `confirmed_by_user_id` e `granted_at` na **mesma transação**. A consulta pode
  ainda não ter prontuário. Repetição/concorrência não podem criar segunda
  concessão nem sobrescrever sua procedência.
- **Concluir atendimento:** somente o dentista responsável e elegível, a partir
  de `CONFIRMED` com concessão confiável; bloquear a mesma consulta e concessão,
  validar participantes e horário informado, gravar `COMPLETED` e os três campos
  `care_*` em **um commit**. Administrador e recepção não concluem. PATCH
  genérico e rota específica precisam passar pelo mesmo serviço; `SCHEDULED`
  para `COMPLETED` fica vedado. Falha parcial exige rollback. Concluir consulta
  não finaliza a evolução clínica.
- **Cancelamento/ausência e leitura:** não apagar concessões. Em cada leitura,
  verificar usuário leitor ativo, perfil/cadastro profissional elegível e
  clínica; buscar **qualquer** concessão confiável da dupla na clínica cuja
  consulta esteja atualmente `CONFIRMED`, ou cuja consulta esteja `COMPLETED`
  com realização completa e válida. A situação atual do confirmador histórico
  não entra nessa verificação. Outra origem válida mantém acesso. Retornar
  finalizadas de todos os autores e apenas rascunhos do próprio autor.

O banco não impõe, por FK/CHECK, a transição de estado nem a validade
assistencial da realização. Na data deste ensaio SQL, a API ainda não havia
sido adaptada; os testes abaixo **não são testes da API**. D02, correções
indevidas, troca de participantes, paciente inativo, estados de escrita,
atendimento avulso, nome/CRO histórico e revogação administrativa permanecem
fora desta entrega.

### Reprodução e resultados novos

Da raiz do repositório, com Docker acessível e imagem `postgres:16-alpine`:

```bash
bash backend/database/checks/run_20261025_clinical_access_pg16.sh
```

O script extrai os `schema.sql` dos commits `698a3bd4...` e `01a01573...` em
`/tmp`, cria três contêineres e volumes com nomes `lumina_acl25_*_<sufixo>` e
sem porta ou rede publicada, executa `psql -X -v ON_ERROR_STOP=1`, reinicia
somente esses contêineres, verifica os dados e remove somente os recursos que
criou. Os bancos internos são `lumina_acl25_new`, `lumina_acl25_upgrade` e
`lumina_acl25_base`. Não usa Compose, banco real ou volume da revisão.

**Execução efetiva em 25/10/2026, PostgreSQL 16.15:**

- `new`: `schema.sql` atual, seed, exercício e verificação após reinício
  passaram.
- `upgrade`: schema publicado em `01a01573...`, seed anterior à migração nova,
  migração, exercício e verificação após reinício passaram; a reaplicação foi
  recusada sem apagar a concessão antiga.
- `base`: schema de `698a3bd4...`, migração publicada de 24/10, seed, migração
  nova, exercício e verificação após reinício passaram.
- As colunas e definições das restrições de `clinical_access_grants` ficaram
  idênticas nos três caminhos. A linha antiga conservou `granted_at` e os
  quatro campos novos nulos; prontuário e evolução fictícios anteriores
  permaneceram. A concessão pôde existir sem prontuário para o paciente A.
- A consulta de elegibilidade negou preparação após primeira consulta
  cancelada ou marcada ausente, preservou preparação por outra `CONFIRMED` e
  continuidade pelo atendimento anterior com evidência completa. `COMPLETED`
  legado sem procedência não concedeu acesso. A inativação e mudança de perfil
  posteriores do confirmador não apagaram o fundamento do leitor elegível.
- PK, FK de origem, FKs de responsáveis e `CHECK` rejeitaram duplicidade,
  participantes/atores inválidos e realização parcial ou sem confirmação
  confiável. Uma falha simulada reverteu estado e evidência no subbloco do
  ensaio. Duas sessões concorrentes deixaram uma única concessão.
- A primeira tentativa do script encontrou o servidor temporário de `initdb`
  e falhou no terceiro destino; a espera foi corrigida e os dois ensaios
  completos seguintes passaram. A limpeza automática removeu os recursos
  exclusivos inclusive após essa falha. Ao final, restaram apenas os três
  contêineres preexistentes da revisão e o volume
  `lumina_s07_docker_review_20261023`.

São resultados **estruturais SQL e da consulta de elegibilidade simulada**.
Não comprovam autenticação HTTP, autorização do ator em “Concluir atendimento”,
privacidade nas rotas, transação da API, tratamento de erros ou aceite clínico.
