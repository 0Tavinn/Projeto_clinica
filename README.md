# Lumina Odonto

Sistema acadêmico de gestão para clínica odontológica, desenvolvido nas
disciplinas de Fábrica de Software e Extensão.

Esta branch prepara a base compartilhável para o desenvolvimento da Sprint 6.
O [planejamento da Sprint 6](docs/sprint/sprint-06.md) ainda é uma **proposta
para alinhamento da equipe**. O módulo de Prontuário e Evolução Clínica não foi
implementado nesta base.

## Estado atual da aplicação

A aplicação possui frontend React/Vite, API FastAPI e persistência projetada
para PostgreSQL. O código conecta autenticação, gestão de usuários, pacientes,
dentistas e Agenda. A execução integrada em um banco de equipe depende da
configuração local e de validação nesse ambiente.

O fluxo suportado nesta base é local, com PostgreSQL, FastAPI e Vite em
processos separados. `backend/compose.yaml` ainda usa MySQL e não fornece o
ambiente PostgreSQL/frontend da Sprint 6. Veja o
[guia de desenvolvimento](docs/development.md).

## Funcionalidades implementadas

- Health check público em `GET /health`.
- Login OAuth2 Password com JWT de acesso e renovação de sessão.
- Consulta do usuário autenticado.
- Perfis `ADMINISTRATOR`, `RECEPTIONIST` e `DENTIST`.
- Listagem e cadastro de usuários por administradores; cadastro de dentista
  cria também seu perfil profissional com CRO e UF.
- Listagem de dentistas ativos para administrador e recepção.
- Cadastro, listagem, consulta, edição e inativação lógica de pacientes.
- Agenda: criação, consulta, filtros, atualização, reagendamento, cancelamento
  e mudanças de situação por perfil, com verificação de horários.
- Interface web conectada às rotas de autenticação, usuários, pacientes,
  dentistas e Agenda.
- Documentação interativa da API via Swagger/OpenAPI.
- Testes automatizados da API com SQLite em memória e testes locais do cliente
  de autenticação do frontend.

## Permissões confirmadas

| Ação | Administrador | Recepcionista | Dentista |
|---|:---:|:---:|:---:|
| Login, refresh e consulta do próprio usuário | Sim | Sim | Sim |
| Listar e cadastrar usuários | Sim | Não | Não |
| Listar dentistas ativos | Sim | Sim | Não |
| Listar e consultar pacientes | Sim | Sim | Sim |
| Cadastrar e editar pacientes | Sim | Sim | Sim |
| Inativar pacientes | Sim | Sim | Não |
| Criar, editar e cancelar consultas | Sim | Sim | Não |
| Consultar Agenda | Sim | Sim | Somente consultas próprias |
| Concluir consultas | Sim | Não | Somente consultas próprias, após o início |
| Registrar ausência | Sim | Sim | Somente consultas próprias, após o início |

O paciente não possui acesso ao sistema. A exclusão pela API é lógica: o
registro recebe `is_active = false` e não é apagado fisicamente.

## Pendente para a Sprint 6

- Prontuário e Evolução Clínica: models, schemas, serviços, rotas, permissões
  específicas, interface e testes ainda precisam ser desenvolvidos.
- Aprovar as decisões clínicas reunidas na
  [revisão técnica](docs/reference/clinical-records-review.md).
- Conciliar o schema PostgreSQL, as migrações Alembic e o ambiente Docker antes
  de oferecer provisionamento automatizado em bancos existentes.
- Reunir evidências de testes e da demonstração final. A presença de rotas e
  telas no código não substitui essa validação.
- Corrigir a navegação móvel antes de uma demonstração em celular: o CSS
  oculta a barra lateral em telas estreitas, mas o botão "Abrir menu" ainda
  não possui ação. Pode ser uma tarefa separada desta preparação de base.

## Tecnologias utilizadas

- Python 3.11 ou 3.12 e FastAPI;
- SQLAlchemy e Psycopg para acesso ao PostgreSQL;
- Pydantic para validação de dados;
- JWT, OAuth2 Password Bearer e Argon2 para autenticação e senhas;
- Pytest e HTTPX nos testes;
- Swagger/OpenAPI disponibilizado pelo FastAPI;
- Git e GitHub para versionamento.

## Estrutura atual do repositório

```text
backend/                    # API FastAPI, schema PostgreSQL, testes e scripts
  app/                       # Rotas, regras de negócio, modelos e segurança
  database/schema.sql        # Estrutura de referência do PostgreSQL
  tests/                     # Testes automatizados
docs/                        # Documentação técnica e planejamento proposto da Sprint 6
frontend/                    # React/Vite, cliente da API e testes do cliente
README.md                    # Visão geral do projeto
```

## Documentação técnica

- **[Guia de desenvolvimento local](docs/development.md)**
- [Contrato de integração da API](docs/guides/api-integration.md)
- [Preparação do banco PostgreSQL](docs/guides/database-setup.md)
- [Revisão clínica para repasse](docs/reference/clinical-records-review.md)
- [Planejamento proposto da Sprint 6](docs/sprint/sprint-06.md)
- [Arquitetura](docs/reference/architecture.md)
- [Banco de dados](docs/reference/database.md)
- [Planejamento da Sprint 4](docs/sprint/sprint-04.md)

## Swagger da API

Com a API local em execução, acesse:

- Swagger: <http://localhost:8000/docs>
- OpenAPI JSON: <http://localhost:8000/openapi.json>
- Health check: <http://localhost:8000/health>

As instruções de ambiente e de inicialização estão no
[guia de desenvolvimento](docs/development.md).

## Equipe

- Caio Cesar
- Cassiano Augusto Brito de Souza
- João Vitor Lima Rocha
- Luiz Otávio de Souza Azevedo
- Paulo Sérgio Barros de Souza
- Tarcísio Alves Viana Costa Filho

## Aviso

Este é um projeto acadêmico. Antes de qualquer uso com dados reais de
pacientes, são indispensáveis avaliação de segurança, adequação à LGPD e
validação jurídica.
