# Lumina Odonto

Sistema de gestão para clínica odontológica desenvolvido no contexto das
disciplinas de Fábrica de Software e Extensão. O objetivo é formar uma base
segura e organizada para a equipe administrar o acesso ao sistema e os
cadastros de pacientes.

Este README descreve somente o que está disponível no repositório nesta etapa.
Funcionalidades planejadas não devem ser tratadas como concluídas.

## Execução de desenvolvimento — referência PR18

O repositório contém API FastAPI, frontend React/Vite e o schema PostgreSQL 16
unificado do PR #18. A execução reproduzível por Docker e os comandos de início,
status, parada e recuperação estão em [Ambiente de desenvolvimento](docs/ambiente-desenvolvimento.md).
O fluxo clínico novo e OpenCL da Agenda dependem de integração e testes próprios.

As seções funcionais abaixo são o registro histórico da fundação da Sprint 4.
A disponibilidade atual de cada módulo deve ser conferida na versão em uso.

## Funcionalidades implementadas

- Health check público em `GET /health`.
- Login OAuth2 Password com JWT de acesso e renovação de sessão.
- Consulta do usuário autenticado.
- Perfis `ADMINISTRATOR`, `RECEPTIONIST` e `DENTIST`.
- Cadastro de usuários, restrito a administradores.
- Cadastro, listagem, consulta, edição e inativação lógica de pacientes.
- Isolamento dos pacientes por clínica e validações de CPF, e-mail e campos
  obrigatórios.
- Documentação interativa da API via Swagger/OpenAPI.
- Testes automatizados da API com SQLite em memória.

## Permissões confirmadas

| Ação | Administrador | Recepcionista | Dentista |
|---|:---:|:---:|:---:|
| Login, refresh e consulta do próprio usuário | Sim | Sim | Sim |
| Cadastrar usuário | Sim | Não | Não |
| Listar e consultar pacientes | Sim | Sim | Sim |
| Cadastrar, editar e inativar pacientes | Sim | Sim | Não |

O paciente não possui acesso ao sistema. A exclusão pela API é lógica: o
registro recebe `is_active = false` e não é apagado fisicamente.

## Próximos passos e fora do escopo atual

- Listagem de usuários: `GET /api/v1/users` ainda não existe.
- Permitir que dentistas cadastrem ou alterem pacientes ainda não está
  implementado.
- A integração funcional de interface, Agenda e prontuários precisa ser
  verificada na candidata identificada. IA e métricas financeiras permanecem
  sujeitas ao planejamento próprio.
- O provisionamento de desenvolvimento usa a cadeia Alembic até
  `a6e8f0b2c4d6`, pelo procedimento documentado para banco vazio.

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
docs/                        # Documentação técnica e materiais da Sprint 4
frontend/                    # Diretório reservado; sem código versionado atual
README.md                    # Visão geral do projeto
```

## Documentação técnica

- [Contrato de integração da API](docs/api-integration.md)
- [Guia de desenvolvimento local](docs/development.md)
- [Arquitetura](docs/architecture.md)
- [Banco de dados](docs/database.md)
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
