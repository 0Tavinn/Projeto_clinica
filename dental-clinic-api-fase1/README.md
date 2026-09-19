# Dental Clinic API

Backend de uma aplicação de gestão de clínicas odontológicas, focado em
**prontuários odontológicos** e **agendamentos clínicos**.

> ⚠️ **Este projeto é um MVP acadêmico/profissional.** Ele implementa boas
> práticas de segurança e arquitetura (RBAC, JWT, hashing Argon2, auditoria,
> validação rigorosa de entrada), mas **não deve ir para produção sem antes
> passar por revisão jurídica, revisão de segurança e avaliação formal de
> conformidade com a LGPD** (Lei Geral de Proteção de Dados), já que o
> sistema trata dados pessoais e dados sensíveis de saúde. Itens como
> política de retenção/exclusão de dados, DPO, base legal de tratamento e
> auditoria de terceiros (ex.: provedor de IA) precisam de validação
> jurídica antes de qualquer uso com pacientes reais.

## Status do projeto — Fase 1 concluída

A Fase 1 (fundação da API) está implementada e testada:

- [x] Projeto FastAPI modular por domínio.
- [x] Configuração de ambiente via variáveis de ambiente (Pydantic Settings).
- [x] Banco MySQL + Alembic (migrações versionadas, autogenerate validado).
- [x] Autenticação OAuth2 Password Bearer + JWT (access + refresh token).
- [x] RBAC (controle de acesso por perfil).
- [x] Health check (`GET /health`).
- [x] Tratamento padronizado de erros (`{"error": {"code", "message", "details"}}`).
- [x] Rate limiting no endpoint de login.
- [x] Proteção contra enumeração de usuários no login.
- [x] Docker Compose (API + MySQL).
- [x] 22 testes automatizados (auth, RBAC, hashing, rate limit, health).

As demais fases do backlog (pacientes, profissionais, agendamentos,
prontuários, resumo de pré-consulta por IA, auditoria, processamento
CPU/OpenCL) seguem a mesma estrutura modular já estabelecida aqui e entram
nas próximas iterações.

## Decisão de perfis do MVP

O domínio completo prevê 4 perfis: **Paciente**, **Recepcionista**,
**Dentista** e **Administrador**. Para garantir entrega dentro do prazo, o
MVP ativa apenas dois:

- **Recepcionista** — cobre a ponta de **agendamento** (cadastro básico,
  criação/gestão de consultas, prevenção de conflitos de horário).
- **Dentista** — cobre a ponta de **prontuário** (registro clínico,
  evolução do paciente, solicitação de resumo de pré-consulta por IA).

Essa é exatamente a combinação que atende ao objetivo central do projeto
(prontuários + agendamentos) com o menor escopo possível. Paciente
(acesso ao próprio histórico) e Administrador (relatórios financeiros,
gestão administrativa) ficam modelados na arquitetura — enum `Role`, campo
`clinic_id` em todas as entidades relevantes — mas **sem endpoints ativos**
nesta fase. Isso evita retrabalho estrutural quando forem habilitados.

O enum `Role` e o RBAC (`app/security/permissions.py`) reforçam essa
decisão em tempo de execução: mesmo que um novo endpoint liste
`Role.PATIENT` ou `Role.ADMIN` por engano em `require_roles(...)`, o acesso
é negado enquanto esses perfis não estiverem em `MVP_ACTIVE_ROLES`.

## Arquitetura

Estrutura modular por domínio, com separação de responsabilidades:

