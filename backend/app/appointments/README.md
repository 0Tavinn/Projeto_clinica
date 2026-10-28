# Agenda — contrato HTTP implementado

Este guia descreve as rotas da Agenda presentes no código da Sprint 7. A API usa o prefixo `/api/v1`. Todas as rotas abaixo exigem `Authorization: Bearer <access_token>` de um usuário ativo; a clínica vem da sessão, não do corpo enviado pelo cliente. Os perfis são `ADMINISTRATOR` (administrador), `RECEPTIONIST` (recepção) e `DENTIST` (dentista).

## Rotas e permissões

| Método | Caminho | Finalidade | Perfis autorizados |
| --- | --- | --- | --- |
| `POST` | `/api/v1/appointments` | Agendar consulta. | Administrador, recepção. |
| `GET` | `/api/v1/appointments` | Listar e filtrar consultas da clínica. | Os três; dentista vê somente as próprias. |
| `GET` | `/api/v1/appointments/{appointment_id}` | Consultar uma consulta. | Os três; dentista vê somente a própria. |
| `PATCH` | `/api/v1/appointments/{appointment_id}` | Editar dados ou mudar situação. | Administrador e recepção editam dados e situações permitidas; dentista muda somente a situação da própria consulta. |
| `PATCH` | `/api/v1/appointments/{appointment_id}/status` | Mudar situação. | Os três, conforme transições e responsabilidade abaixo. |
| `POST` | `/api/v1/appointments/{appointment_id}/cancel` | Cancelar sem corpo; caminho alternativo à mudança de situação. | Administrador, recepção. |

`appointment_id` é o ID inteiro da consulta. Uma consulta fora da clínica, inexistente ou pertencente a outro dentista retorna `404` ao dentista. Ocultar botões na interface melhora a experiência, mas **não substitui a autorização feita pela API**.

### Filtros de `GET /api/v1/appointments`

| Nome exato | Efeito |
| --- | --- |
| `start_date` | Início do intervalo, inclusivo: `scheduled_at >= start_date`. |
| `end_date` | Fim do intervalo, exclusivo: `scheduled_at < end_date`. |
| `dentist_id`, `patient_id` | Filtram pelos IDs; devem ser inteiros positivos. Não ampliam a visibilidade do dentista. |
| `status` | Um de `SCHEDULED`, `CONFIRMED`, `COMPLETED`, `CANCELED`, `NO_SHOW`. |
| `start`, `end` | Nomes antigos ainda aceitos, mas marcados como obsoletos no OpenAPI. `start_date`/`end_date` prevalecem quando ambos são informados. |

`start_date` deve ser anterior a `end_date` quando ambos são enviados. A lista vem em ordem crescente de `scheduled_at`; sem resultados, retorna `[]` com HTTP `200`. O detalhe e todas as mutações bem-sucedidas retornam um objeto de consulta no mesmo formato.

## Corpos e valores nulos

| Operação | Campos |
| --- | --- |
| `POST /appointments` | Obrigatórios: `patient_id` e `dentist_id` (inteiros positivos), `scheduled_at` (data e hora). Opcionais: `duration_minutes` (inteiro positivo; padrão `30`) e `notes` (texto ou `null`). A API define `clinic_id` pela sessão e `status` inicial como `SCHEDULED`. |
| `PATCH /appointments/{appointment_id}` | Todos opcionais: `patient_id`, `dentist_id`, `scheduled_at`, `duration_minutes`, `notes`, `status`, `care_occurred_at`. Envie apenas os campos a alterar. |
| `PATCH /appointments/{appointment_id}/status` | `status` é obrigatório; `care_occurred_at` acompanha somente `COMPLETED`. |
| `POST /appointments/{appointment_id}/cancel` | Sem corpo. |

No `PATCH` genérico, `notes: null` limpa as observações. `scheduled_at: null` e `duration_minutes: null` retornam `422`; `patient_id` ou `dentist_id` nulo não remove o participante e resulta em participante não encontrado (`404`). `status: null` não muda a situação; omita esse campo quando não houver transição. `care_occurred_at` ausente ou nulo com `COMPLETED`, ou informado com outra situação, retorna `422`. Campos desconhecidos são rejeitados (`422`). Não envie `clinic_id`, `created_at`, `updated_at` nem `scheduled_period` como campos gerenciados pela API/banco.

