# Prontuário e evoluções — contrato HTTP atual

Este guia descreve as cinco rotas implementadas em `records` na Sprint 7. Todas usam o prefixo `/api/v1` e exigem `Authorization: Bearer <access_token>` de usuário ativo. O conteúdo clínico é restrito a dentistas com cadastro profissional elegível, clínica ativa e fundamento assistencial válido para o paciente. Administrador e recepção não recebem conteúdo clínico por essas rotas.

## Rotas existentes

| Método | Caminho | Finalidade e resposta de sucesso |
| --- | --- | --- |
| `GET` | `/api/v1/patients/{patient_id}/record` | Consulta o prontuário; **se não existir, cria um** após autorizar. Retorna `200` e `MedicalRecordResponse`. |
| `GET` | `/api/v1/patients/{patient_id}/evolutions` | Lista evoluções visíveis. Retorna `200` e um array, ou `404` se o prontuário ainda não existir. |
| `POST` | `/api/v1/patients/evolutions` | Cria rascunho. Retorna `201` e `ClinicalEvolutionResponse`. |
| `PATCH` | `/api/v1/patients/evolutions/{evolution_id}/draft` | Edita rascunho do próprio autor. Retorna `200` e a evolução atualizada. |
| `POST` | `/api/v1/patients/evolutions/{evolution_id}/finalize` | Finaliza rascunho do próprio autor, sem corpo. Retorna `200` e a evolução finalizada. |

`patient_id` e `evolution_id` nos caminhos são IDs inteiros. Não existem nesta API rotas HTTP para obter uma evolução isolada, editar `general_notes`, excluir evolução ou retificar uma finalizada. `medical_record_number` do cadastro de paciente não substitui a abertura do prontuário clínico.

## Acesso e visibilidade

Uma confirmação confiável de consulta **atualmente `CONFIRMED`** para a mesma dupla paciente–dentista na clínica sustenta acesso de preparação. Uma consulta `COMPLETED` com confirmação e evidência válida da realização sustenta continuidade. Outra origem válida da mesma dupla pode manter o acesso após cancelamento ou ausência; esses eventos não apagam evidências. Consulta apenas `SCHEDULED`, clínica comum ou autoria antiga, isoladamente, não bastam.

A API verifica novamente usuário ativo, perfil `DENTIST`, cadastro com CRO/UF preenchidos, clínica ativa, clínica do paciente e ao menos uma origem válida a cada requisição. A lista inclui evoluções `FINALIZED` de todos os autores e apenas evoluções `DRAFT` do dentista leitor, em ordem decrescente de `recorded_at`. O autor perde acesso ao próprio rascunho se perder todo fundamento assistencial. Rascunhos de terceiros não aparecem na lista nem podem ser editados ou finalizados por eles.

O `GET /record` autoriza **antes** de consultar ou criar dados e expõe `general_notes` somente ao dentista elegível. Sua criação implícita é o contrato implementado hoje; D02 ainda decidirá a separação entre consulta e abertura explícita. Não apresente esse `GET` como operação somente de leitura.

## Corpos, campos e valores nulos

| Operação | Contrato atual |
| --- | --- |
| `POST /patients/evolutions` | `patient_id` e `description` são obrigatórios. `appointment_id`, `procedure_performed` e `notes` são opcionais e aceitam `null`. O servidor define `medical_record_id`, autor, `status: "DRAFT"` e horários. |
| `PATCH .../{evolution_id}/draft` | `description`, `procedure_performed` e `notes` são opcionais. Campo omitido ou enviado como `null` **não altera** o valor atual; string vazia é gravada. |
| `POST .../{evolution_id}/finalize` | Sem corpo. O servidor muda `DRAFT` para `FINALIZED` e registra `finalized_at`. |

Quando `appointment_id` é informado, a consulta deve pertencer à mesma clínica, ao paciente e ao dentista autenticado. Só pode haver uma evolução vinculada a cada consulta; uma segunda criação recebe `409`, portanto o frontend deve recuperar o registro pela listagem. O código atual aceita `appointment_id: null` se houver outro fundamento de acesso, mas a regra de atendimento sem agendamento ainda depende de D03.

O schema atual não rejeita campos extras no corpo de criação: um `dentist_id` enviado pelo cliente é ignorado. **Não envie autor nem `medical_record_id`**; a autoria vem da sessão. `description` é exigida na criação, mas texto vazio ou apenas espaços ainda não é recusado na finalização. O conteúdo mínimo depende de D04. `null` na edição não limpa campos opcionais; para limpar `procedure_performed` ou `notes` no contrato atual, envie `""`.

## Exemplos com dados fictícios

### Abrir ou consultar prontuário

```http
GET /api/v1/patients/21/record HTTP/1.1
Authorization: Bearer <access_token>
```

Resposta HTTP `200` de primeira abertura (valores e horários ilustrativos):

```json
{
  "id": 15,
  "patient_id": 21,
  "general_notes": null,
  "opened_at": "2026-10-28T14:00:00Z",
  "updated_at": "2026-10-28T14:00:00Z"
}
```