```
app/
  main.py                 # entry point FastAPI, CORS, error handlers, health check
  core/
    config.py              # Settings (env vars) — nunca hardcode segredos
    database.py             # engine SQLAlchemy, sessão, Base declarativa
  security/
    hashing.py               # hash/verify de senha (Argon2)
    auth.py                  # emissão/validação de JWT, get_current_user
    permissions.py           # RBAC (require_roles)
    roles.py                 # enum Role + MVP_ACTIVE_ROLES
    rate_limit.py             # rate limiter em memória (login)
  users/
    models.py                # User, Clinic (SQLAlchemy)
    schemas.py                # contratos Pydantic (Token, UserRead, ...)
    repository.py              # acesso a dados
    service.py                 # regras de negócio (login, refresh)
    router.py                  # endpoints /auth/*
  common/
    exceptions.py              # exceções de domínio, desacopladas de HTTP
    error_handlers.py           # tradução de exceções -> resposta HTTP padronizada
  audit/                      # reservado para eventos de auditoria (próxima fase)
alembic/                    # migrações versionadas
scripts/
  seed.py                    # cria clínica + usuários iniciais (dev/demo)
tests/                     # 22 testes (pytest + TestClient)
```

Módulos futuros (`patients`, `professionals`, `appointments`, `records`,
`ai`, `processing`) seguem exatamente o mesmo padrão de `app/users`:
`models.py` → `schemas.py` → `repository.py` → `service.py` → `router.py`.

### Por que essa estrutura

- **`repository` separado de `service`**: troca de banco (MySQL →
  PostgreSQL) ou de estratégia de acesso a dados não deve tocar em regra de
  negócio.
- **Exceções de domínio (`common/exceptions.py`) desacopladas de HTTP**:
  services nunca importam `fastapi`. A tradução para status HTTP acontece
  só em `common/error_handlers.py`, então a lógica de negócio é testável
  sem subir um app HTTP (ver `tests/test_permissions.py`).
- **`Role` compartilhado entre `security` e `users`**: fonte única de
  verdade para RBAC, evitando strings soltas de perfil espalhadas pelo
  código.

## Rodando localmente

### Opção 1 — Docker Compose (recomendado)

```bash
cp .env.example .env
# edite SECRET_KEY em .env com um valor forte, ex:
# python -c "import secrets; print(secrets.token_urlsafe(64))"

docker compose up --build
```

A API sobe em `http://localhost:8000`, já com `alembic upgrade head`
executado automaticamente. Depois, popule os usuários iniciais:

```bash
docker compose exec api python -m scripts.seed
```

### Opção 2 — Ambiente local (Python + MySQL à parte)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env
# ajuste DATABASE_URL para seu MySQL local e defina SECRET_KEY

alembic upgrade head
python -m scripts.seed
uvicorn app.main:app --reload
```

Documentação interativa (OpenAPI/Swagger) disponível em
`http://localhost:8000/docs`.

### Credenciais padrão do seed (⚠️ apenas dev/demo — troque antes de qualquer outro uso)

| Perfil | Email | Senha |
|---|---|---|
| Recepcionista | `recepcao@clinica.demo` | `Recepcao@123` |
| Dentista | `dentista@clinica.demo` | `Dentista@123` |

Sobrescrevíveis via `SEED_RECEPTIONIST_EMAIL`, `SEED_RECEPTIONIST_PASSWORD`,
`SEED_DENTIST_EMAIL`, `SEED_DENTIST_PASSWORD`.

## Rodando os testes

```bash
pip install -e ".[dev]"
pytest -v
```

Os testes rodam contra **SQLite em memória** (nunca contra o MySQL de
desenvolvimento/produção) — ver `tests/conftest.py`. Cobrem:

- Login: sucesso, senha incorreta, email inexistente (com a **mesma**
  resposta genérica de senha incorreta, para não permitir enumeração de
  contas), usuário inativo, rate limit.
- `GET /auth/me`: token ausente, token inválido, token válido (e confirma
  que `hashed_password` nunca é serializado).
- Refresh token: fluxo completo, rejeição de access token usado como
  refresh token.
- RBAC: bloqueio cross-role e bloqueio de perfis ainda não ativos no MVP
  (`PATIENT`/`ADMIN`), mesmo que um endpoint futuro os liste por engano.
- Hashing Argon2 e rate limiter isolado (unitários).

## Autenticação — fluxo resumido

1. `POST /api/v1/auth/login` — form `x-www-form-urlencoded` com `username`
   (email) e `password` (padrão OAuth2 Password Bearer do FastAPI). Retorna
   `access_token` + `refresh_token`.