Ao criar ou alterar participantes, eles devem pertencer à clínica e estar ativos. Alterações administrativas de horário, duração ou observações revalidam um horário futuro e a ausência de sobreposição; dados de consultas em situação final não podem ser editados. Uma consulta que já possui evidência clínica não aceita troca comum de paciente ou dentista (`409`); a correção controlada ainda depende de decisão.

## Situações, evidências e horários

| Situação atual | Destino | Quem pode solicitar | Condição adicional |
| --- | --- | --- | --- |
| `SCHEDULED` | `CONFIRMED`, `CANCELED` | Administrador, recepção. | Confirmar registra evidência própria com autor e instante. |
| `SCHEDULED` | `NO_SHOW` | Administrador, recepção ou dentista responsável. | O horário agendado já deve ter iniciado. |
| `CONFIRMED` | `CANCELED` | Administrador, recepção. | A evidência anterior não é apagada. |
| `CONFIRMED` | `NO_SHOW` | Administrador, recepção ou dentista responsável. | O horário agendado já deve ter iniciado. |
| `CONFIRMED` | `COMPLETED` | **Somente o dentista responsável.** | Exige confirmação confiável, início da consulta e `care_occurred_at` válido. |

`COMPLETED`, `CANCELED` e `NO_SHOW` não têm transições de saída. Repetir a mesma transição ou tentar `SCHEDULED → COMPLETED` retorna `422`. Administrador e recepção não concluem atendimento, inclusive pelo `PATCH` genérico. O dentista não edita participantes, horário, duração ou observações pela Agenda.

Confirmação e realização possuem **evidências distintas** vinculadas à consulta. `CONFIRMED` grava a confirmação e sua autoria; `COMPLETED` grava o horário da realização informado pelo dentista, o autor e o instante do registro. Situação e evidência são persistidas na mesma transação. Uma consulta antiga marcada `CONFIRMED` sem confirmação confiável não pode ser concluída por essa operação. Cancelamento e ausência não apagam evidências. **Concluir a consulta não finaliza uma evolução clínica.** Esses campos de evidência não aparecem no objeto de resposta da Agenda.

Envie datas ISO 8601 com fuso, por exemplo `2026-11-03T09:00:00-03:00` ou `2026-11-03T12:00:00Z`. O backend aceita `scheduled_at` e filtros sem fuso e os interpreta como UTC; para evitar mudança involuntária de horário, o frontend deve enviar o fuso explicitamente. O horário de criação ou reagendamento deve ser futuro. `care_occurred_at` **exige fuso**, não pode ser futuro e é exigido somente para `COMPLETED`; não o deduza de `scheduled_at` nem do instante de envio. Para filtrar um dia local, converta seus limites para instantes e lembre que `end_date` é exclusivo.

## Exemplos com dados fictícios

### Criar e consultar

Requisição da recepção (o token é ilustrativo):

```http
POST /api/v1/appointments HTTP/1.1
Authorization: Bearer <access_token>
Content-Type: application/json

{"patient_id":21,"dentist_id":7,"scheduled_at":"2026-11-03T09:00:00-03:00","duration_minutes":30,"notes":"Avaliação"}
```

Resposta HTTP `201` (todos os campos do objeto de Agenda; horários gerados são ilustrativos):

```json
{
  "id": 42,
  "clinic_id": 3,
  "patient_id": 21,
  "patient_name": "Ana Exemplo",
  "dentist_id": 7,
  "dentist_name": "Dr. Bruno Exemplo",
  "scheduled_at": "2026-11-03T12:00:00Z",
  "status": "SCHEDULED",
  "notes": "Avaliação",
  "duration_minutes": 30,
  "created_at": "2026-10-28T14:00:00Z",
  "updated_at": "2026-10-28T14:00:00Z"
}
```

`GET /api/v1/appointments/42` responde `200` com esse mesmo formato. Exemplo de filtro: `GET /api/v1/appointments?start_date=2026-11-03T03:00:00Z&end_date=2026-11-04T03:00:00Z&dentist_id=7&patient_id=21&status=SCHEDULED`. A resposta é um array desse objeto, ou `[]` se não houver correspondência.

### Editar, confirmar, concluir e cancelar

O administrador ou a recepção pode reagendar e limpar `notes` por `PATCH /api/v1/appointments/42`:

