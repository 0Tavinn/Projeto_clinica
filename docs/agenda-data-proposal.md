# Proposta técnica — Agenda e dados fictícios

## Objetivo

Este documento registra uma proposta técnica para o módulo de Agenda e para a futura geração de dados fictícios de demonstração. Nenhuma alteração no banco de dados deve ser realizada a partir deste documento sem validação técnica do responsável pelo backend.

## Estrutura atual do banco

A tabela `appointments` já possui os campos principais necessários para o módulo:

- `clinic_id`;
- `patient_id`;
- `dentist_id`;
- `scheduled_at`;
- `status`;
- `notes`;
- `duration_minutes`;
- `created_at`;
- `updated_at`.

A consulta é vinculada corretamente à clínica, ao paciente e ao dentista. O campo `dentist_id` referencia `dentists.id`, e não `users.id`. Portanto, os dados enviados pela API e pelo frontend devem utilizar o identificador do perfil profissional do dentista.

Os estados aceitos atualmente são:

```text
SCHEDULED
CONFIRMED
COMPLETED
CANCELED
```

## Ajustes propostos para validação

### Status de ausência

Adicionar o status abaixo à restrição da tabela `appointments`:

```text
NO_SHOW
```

Esse estado será utilizado quando o paciente não comparecer à consulta. O cancelamento continuará utilizando o estado `CANCELED`, preservando o histórico sem exclusão física do registro.

### Conflitos de horário

A API deverá impedir agendamentos sobrepostos para o mesmo dentista. A validação deve considerar o horário inicial e a duração da consulta.

Consultas com situação `CANCELED` ou `NO_SHOW` não devem bloquear um novo horário.

### Isolamento por clínica

A API deverá garantir que:

- o paciente pertença à clínica do usuário autenticado;
- o dentista pertença à mesma clínica;
- o `clinic_id` do agendamento seja definido com base no usuário autenticado;
- usuários não consigam consultar ou modificar agendamentos de outra clínica.

### Registros inativos

A API deverá impedir a criação ou alteração de agendamentos quando:

- o paciente estiver inativo;
- o usuário vinculado ao dentista estiver inativo.

### Transições de situação

Como proposta inicial, as transições permitidas serão:

```text
SCHEDULED → CONFIRMED
SCHEDULED → CANCELED
SCHEDULED → NO_SHOW

CONFIRMED → COMPLETED
CONFIRMED → CANCELED
CONFIRMED → NO_SHOW
```

Consultas concluídas, canceladas ou marcadas como ausência serão consideradas encerradas e não poderão ser reagendadas diretamente.

### Perfil profissional do dentista

Todo usuário com perfil `DENTIST` utilizado na Agenda deverá possuir um registro correspondente na tabela `dentists`.

O fluxo de cadastro deverá avaliar a criação conjunta de:

1. usuário com perfil `DENTIST`;
2. perfil profissional em `dentists`;
3. CRO;
4. estado do CRO;
5. especialidade, quando informada.

## Proposta de dados fictícios para demonstração

Após validação do modelo técnico e das rotas da Agenda, será criado o script:

```text
backend/scripts/seed_demo.py
```

O script deverá gerar apenas dados fictícios e anonimizados para ambiente local de desenvolvimento.

A base inicial proposta será composta por:

| Tipo de dado | Quantidade proposta |
| :-- | --: |
| Clínica de demonstração | 1 |
| Administrador | 1 |
| Recepcionistas | 2 |
| Dentistas com perfil profissional e CRO fictício | 5 |
| Pacientes ativos | 50 |
| Pacientes inativos | 2 |
| Consultas futuras | 20 |
| Consultas confirmadas | 10 |
| Consultas concluídas | 10 |
| Consultas canceladas | 5 |
| Consultas com ausência | 5, após inclusão de `NO_SHOW` |

O script deverá:

- não apagar dados existentes;
- utilizar e-mails, CPFs, CROs e números de prontuário fictícios;
- evitar duplicação quando executado mais de uma vez;
- criar usuários dentistas e seus respectivos registros em `dentists`;
- criar consultas em horários sem conflito;
- utilizar datas relativas ao momento da execução para manter a demonstração atualizada;
- registrar no terminal os dados criados ou já existentes.

## Decisões que dependem de validação técnica

Antes da implementação, é necessário confirmar:

- a inclusão do status `NO_SHOW`;
- as transições de situação propostas;
- o fluxo de criação do perfil profissional do dentista;
- a estratégia de prevenção de duas reservas simultâneas;
- os filtros definitivos da listagem de Agenda;
- a estrutura final dos endpoints.

Após validação, esta proposta deverá orientar a implementação do backend, do frontend, dos testes e do script de dados fictícios.