Nova chamada autorizada retorna o mesmo prontuário. Não há `POST /record` neste contrato.

### Listar e criar rascunho

`GET /api/v1/patients/21/evolutions` retorna `200` com `[]` quando o prontuário existe, mas ainda não há evoluções visíveis. Para criar:

```http
POST /api/v1/patients/evolutions HTTP/1.1
Authorization: Bearer <access_token>
Content-Type: application/json

{"patient_id":21,"appointment_id":42,"description":"Avaliação clínica fictícia","procedure_performed":null,"notes":"Retorno combinado"}
```

Resposta HTTP `201` completa. O objeto `dentist` apresenta os dados **atuais** do cadastro profissional:

```json
{
  "id": 81,
  "medical_record_id": 15,
  "status": "DRAFT",
  "description": "Avaliação clínica fictícia",
  "procedure_performed": null,
  "notes": "Retorno combinado",
  "appointment_id": 42,
  "recorded_at": "2026-10-28T14:05:00Z",
  "finalized_at": null,
  "created_at": "2026-10-28T14:05:00Z",
  "dentist": {
    "id": 7,
    "full_name": "Dra. Beatriz Exemplo",
    "cro_number": "12345",
    "cro_state": "PE"
  }
}
```

Se o prontuário ainda não existe, sua abertura e a criação do rascunho usam uma transação: falha na criação reverte ambas. A resposta da listagem é um array de objetos nesse formato, filtrado pela regra de visibilidade acima.

### Editar e finalizar

```http
PATCH /api/v1/patients/evolutions/81/draft HTTP/1.1
Authorization: Bearer <access_token>
Content-Type: application/json

{"description":"Evolução clínica fictícia revisada","notes":""}
```

Resposta HTTP `200`: o mesmo objeto de evolução, com `description` revisada, `notes: ""` e `status: "DRAFT"`. Para finalizar, o próprio autor envia:

```http
POST /api/v1/patients/evolutions/81/finalize HTTP/1.1
Authorization: Bearer <access_token>
```

Resposta HTTP `200`: o mesmo objeto, agora com `status: "FINALIZED"` e `finalized_at` preenchido. Outra edição ou finalização comum dessa evolução recebe `422`. Finalizar evolução **não** conclui a consulta da Agenda; `COMPLETED` e `care_occurred_at` pertencem ao contrato da Agenda.

## Erros e integração do frontend

| HTTP | Quando ocorre |
| --- | --- |
| `401` | Token ausente/inválido ou usuário inativo. |
| `403` | Perfil não clínico, cadastro profissional/clínica sem elegibilidade, outra clínica, vínculo ausente ou tentativa de editar/finalizar rascunho de outro autor autorizado. |
| `404` | Paciente, evolução ou consulta vinculada inexistente/incompatível; listagem antes da abertura do prontuário. |
| `409` | Consulta já vinculada a uma evolução. |
| `422` | Corpo inválido ou tentativa de editar/finalizar evolução fora de `DRAFT`. |
| `500` | Falha inesperada. |

O envelope é `{"error":{"code":"...","message":"...","details":null}}`. Em validação do corpo, `details` contém locais/tipos sem repetir conteúdo clínico enviado; a API também não o registra no log de validação. Exemplos do contrato atual:

```json
{"error":{"code":"CONFLICTERROR","message":"A consulta já possui evolução clínica.","details":null}}
```

```json
{"error":{"code":"INVALID_STATE_TRANSITION","message":"Evoluções finalizadas não podem ser editadas.","details":null}}
```

O frontend atual chama `recordsApi.getOrOpen`, lista evoluções e oferece criação, edição e finalização. Deve tratar `403` como perda/ausência de autorização, `404` da listagem como prontuário ainda não aberto e `409` como duplicidade a recuperar pela lista. Botões não substituem a checagem do servidor. Não exiba texto clínico de respostas de erro; `GET /health` não comprova acesso ao banco.

**Regra aprovada:** a leitura depende de preparação ou continuidade comprovada; finalizadas são compartilhadas entre dentistas autorizados e rascunhos permanecem privados ao autor. **Comportamento implementado:** as verificações e rotas acima aplicam essa leitura e a autoria; criação e finalização ainda seguem condições de escrita herdadas. **Pendências:** D02 (abertura explícita), D03/D04 (estados de escrita, atendimento avulso e conteúdo mínimo), D05 (nome/CRO histórico e retificação) e D06 (paciente inativo). Nome e CRO mostrados hoje vêm do cadastro atual, sem fotografia histórica.

**Limite concorrente conhecido:** a autorização pode deixar de valer enquanto edição ou finalização aguarda bloqueio da linha. Essa mutação não reconfere o fundamento após a espera; não considere o bloqueio garantia integral de autorização. Edições simultâneas do mesmo rascunho também não têm controle de versão para impedir sobrescrita silenciosa. A migração preparada não foi aplicada ao PostgreSQL existente apenas por publicar esta API.

Ver também [Agenda](../appointments/README.md), [repasse técnico clínico](../../../docs/clinical-api-technical-handoff.md) e [decisões e requisitos](../../../docs/requisitos/README.md).