```json
{"scheduled_at":"2026-11-04T10:00:00-03:00","duration_minutes":45,"notes":null}
```

Para confirmar uma consulta `SCHEDULED`, envie `PATCH /api/v1/appointments/42/status`:

```json
{"status":"CONFIRMED"}
```

Após o início de uma consulta **já confirmada**, o dentista responsável conclui pela mesma rota (ou pelo `PATCH /api/v1/appointments/42`, com o mesmo corpo):

```http
PATCH /api/v1/appointments/42/status HTTP/1.1
Authorization: Bearer <access_token>
Content-Type: application/json

{"status":"COMPLETED","care_occurred_at":"2026-11-04T10:12:00-03:00"}
```

Resposta HTTP `200` da conclusão, em exemplo fictício executado após esse horário:

```json
{
  "id": 42,
  "clinic_id": 3,
  "patient_id": 21,
  "patient_name": "Ana Exemplo",
  "dentist_id": 7,
  "dentist_name": "Dr. Bruno Exemplo",
  "scheduled_at": "2026-11-04T13:00:00Z",
  "status": "COMPLETED",
  "notes": null,
  "duration_minutes": 45,
  "created_at": "2026-10-28T14:00:00Z",
  "updated_at": "2026-10-28T14:00:00Z"
}
```

As demais mutações bem-sucedidas retornam `200` com o mesmo conjunto de campos e a situação atualizada. Para cancelar uma consulta ainda `SCHEDULED` ou `CONFIRMED`, administrador/recepção enviam `POST /api/v1/appointments/42/cancel` **sem corpo**, ou `PATCH .../status` com `{"status":"CANCELED"}`. Cancelamento não exclui a consulta; a rota `/cancel` não é permitida ao dentista.

## Respostas de erro e integração

| HTTP | Uso observado |
| --- | --- |
| `401` | Token ausente, inválido, expirado ou usuário inativo. |
| `403` | Perfil sem permissão para a ação. |
| `404` | Consulta não encontrada ou fora do alcance do dentista; participante fora da clínica. |
| `409` | Horário sobreposto, troca de participantes com evidência ou evidência de confirmação já existente. |
| `422` | Corpo/filtro inválido, clínica ou participante inativo, horário não futuro, transição inválida ou conclusão sem evidência/horário válido. |
| `500` | Falha inesperada. |

O envelope é `{"error":{"code":"...","message":"...","details":null}}`. Em erros de validação do corpo, `details` pode ser uma lista de locais e tipos, sem repetir os valores enviados. Exemplo real do contrato de conflito de horário (`409`):

```json
{
  "error": {
    "code": "APPOINTMENT_TIME_CONFLICT",
    "message": "O dentista já possui uma consulta agendada nesse período.",
    "details": null
  }
}
```

Outros códigos específicos: `APPOINTMENT_PARTICIPANT_CONFLICT` (`409`) e `VALIDATION_ERROR` (`422` para validação do corpo). Uma transição de situação inválida retorna `422`; não trate uma falha de rede como erro de autorização.

**Frontend ainda pendente:** `appointmentsApi.updateStatus` em `frontend/src/api.ts` envia somente `{status}`. A interface precisa coletar e enviar `care_occurred_at` com fuso ao concluir; essa alteração **não está implementada**. Exiba apenas ações adequadas ao perfil, à consulta e ao estado, mas sempre trate `403`, `404`, `409` e `422` devolvidos pela API. `GET /health` verifica o processo, não a conexão com o banco.

**Regra aprovada:** a conclusão pertence ao dentista responsável, parte de `CONFIRMED` com confirmação confiável e registra situação e realização juntas. **Comportamento implementado:** as rotas e transições descritas acima aplicam essa regra na Agenda. **Pendente:** a interface ainda não envia o horário exigido; abertura do prontuário, condições de escrita da evolução e correções históricas seguem as decisões D02–D06.

**Limite conhecido:** a autorização clínica pode ser perdida enquanto uma mutação clínica aguarda bloqueio; a proteção concorrente desse fluxo ainda precisa de correção e teste. A Agenda não deve ser apresentada como garantia de proteção concorrente integral do prontuário.

Ver também [repasse técnico clínico](../../../docs/clinical-api-technical-handoff.md) e [índice de decisões e requisitos](../../../docs/requisitos/README.md).