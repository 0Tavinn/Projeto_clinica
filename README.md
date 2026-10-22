# Lumina Odonto

Sistema de gestão para clínica odontológica desenvolvido no contexto das
disciplinas de Fábrica de Software e Extensão. O objetivo é formar uma base
segura e organizada para a equipe administrar o acesso ao sistema e os
cadastros de pacientes.

Este README descreve somente o que está disponível no repositório nesta etapa.
Funcionalidades planejadas não devem ser tratadas como concluídas.

## Estado atual

A API oferece autenticação, controle de perfis, cadastro de usuários da equipe,
gestão de pacientes, dentistas, agenda e prontuário. O front-end React também
está versionado e pode ser executado por Docker Compose.

O fluxo recomendado para desenvolvimento integrado é o ambiente containerizado
descrito na seção [Executar com Docker Compose](#executar-com-docker-compose).

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
| Cadastrar e editar pacientes | Sim | Sim | Sim |
| Inativar pacientes | Sim | Sim | Não |

O paciente não possui acesso ao sistema. A exclusão pela API é lógica: o
registro recebe `is_active = false` e não é apagado fisicamente.

## Próximos passos e fora do escopo atual

- IA e métricas financeiras permanecem fora do escopo atual.
- O Compose local inicializa o PostgreSQL a partir de `backend/database/schema.sql`.
  As migrações Alembic ainda devem ser alinhadas antes de serem usadas como
  mecanismo oficial de evolução do banco.

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
frontend/                  # Aplicação React/Vite e imagem Nginx
README.md                    # Visão geral do projeto
```

## Documentação técnica

- [Contrato de integração da API](docs/api-integration.md)
- [Guia de desenvolvimento local](docs/development.md)
- [Arquitetura](docs/architecture.md)
- [Banco de dados](docs/database.md)
- [Planejamento da Sprint 4](docs/sprint/sprint-04.md)

## Executar com Docker Compose

### Serviços

O Compose na raiz do projeto orquestra:

| Serviço | Função | Porta local |
|---|---|---:|
| `db` | PostgreSQL 16 com volume persistente | não publicada |
| `api` | API FastAPI/Uvicorn | `8000` |
| `frontend` | Build React servido pelo Nginx | `8080` |

Todos os serviços ficam na rede interna `lumina_odonto_network`. A API acessa o
banco pelo hostname `db`; o navegador acessa a API por `localhost:8000`.

### Primeiro uso

Na raiz do repositório:

```bash
cp .env.example .env
```

Edite `.env` e substitua pelo menos `POSTGRES_PASSWORD` e `SECRET_KEY`. Para
gerar uma chave JWT localmente:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Suba os serviços:

```bash
docker compose up --build
```

Acesse:

- Frontend: <http://localhost:8080>
- API: <http://localhost:8000>
- Swagger: <http://localhost:8000/docs>
- Health da API: <http://localhost:8000/health>
- Health do frontend: <http://localhost:8080/health>

O banco executa `backend/database/schema.sql` somente na primeira inicialização
do volume `lumina_odonto_postgres_data`. Para acompanhar o estado dos serviços:

```bash
docker compose ps
docker compose logs -f api
```

Para apagar também os dados persistidos e recriar o banco do zero:

```bash
docker compose down -v
```

Esse comando é destrutivo para os dados locais do PostgreSQL. Não o execute em
ambientes compartilhados ou de produção.

### Variáveis de ambiente

O arquivo `.env.example` documenta as variáveis usadas pelo Compose. Segredos
reais devem ser fornecidos pelo gerenciador de secrets da plataforma de nuvem,
não por commits, imagens Docker ou arquivos `.env`.

`VITE_API_URL` é incorporada no build do frontend, pois aplicações Vite são
estáticas após a compilação. Em produção, defina essa variável com a URL
pública da API antes de executar o build da imagem:

```bash
VITE_API_URL=https://api.exemplo.com/api/v1 docker compose build frontend
```

### Deploy em nuvem

- **API e banco:** use a imagem de `backend/Dockerfile` em ECS, EKS, Render,
  Railway ou serviço equivalente. Configure `DATABASE_URL` e os demais segredos
  pela plataforma. Em produção, prefira PostgreSQL gerenciado.
- **Frontend:** publique a imagem de `frontend/Dockerfile` em um serviço de
  container ou use o diretório `frontend/` em Vercel. O valor de
  `VITE_API_URL` deve apontar para a API pública no momento do build.
- **Healthchecks:** use `/health` da API como readiness/liveness e `/health` do
  frontend para verificar o Nginx.
- **Persistência:** o volume local é adequado para desenvolvimento. Em nuvem,
  use o armazenamento persistente/serviço gerenciado da plataforma; não
  dependa de filesystem efêmero do container.
- **Migrações:** não execute `alembic upgrade head` automaticamente neste
  Compose, pois Alembic ainda não está alinhado ao schema PostgreSQL atual.

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
