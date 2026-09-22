# Dental Clinic API

API para gerenciamento de clínicas odontológicas, desenvolvida como projeto acadêmico da disciplina de Fábrica de Software.

A versão atual implementa a base funcional da Sprint 3: autenticação, perfis de acesso, cadastro de usuários, CRUD de pacientes e persistência em PostgreSQL.

> Este é um projeto acadêmico. Antes de qualquer uso com pacientes reais, a aplicação deve passar por avaliação de segurança, conformidade com a LGPD e validação jurídica.

## Funcionalidades implementadas

- Autenticação com OAuth2 Password Bearer e JWT.
- Tokens de acesso e atualização de sessão.
- Senhas protegidas com Argon2.
- Perfis de acesso:
  - `ADMINISTRATOR`;
  - `RECEPTIONIST`;
  - `DENTIST`.
- Cadastro de usuários protegido para administradores.
- CRUD completo de pacientes:
  - cadastrar;
  - listar;
  - consultar;
  - atualizar;
  - inativar.
- Persistência real em PostgreSQL.
- Documentação interativa pelo Swagger.
- Testes automatizados com SQLite em memória.

## Regras de acesso

| Funcionalidade | Administrador | Recepcionista | Dentista |
|---|---:|---:|---:|
| Login | Sim | Sim | Sim |
| Cadastro de usuários | Sim | Não | Não |
| Cadastrar paciente | Sim | Sim | Não |
| Consultar pacientes | Sim | Sim | Sim |
| Atualizar paciente | Sim | Sim | Não |
| Inativar paciente | Sim | Sim | Não |

O paciente não possui login nesta fase do projeto.

A exclusão de pacientes é lógica: o endpoint `DELETE` altera o campo `is_active` para `false`, preservando o histórico clínico para futuras etapas de prontuário e agendamento.

## Estrutura do projeto

```text
app/
  main.py                     # Inicialização do FastAPI e registro dos routers
  core/
    config.py                 # Configurações por variáveis de ambiente
    database.py               # Engine, sessão e Base do SQLAlchemy
  security/
    auth.py                   # JWT, login e usuário autenticado
    hashing.py                # Hash e validação de senhas com Argon2
    permissions.py            # Regras de acesso por perfil
    roles.py                  # Perfis da aplicação
    rate_limit.py             # Limite de tentativas de login
  users/
    models.py                 # Models Clinic e User
    schemas.py                # Schemas de autenticação e usuários
    repository.py             # Acesso a dados de usuários
    service.py                # Regras de autenticação e cadastro
    router.py                 # Endpoints de autenticação
    management_router.py      # Endpoint administrativo de usuários
  patients/
    models.py                 # Model Patient
    schemas.py                # Schemas do CRUD de pacientes
    repository.py             # Acesso a dados de pacientes
    service.py                # Regras do CRUD de pacientes
    router.py                 # Endpoints de pacientes
database/
  schema.sql                  # Estrutura oficial do banco PostgreSQL
scripts/
  seed.py                     # Criação da clínica e administrador iniciais
tests/
  ...                         # Testes automatizados
```

## Requisitos

- WSL com Ubuntu ou outro ambiente Linux compatível;
- Python 3.11 ou 3.12;
- PostgreSQL;
- Git.

O projeto foi validado com:

```text
Python 3.12.14
PostgreSQL 18
```

## Configuração do Python

Caso utilize `pyenv`:

```bash
pyenv install 3.12.14
```

```bash
pyenv local 3.12.14
```

Crie e ative o ambiente virtual:

```bash
python -m venv .venv
```

```bash
source .venv/bin/activate
```

Instale as dependências:

```bash
python -m pip install --upgrade pip
```

```bash
python -m pip install -e ".[dev]"
```

## Configuração do PostgreSQL

Inicie o serviço:

```bash
sudo service postgresql start
```

Se ainda não existir um banco local, crie o usuário e o banco:

```bash
sudo -u postgres psql
```

Dentro do PostgreSQL:

```sql
CREATE ROLE clinic_app
WITH LOGIN
PASSWORD 'SUA_SENHA_LOCAL';
```

