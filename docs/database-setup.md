# Preparação do PostgreSQL para a base da Sprint 6

Este guia cobre o esquema necessário aos módulos já existentes, inclusive a
Agenda. Prontuário e Evolução Clínica ainda não possuem API ou interface. Use
somente dados fictícios no ambiente de desenvolvimento.

## Escolher o caminho pelo estado do banco

| Estado do banco | Procedimento nesta base |
| --- | --- |
| Banco **novo e vazio** | Aplicar uma vez `backend/database/schema.sql`. O arquivo já inclui Agenda, `NO_SHOW`, período, restrição de sobreposição e tabelas clínicas de referência. |
| Banco PostgreSQL com o esquema **anterior à Agenda** | Conferir estrutura, fazer backup e aplicar uma vez `backend/database/migrations/20260930_add_no_show_and_prevent_appointment_overlap.sql` em ambiente autorizado. |
| Banco com `scheduled_period` e a restrição `ex_appointments_dentist_active_period` | A estrutura da Agenda já está presente. Não reaplicar o script. Conferir o restante do esquema antes de prosseguir. |
| Banco criado somente pelo Alembic, esquema desconhecido ou com dados importantes | Nenhuma atualização automática é suportada. Comparar o catálogo com o SQL, planejar a migração específica, registrar backup e pedir revisão do responsável pelo banco. |

O `schema.sql` cria tabelas sem `IF NOT EXISTS` e não é uma migração para banco
existente. O script da Agenda usa `ALTER TABLE` e também não é idempotente. Os
dois caminhos **não devem ser aplicados em sequência no mesmo banco novo**.

## Banco novo e vazio

No Linux/WSL com PostgreSQL instalado e privilégios para criar role e banco:

```bash
sudo service postgresql start
sudo -u postgres createuser --pwprompt clinic_app
sudo -u postgres createdb --owner=clinic_app clinic_management
cd backend
psql -h 127.0.0.1 -p 5432 -U clinic_app -d clinic_management -W -v ON_ERROR_STOP=1 -f database/schema.sql
```

Crie `backend/.env` a partir de `.env.example` e configure `DATABASE_URL` com
driver `postgresql+psycopg`, usuário, senha e banco locais. Configure
`SECRET_KEY` para desenvolvimento sem publicar o valor. O serviço deve ser
iniciado a partir de `backend/` para carregar esse `.env`.

O seed (`python -m scripts.seed`) altera o banco e inclui dados fictícios de
equipe, pacientes e Agenda. Execute-o somente em banco local autorizado.

## Banco existente antes da Agenda

Este caminho serve apenas para o esquema PostgreSQL anterior, com tabela
`appointments`, restrição `ck_appointments_status`, sem coluna
`scheduled_period`, sem gatilho `trg_appointments_set_period` e sem exclusão
`ex_appointments_dentist_active_period`. Antes de qualquer DDL, confirme o
banco de destino e consulte sua estrutura:

```bash
psql -h 127.0.0.1 -p 5432 -U clinic_app -d clinic_management -W
```

Na sessão `psql`, use `\d+ appointments`, `\d+ patients`, `\d+ dentists` e
`\d+ medical_records`. Confirme também a versão de `ck_appointments_status`,
a ausência das estruturas da Agenda listadas acima e eventuais conflitos de
horário já existentes. Faça um backup recuperável em local protegido. Se o
banco diferir desse estado, pare e defina uma migração própria com o
responsável pela API/banco; o script não corrige estados intermediários.

Depois da revisão e autorização para **aquele banco específico**, o comando
de atualização, executado a partir de `backend/`, é:

```bash
psql -h 127.0.0.1 -p 5432 -U clinic_app -d clinic_management -W -v ON_ERROR_STOP=1 -f database/migrations/20260930_add_no_show_and_prevent_appointment_overlap.sql
```

O script opera em transação, adiciona `NO_SHOW`, calcula o período das consultas
anteriores, cria o gatilho e impõe a exclusão de horários ativos sobrepostos.
Se já houver consultas conflitantes, a restrição pode rejeitar a atualização;
é necessário resolver os dados com a equipe antes de repetir.

## Limite do Alembic e do Docker

As duas revisões Alembic atuais criam parte do esquema, mas não as tabelas
clínicas, os gatilhos e a restrição PostgreSQL de sobreposição presentes em
`schema.sql`. `alembic upgrade head` não reproduz sozinho a base completa.
Não o execute em um banco existente apenas para tentar sincronizar versões.
Uma estratégia única de baseline e migrações para bancos com dados permanece
como decisão da equipe.

`backend/compose.yaml` ainda usa MySQL, não inclui o frontend e executa
`alembic upgrade head`. Ele não é um caminho suportado para PostgreSQL nesta
base. Execute PostgreSQL local, API e frontend como descrito no
[guia de desenvolvimento](development.md).