2. Use `Authorization: Bearer <access_token>` nos demais endpoints.
3. Quando o access token expirar, chame `POST /api/v1/auth/refresh` com
   `{"refresh_token": "..."}` para obter um novo par de tokens.
4. `GET /api/v1/auth/me` retorna os dados do usuário autenticado.

Exemplo com `curl`:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=recepcao@clinica.demo&password=Recepcao@123"

curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"
```

## Segurança — o que já está implementado

- Hash de senha com **Argon2** (via passlib), com fallback de verificação
  para bcrypt (hashes legados futuros).
- **JWT** com expiração configurável para access e refresh token,
  algoritmo configurável via `JWT_ALGORITHM`.
- **OAuth2 Password Bearer** padrão do FastAPI.
- **RBAC** explícito por endpoint (`require_roles`), com perfis do MVP
  reforçados em tempo de execução.
- Validação de entrada rigorosa via **Pydantic** (schemas dedicados de
  entrada/saída — nunca se expõe o model ORM diretamente).
- **Proteção contra enumeração de usuários**: mensagem de erro idêntica
  para "usuário não existe" e "senha incorreta", com hash *dummy* executado
  no caso de usuário inexistente para reduzir diferença de tempo de
  resposta.
- **Rate limiting** no endpoint de login (ver limitação abaixo).
- **CORS configurável por ambiente** (`CORS_ORIGINS`).
- **Segredos exclusivamente via variáveis de ambiente** — `SECRET_KEY`
  default inseguro é **rejeitado automaticamente** se `ENVIRONMENT=production`.
- **Logs sem dado sensível**: os handlers de erro nunca logam corpo de
  requisição, senha, token ou conteúdo clínico — apenas metadados
  (path, método, tipo de erro, status).
- Tratamento de erro padronizado, sem vazar stack trace/detalhes internos
  ao cliente em erros 500.

### Limitações conhecidas (documentadas de propósito)

- O rate limiter (`app/security/rate_limit.py`) guarda estado **em memória
  do processo**. Funciona corretamente com uma única instância/worker.
  Em produção com múltiplas réplicas, troque por um backend compartilhado
  (Redis, ex. via `slowapi` + Redis, ou rate limiting no API Gateway) — a
  troca foi isolada nesse módulo exatamente para não exigir mudanças nos
  routers.
- TLS não é implementado pela aplicação em si (é responsabilidade da
  infraestrutura/proxy reverso em produção — ex.: Nginx, load balancer).
- Auditoria de operações sensíveis (`app/audit/`) está reservada na
  estrutura, mas ainda não implementada — entra em fase posterior, junto
  com os módulos de prontuário/agendamento que ela precisa auditar.
- Política de retenção e exclusão de dados: a estrutura já favorece
  inativação lógica sobre exclusão física (ver `is_active` em `User`), mas
  a política formal de retenção precisa ser definida com apoio jurídico
  antes de produção.

## Migrações (Alembic)

```bash
# gerar uma nova migração a partir de mudanças nos models
alembic revision --autogenerate -m "descrição da mudança"

# aplicar migrações pendentes
alembic upgrade head

# reverter a última migração
alembic downgrade -1
```

`alembic/env.py` lê a URL do banco das `Settings` da aplicação (variáveis
de ambiente), não do `alembic.ini` — evita duas fontes de verdade
divergentes para credenciais de banco.

## Compatibilidade MySQL → PostgreSQL

Os models evitam tipos/dialects específicos do MySQL: enums são
persistidos como `String` (via `native_enum=False`, não `ENUM` nativo do
MySQL), UUIDs são `String(36)` gerados em Python (não `AUTO_INCREMENT`
nem tipo nativo de UUID), e timestamps usam `DateTime(timezone=True)`
padrão do SQLAlchemy. Trocar para PostgreSQL deve exigir apenas alterar
`DATABASE_URL` para `postgresql+psycopg://...` e revisar as migrações
Alembic geradas (o autogenerate pode precisar de pequenos ajustes de tipo,
mas nenhuma reescrita de model é esperada).
