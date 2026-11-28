# Prontuário e evoluções — contrato atual

[Voltar ao guia de Otávio](../../FRONTEND.md).
Fonte: `app/main.py`, `app/crud.py` e `sql/schema.sql` da candidata consolidada.
Todos os exemplos abaixo usam `Authorization: Bearer <clinical_token>`.
IDs, datas e conteúdo são fictícios; os exemplos não são capturas do QA.

## Selecionar paciente e montar cabeçalho

Usar GET /api/v1/clinical/patients e GET /api/v1/clinical/patients/{patient_id}
com token clínico. Incluem vínculo manual e prontuário vazio, sem exigir
consulta ou evolução. O DTO mínimo, cursor e erros estão no
[contrato de pacientes clínicos e vínculos](clinical-patients-and-links.md).

## Prontuário existente ou vazio

GET `/api/v1/patients/7/record` → 200:

```json
{"id": 3, "patient_id": 7}
```

O cadastro do paciente cria esse registro, mesmo sem evolução. A leitura não
cria outro prontuário. Sem vínculo, o acesso é recusado; um 404 não autoriza
repetir a chamada como uma operação de abertura.

GET `/api/v1/patients/7/record/summary` → 200, exemplo completo:

```json
{
  "id": 3,
  "patient_id": 7,
  "general_notes": null,
  "created_at": "2026-11-26T10:00:00+00:00",
  "updated_at": "2026-11-26T10:00:00+00:00"
}
```

PATCH `/api/v1/patients/7/record`, corpo:

```json
{"general_notes": "Observação geral fictícia."}
```

Retorna 200 com o registro de `medical_records` atualizado, no formato do
summary. Somente `general_notes` é campo deste PATCH; campo extra é 422.
Enviar `null` limpa essa observação. Não usar esse campo como histórico de
atendimentos: a alteração substitui o texto geral. O campo não tem controle
`version` nem autoria individual como as evoluções.

## Listar e ler evoluções

GET `/api/v1/patients/7/evolutions` → 200 com um **array**. Prontuário novo,
sem registro visível, retorna `[]`. Ordenação: `recorded_at DESC`.
Esta rota não implementa `limit`, `offset` ou busca por termo.

São visíveis finalizadas de todos os autores autorizados e rascunhos do
próprio dentista. Autoria antiga sozinha não substitui o vínculo ativo.
Não confiar em filtro no frontend para esconder rascunhos de terceiros.

GET `/api/v1/evolutions/10` → 200 com campos da evolução e `patient_id`.
A listagem retorna os campos de `clinical_evolutions` sem o `patient_id`
adicional do detalhe. Use o paciente selecionado no contexto da lista.

## Criar um rascunho

POST `/api/v1/evolutions`, corpo mínimo:

```json
{"patient_id": 7, "description": "Primeira anotação clínica fictícia."}
```

Opcionais: `appointment_id`, `procedure_performed`, `notes` (aceitam `null`).
A consulta não é obrigatória. Se informada, deve pertencer à clínica,
àquele paciente e ao dentista; incompatibilidade resulta em 422.
Uma consulta já associada a uma evolução pode gerar 409.

A descrição deve conter conteúdo, não apenas espaços. O servidor define
prontuário, autor, estado, versão e horários. Não enviar campos de autoria,
`status`, `recorded_at` ou `finalized_at` como instruções de atualização.

Retorna **201** com a linha da evolução, por exemplo:

```json
{
  "id": 10,
  "medical_record_id": 3,
  "dentist_id": 4,
  "appointment_id": null,
  "recorded_at": "2026-11-26T10:00:00+00:00",
  "status": "DRAFT",
  "description": "Primeira anotação clínica fictícia.",
  "procedure_performed": null,
  "notes": null,
  "finalized_at": null,
  "created_at": "2026-11-26T10:00:00+00:00",
  "updated_at": "2026-11-26T10:00:00+00:00",
  "version": 1
}
```

POST/PATCH/finalize não acrescentam `patient_id` à linha retornada. Conserve
esse contexto na interface; o detalhe GET o fornece quando necessário.

## Editar o próprio rascunho

PATCH `/api/v1/evolutions/10`, corpo:

```json
{
  "version": 1,
  "description": "Anotação fictícia revisada.",
  "procedure_performed": "Procedimento fictício",
  "notes": null
}
```

`version` é inteiro JSON estrito, positivo e obrigatório; `"1"`, `true`,
`null`, zero e ausência resultam em 422. Enviar pelo menos um campo editável:
`description`, `procedure_performed` ou `notes`.

Campo omitido fica inalterado. `procedure_performed`/`notes` nulos limpam o
campo; descrição nula ou vazia é recusada. Não usar corpo somente com versão.

Retorna **200** com a evolução completa, `status: "DRAFT"` e `version: 2`
nesse exemplo. Passe a guardar a versão recebida, sem incrementá-la localmente
antes da resposta. Só o autor pode editar o rascunho.

Versão antiga retorna **409** com `{"detail":"Versão desatualizada"}`.
Preservar o texto digitado, recarregar o registro autorizado e permitir que
o usuário compare antes de reenviar com a nova versão. Não sobrescrever
silenciosamente nem repetir automaticamente com uma versão recém-obtida.

## Finalizar

POST `/api/v1/evolutions/10/finalize`, corpo obrigatório:

```json
{"version": 2}
```

Retorna **200** com a evolução completa, `status: "FINALIZED"`,
`finalized_at` preenchido pelo servidor e `version: 3` nesse exemplo.
O botão não envia a descrição como uma edição implícita: salvar antes e
usar a versão retornada se existir texto alterado na tela.

A finalização é independente do estado da Agenda nesta candidata. O próprio
autor finaliza seu rascunho autorizado. Finalizada ou de outro autor não é
rascunho editável: o código recusa com 403, sem alterar o registro.
Versão desatualizada de rascunho elegível retorna 409. Não presumir qual erro
tem prioridade em situações com várias condições inválidas.

## Erros e limites da interface

- 401: token ausente, inválido/expirado, tipo de token incorreto ou sessão invalidada.
- 403: vínculo/autoria/perfil ou estado não permitem a operação.
- 404: paciente, prontuário ou evolução não encontrado no contexto permitido.
- 409: versão antiga ou conflito de integridade, conforme a operação.
- 422: corpo/campo inválido, consulta incompatível ou ausência de alteração.

Mensagens podem variar conforme a verificação que falhar. Ver também os
[formatos de erro](authentication-and-search.md#erros-para-a-interface).
Em perda de acesso, não manter o histórico anteriormente carregado na tela.
O token clínico não concede acesso a todos os pacientes da clínica.

O detalhe da evolução não fornece nome/CRO histórico do autor; imprime-se
somente após alinhar esses dados e a política de impressão. Não há DELETE
clínico nem rota específica de PDF nesta candidata. Não oferecer edição
comum de finalizadas ou inventar endpoint de retificação.