```sql
CREATE DATABASE clinic_management
WITH
OWNER = clinic_app
ENCODING = 'UTF8';
```

Saia:

```sql
\q
```

Aplique a estrutura oficial:

```bash
psql -h 127.0.0.1 -p 5432 -U clinic_app -d clinic_management -W -f database/schema.sql
```

O banco será criado com as tabelas:

```text
appointments
audit_logs
clinical_evolutions
clinics
dentists
medical_records
patients
users
```

## Configuração do ambiente

Crie o arquivo local de variáveis:

```bash
cp .env.example .env
```

No arquivo `.env`, configure a URL do banco:

```env
DATABASE_URL=postgresql+psycopg://clinic_app:SUA_SENHA_LOCAL@127.0.0.1:5432/clinic_management
```

Se a senha possuir caracteres especiais, ela deve ser codificada na URL. Por exemplo, o caractere `@` deve ser substituído por `%40`.

Também defina uma chave JWT segura:

```env
SECRET_KEY=troque-por-uma-chave-local-segura
```

O arquivo `.env` não deve ser enviado ao GitHub.

## Criação dos dados iniciais

Com o banco criado e o ambiente virtual ativo, execute:

```bash
python -m scripts.seed
```

O script cria, quando ainda não existirem:

- uma clínica de demonstração;
- um administrador inicial.

Credenciais locais de demonstração:

| Perfil | Email | Senha |
|---|---|---|
| Administrador | `admin@clinica.demo` | `Admin@123` |

Troque essas credenciais antes de qualquer uso fora do ambiente acadêmico local.

## Executando a API

Com o ambiente virtual ativo:

```bash
uvicorn app.main:app --reload
```

A API ficará disponível em:

```text
http://localhost:8000
```

Documentação Swagger:

```text
http://localhost:8000/docs
```

Health check:

```text
GET http://localhost:8000/health
```

## Fluxo de demonstração pelo Swagger

1. Acesse `http://localhost:8000/docs`.
2. Clique em **Authorize**.
3. Faça login com:

```text
username: admin@clinica.demo
password: Admin@123
```

4. Use `POST /api/v1/users` para cadastrar recepcionistas e dentistas.
5. Use os endpoints de `Patients` para demonstrar o CRUD.
6. O Swagger armazena e envia o token JWT automaticamente após a autorização.

## Principais endpoints

### Autenticação

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/api/v1/auth/login` | Realiza login e retorna tokens JWT |
| `POST` | `/api/v1/auth/refresh` | Renova os tokens de sessão |
| `GET` | `/api/v1/auth/me` | Retorna o usuário autenticado |

### Usuários

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/api/v1/users` | Cadastra usuário da clínica do administrador autenticado |

### Pacientes

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/api/v1/patients` | Cadastra paciente |
| `GET` | `/api/v1/patients` | Lista pacientes ativos da clínica |
| `GET` | `/api/v1/patients/{patient_id}` | Consulta um paciente |
| `PATCH` | `/api/v1/patients/{patient_id}` | Atualiza paciente |
| `DELETE` | `/api/v1/patients/{patient_id}` | Inativa paciente |

## Testes automatizados

Execute:

```bash
python -m pytest
```

Resultado validado:

```text
23 passed
```

Os testes utilizam SQLite em memória e não alteram o banco PostgreSQL local.

## Validação da persistência no PostgreSQL

Para verificar os pacientes diretamente no banco:

```bash
psql -h 127.0.0.1 -p 5432 -U clinic_app -d clinic_management -W
```

Dentro do PostgreSQL:

```sql
SELECT
    id,
    full_name,
    cpf,
    medical_record_number,
    is_active,
    updated_at
FROM patients
ORDER BY id;
```

## Observação sobre Alembic e Docker

O arquivo de migração Alembic existente pertence à estrutura inicial baseada em MySQL. Não execute:

```bash
alembic upgrade head
```

na versão atual do projeto, pois o banco PostgreSQL já é criado a partir de `database/schema.sql`.

A execução local oficial desta fase utiliza WSL, PostgreSQL e Uvicorn. A configuração Docker será revisada em uma etapa posterior para refletir a arquitetura PostgreSQL atual.