# Repasse Técnico — Banco de Dados da Agenda

## 1. Objetivo

Este documento apresenta as alterações realizadas no PostgreSQL para preparar o módulo de Agenda e orienta a implementação do backend.

A estrutura foi atualizada para permitir o registro dos estados da consulta, o cálculo automático do período ocupado e o bloqueio de horários sobrepostos para o mesmo dentista.

## 2. Arquivos relacionados

A estrutura completa para bancos novos está disponível em:

```text
backend/database/schema.sql
```

A atualização de bancos que já possuem as tabelas criadas deve ser feita por meio da migração:

```text
backend/database/migrations/20260930_add_no_show_and_prevent_appointment_overlap.sql
```

O `schema.sql` completo não deve ser executado em um banco existente, pois tentaria criar novamente todas as tabelas.

## 3. Aplicação da migração

Para atualizar um banco local já existente, executar a partir do diretório `backend`:

```bash
psql \
  -h 127.0.0.1 \
  -p 5432 \
  -U clinic_app \
  -d clinic_management \
  -W \
  -v ON_ERROR_STOP=1 \
  -f database/migrations/20260930_add_no_show_and_prevent_appointment_overlap.sql
```

A migração realiza as seguintes operações:

- instala a extensão `btree_gist`;
- adiciona o estado `NO_SHOW`;
- cria a coluna interna `scheduled_period`;
- calcula o período dos registros existentes;
- cria o gatilho responsável pelo cálculo automático;
- impede agendamentos ativos sobrepostos para o mesmo dentista.

A migração deve ser aplicada somente uma vez em cada banco.

## 4. Dados recebidos pela API

No cadastro ou reagendamento de uma consulta, a API deverá receber e persistir principalmente:

```text
clinic_id
patient_id
dentist_id
scheduled_at
duration_minutes
status
notes
```

Os campos principais relacionados ao horário são:

- `scheduled_at`: data e horário de início;
- `duration_minutes`: duração prevista da consulta em minutos.

Exemplo:

```json
{
  "patient_id": 10,
  "dentist_id": 1,
  "scheduled_at": "2026-10-15T09:00:00-03:00",
  "duration_minutes": 30,
  "notes": "Consulta de avaliação"
}
```

O `clinic_id` não deve ser aceito livremente do frontend. Ele deve ser obtido do usuário autenticado para impedir acesso ou cadastro em outra clínica.

## 5. Cálculo do período

O frontend e a API não devem enviar o campo `scheduled_period`.

O PostgreSQL calcula esse campo automaticamente por meio do gatilho `trg_appointments_set_period`, utilizando:

```text
scheduled_at + duration_minutes
```

Por exemplo:

```text
Início: 09:00
Duração: 30 minutos
Período calculado: [09:00, 09:30)
```

O formato `[)` significa que o horário inicial pertence à consulta e o horário final fica disponível. Portanto, se uma consulta terminar às 09:30, outra poderá começar exatamente às 09:30.

O modelo ORM poderá representar `scheduled_period` como campo gerenciado pelo banco, mas esse campo não deve ser alterado diretamente pelo cliente.

## 6. Conflito de horário

A restrição `ex_appointments_dentist_active_period` impede que o mesmo dentista tenha dois agendamentos ativos em períodos sobrepostos.

A regra considera como ativos os estados:

```text
SCHEDULED
CONFIRMED
```

Consultas nos estados abaixo não bloqueiam o horário:

```text
COMPLETED
CANCELED
NO_SHOW
```

Quando ocorrer sobreposição, o PostgreSQL produzirá uma violação de restrição de exclusão, normalmente identificada pelo código SQLSTATE:

```text
23P01
```

O backend deverá capturar esse erro e retornar:

```text
HTTP 409 Conflict
```

Mensagem sugerida:

```json
{
  "error": {
    "code": "APPOINTMENT_TIME_CONFLICT",
    "message": "O dentista já possui uma consulta agendada nesse período."
  }
}
```

Os detalhes internos da exceção do PostgreSQL não devem ser enviados diretamente ao frontend.

## 7. Cadastro profissional do dentista

Atualmente, a criação de um usuário com perfil `DENTIST` gera uma conta na tabela `users`, mas a Agenda utiliza `dentists.id`.

