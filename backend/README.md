# API Lumina Odonto

API FastAPI para a base de desenvolvimento da Sprint 6. O código contém
autenticação, perfis, usuários, pacientes, dentistas e Agenda. O planejamento
clínico ainda é uma [proposta](../docs/sprint/sprint-06.md); Prontuário e
Evolução Clínica não têm models, serviços ou rotas implementados.

## Ambiente local

Use Python 3.11 ou 3.12 e PostgreSQL. A partir de `backend/`:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
cp .env.example .env
```

Configure no `.env` local `DATABASE_URL`, `SECRET_KEY` e `CORS_ORIGINS` para a
origem do frontend. Nunca versione ou compartilhe valores dessas variáveis.
Para um banco **novo e vazio**, aplique `database/schema.sql`; para um banco
PostgreSQL anterior à Agenda, siga a inspeção e a migração específica descritas
no [guia do banco](../docs/guides/database-setup.md). Não aplique o SQL de criação e a
migração da Agenda em sequência no mesmo banco novo. `alembic upgrade head`
não reproduz o esquema PostgreSQL completo nesta base.

O seed de demonstração (`python -m scripts.seed`) modifica o banco configurado
e deve ser usado somente em ambiente local autorizado. Ele cria dados
fictícios para a equipe e a Agenda. As credenciais e a chave JWT devem ser
definidas e guardadas no ambiente local, sem publicação no repositório.

Inicie a API na pasta `backend/`:

```bash
uvicorn app.main:app --reload
```

O Swagger fica em `http://localhost:8000/docs` e o health check em
`http://localhost:8000/health`. O frontend usa a origem configurada em
`VITE_API_URL` ou, por padrão, `http://localhost:8000/api/v1`.

## Rotas e perfis atuais

Todas as rotas abaixo, salvo `/health`, usam o prefixo `/api/v1`. O login
recebe formulário OAuth2 com e-mail em `username` e senha em `password`.

| Domínio | Rotas | Acesso principal |
| --- | --- | --- |
| Autenticação | `POST /auth/login`, `POST /auth/refresh`, `GET /auth/me` | Login público; refresh com token; consulta autenticada |
| Usuários | `GET /users`, `POST /users` | Administrador |
| Pacientes | `POST /patients`, `GET /patients`, `GET /patients/{id}`, `PATCH /patients/{id}`, `DELETE /patients/{id}` | Consulta por toda a equipe; criação/edição também por dentista; inativação por administrador/recepção |
| Dentistas | `GET /dentists`, `POST /dentists` | Listagem por administrador/recepção; cadastro profissional por administrador |
| Agenda | `POST /appointments`, `GET /appointments`, `GET /appointments/{id}`, `PATCH /appointments/{id}`, `PATCH /appointments/{id}/status`, `POST /appointments/{id}/cancel` | Leitura por equipe com filtro de dentista; escrita conforme perfil e situação |

As regras exatas de payload, status e permissão estão no
[contrato de integração](../docs/guides/api-integration.md). O paciente não possui
login. O endpoint `DELETE /patients/{id}` faz inativação lógica.

## Testes

```bash
python -m pytest
```

Os testes automatizados usam SQLite em memória. Eles não comprovam sozinhos a
execução da API com PostgreSQL; um ensaio isolado é necessário para esse
ambiente. O Compose existente usa MySQL e não é o caminho suportado para a
base PostgreSQL. Consulte o [guia de desenvolvimento](../docs/development.md)
para iniciar API, banco e frontend em processos separados.

Este é um projeto acadêmico. Qualquer uso com dados reais depende de avaliação
de segurança, privacidade e requisitos legais.