O cadastro de um dentista deverá criar dois registros:

```text
users
  └── dentists
```

O formulário do frontend deverá solicitar, quando o perfil selecionado for Dentista:

- nome completo;
- e-mail;
- CPF;
- telefone;
- senha;
- número do CRO;
- UF do CRO;
- especialidade, quando informada.

O backend deverá:

1. criar o usuário com `role = DENTIST`;
2. criar o perfil profissional em `dentists`;
3. associar `dentists.user_id` ao usuário criado;
4. realizar as duas operações na mesma transação;
5. desfazer a criação do usuário caso o perfil profissional não possa ser criado.

Para administradores e recepcionistas, nenhum registro deverá ser criado em `dentists`.

Também deverá ser definido um procedimento para completar os dados profissionais das contas de dentista criadas antes dessa implementação.

## 8. Regras que permanecem no backend

A restrição do PostgreSQL protege a concorrência de horários, mas as demais regras deverão ser implementadas na camada de serviço da API.

### 8.1 Clínica

Antes de criar ou alterar um agendamento, validar que:

- o paciente pertence à clínica do usuário autenticado;
- o dentista pertence à mesma clínica;
- o agendamento pertence à mesma clínica;
- o usuário não consegue consultar dados de outra clínica.

### 8.2 Situação dos cadastros

Antes do agendamento, validar que:

- o paciente está ativo;
- o usuário associado ao dentista está ativo;
- o perfil profissional do dentista existe;
- a clínica está ativa.

### 8.3 Data e horário

Validar que:

- o horário não está no passado;
- a duração é maior que zero;
- a duração respeita os limites definidos pela equipe;
- o dentista não possui outro atendimento ativo no período.

A verificação na API melhora a mensagem apresentada ao usuário. A restrição do PostgreSQL permanece necessária para impedir duas reservas simultâneas.

### 8.4 Permissões

As permissões definidas para a Agenda são:

| Operação              | Administrador     | Recepcionista     | Dentista              |
| --------------------- | ----------------- | ----------------- | --------------------- |
| Consultar agenda      | Agenda da clínica | Agenda da clínica | Próprios atendimentos |
| Criar consulta        | Permitido         | Permitido         | Negado                |
| Editar ou reagendar   | Permitido         | Permitido         | Negado                |
| Cancelar              | Permitido         | Permitido         | Negado                |
| Marcar como concluída | Permitido         | Negado            | Próprios atendimentos |
| Registrar ausência    | Permitido         | Permitido         | Próprios atendimentos |

O dentista deverá visualizar e alterar apenas os atendimentos associados ao seu próprio `dentists.id`.

### 8.5 Estados

Os estados reconhecidos pelo banco são:

```text
SCHEDULED
CONFIRMED
COMPLETED
CANCELED
NO_SHOW
```

O backend não deverá permitir a troca livre do estado. As transições precisam seguir as regras registradas em `docs/business-rules.md`.

Consultas concluídas, canceladas ou marcadas como ausência não devem voltar para um estado ativo sem uma regra específica de reabertura.

## 9. Testes necessários

A implementação deverá incluir testes para:

- criação de consulta válida;
- cálculo do período;
- duas consultas consecutivas sem sobreposição;
- bloqueio de consultas sobrepostas;
- reutilização de horário após cancelamento;
- tentativa de utilizar paciente inativo;
- tentativa de utilizar dentista inativo;
- tentativa de agendamento em horário passado;
- paciente e dentista de clínicas diferentes;
- permissões de administrador, recepcionista e dentista;
- transições permitidas e proibidas;
- isolamento entre clínicas;
- conversão do conflito do PostgreSQL em resposta HTTP `409`.

## 10. Validação já realizada

A migração foi aplicada com sucesso no PostgreSQL local.

Foi criada temporariamente uma consulta das 09:00 às 09:30. Em seguida, tentou-se criar outra consulta para o mesmo dentista das 09:15 às 09:45.

O PostgreSQL bloqueou a segunda operação por meio da restrição:

```text
ex_appointments_dentist_active_period
```

O teste foi executado dentro de uma transação e finalizado com `ROLLBACK`, sem manter os registros fictícios no banco.
