# Lumina Odonto — API REST Python + PostgreSQL + OpenCL

Backend orientado à integração com frontend, com documentação Swagger/OpenAPI em `/docs` e contrato JSON em `/openapi.json`.

## Execução local em ambiente **de desenvolvimento descartável**

```bash
cp .env.example .env
# Altere JWT_SECRET para uma chave longa e aleatória.
docker compose up --build -d
# Somente em banco recém-criado e descartável:
docker compose exec -T db psql -U lumina -d lumina -v ON_ERROR_STOP=1 < sql/seed_demo.sql
```

Acesse `http://localhost:8000/docs`. A configuração do Docker utiliza `db` como hostname do PostgreSQL. Fora do Docker, utilize `localhost` e ajuste `DATABASE_URL`. A criação inicial das tabelas pelo `schema.sql` acontece somente quando o volume PostgreSQL está vazio. Não execute `schema.sql` nem `seed_demo.sql` em banco existente.

**Credenciais apenas fictícias para desenvolvimento** (do `seed_demo.sql`): `admin.demo@example.com` ou `dentista.demo@example.com` com `DemoLumina2026!`; senha clínica do dentista `ClinicaDemo2026!`. Remova essas contas antes de qualquer implantação real.

## Endpoints (prefixo `/api/v1`)

| Área | Operações | Autorização |
|---|---|---|
| Autenticação | `POST /auth/login`, `GET /auth/me`, `POST /auth/clinical-unlock`, `POST /auth/reset-clinical-password` | Sessão; desbloqueio clínico separado |
| Clínicas | `GET /clinics/me`, `PATCH /clinics/me` | Leitura autenticada; alteração admin |
| Usuários | `GET /users`, `GET /users/{id}`, `POST /users`, `PATCH /users/{id}`, `DELETE /users/{id}` (desativação) | Admin |
| Dentistas | `GET /dentists`, `GET /dentists/{id}`, `POST /dentists`, `PATCH /dentists/{id}` | Leitura autenticada; escrita admin |
| Pacientes | `GET /patients`, `GET /patients/{id}`, `POST /patients`, `PATCH /patients/{id}`, `DELETE /patients/{id}` (desativação) | Recepção/admin; desativação admin |
| Agenda | `GET /appointments`, `GET /appointments/{id}`, `POST /appointments`, `PATCH /appointments/{id}`, `DELETE /appointments/{id}` (cancelamento) | Recepção/admin; dentista lê sua agenda |
| Prontuários | `GET /patients/{id}/record`, `GET /patients/{id}/record/summary`, `PATCH /patients/{id}/record` | Dentista com token clínico e vínculo ativo |
| Evoluções | `GET /patients/{id}/evolutions`, `GET /evolutions/{id}`, `POST /evolutions`, `PATCH /evolutions/{id}`, `POST /evolutions/{id}/finalize` | Dentista autorizado; somente autor edita rascunho |
| Acesso clínico | `POST /admin/access`, `GET /access-links`, `GET /access-events` | Admin |
| Auditoria | `GET /audit-logs` | Admin |
| Pesquisa | `GET /clinical/search?patient_id=1&q=...&engine_name=auto` | Dentista com token clínico |
| Senhas | `POST /admin/users/{id}/reset-login-password` | Admin |

**Exclusão física não é oferecida** para registros clínicos, eventos, auditoria ou vínculos, para preservar o histórico. Pacientes e usuários são desativados; agendamentos são cancelados. Os eventos de acesso são imutáveis por gatilho PostgreSQL. Paciente e prontuário são criados na mesma transação; agendamento, concessão/reativação de vínculo e evento também.

### Fluxo para o frontend

1. Login: `POST /api/v1/auth/login` com `{ "email": "...", "password": "..." }`.
2. Enviar `Authorization: Bearer <access_token>` para as rotas administrativas e de recepção.
3. Dentista faz `POST /api/v1/auth/clinical-unlock` com `{ "password": "..." }`, usando token de acesso.
4. Enviar `Authorization: Bearer <clinical_token>` nas rotas de prontuário, evoluções e busca.
5. Para atualizar/finalizar evolução, enviar o campo `version` recebido na leitura; uma versão antiga retorna HTTP 409.

## OpenCL

A pesquisa seleciona os candidatos autorizados no PostgreSQL **antes** de transferir descrições ao motor de busca. O parâmetro `engine_name=auto` tenta OpenCL e utiliza CPU quando o runtime não está disponível; `cpu` força busca sequencial; `opencl` exige OpenCL e devolve HTTP 503 se indisponível. O Dockerfile instala POCL para OpenCL via CPU; aceleração em GPU física requer drivers e exposição explícita do dispositivo. O processamento é literal, insensível a maiúsculas e acentos. A pesquisa exige `patient_id`, processa até 1.000 candidatos por página e retorna `next_offset` quando há mais candidatos. `total` conta os resultados da página. O orçamento de bytes retorna 413; termo vazio após normalização retorna 422 em todos os motores. A autorização é conferida antes e depois do processamento.

## Estrutura

- `app/main.py`: autenticação, permissões clínicas, transações, evoluções, busca e acesso.
- `app/crud.py`: endpoints CRUD, filtros por clínica, validações e desativação lógica.
- `app/opencl_search.py`, `app/kernels/contains.cl`: busca CPU/OpenCL.
- `sql/schema.sql`: esquema PostgreSQL 16 fornecido.
- `sql/check_clinical_schema.sql`: verificações SQL de restrições.
- `sql/seed_demo.sql`: dados de demonstração fictícios.
- `tests/`: verificações unitárias.

## Importante para implantação

O pacote está **candidato a reteste de QA**, mas **não está homologado para produção**. Não foram fornecidas as revisões originais Alembic, portanto não foram inventadas migrações históricas. O `verify_disposable.sh` original exige esses arquivos para executar a suíte completa. São necessários testes reais de concorrência, segurança, permissões e LGPD, estratégia de backup/restauração, migrações versionadas e revisão do uso de dados clínicos antes de usar pacientes reais. A aplicação não cria ou altera tabelas automaticamente em runtime.

## Reteste

Execute `docker compose config` após copiar `.env.example`. Para testes: `docker compose run --rm api python -m pytest -q` (imagem inclui dependências de teste). Consulte `QA_CORRECOES.md`.

## Política de logs da API — correção N05-LOG

Ao importar app.main:app, a API instala a política de app/logging_policy.py.
Ela se aplica ao CMD original da imagem e à execução uvicorn app.main:app,
sem exigir configuração externa para remover querystrings.

O access log mantém método, rota estática e status HTTP. Descarta valores
da querystring, parâmetros de caminho, endereço do cliente e mensagens
originais. Uma rota desconhecida aparece como [unmatched]. O log do servidor
mantém eventos operacionais e o nível de gravidade, mas omite mensagens
arbitrárias e traceback, que podem carregar termos de busca ou dados SQL.
Isso reduz o detalhe disponível no stdout/stderr; investigar falhas exige
reprodução controlada com dados fictícios, sem habilitar logs brutos em
ambiente clínico.

Nenhuma entrada clínica, corpo, token ou senha é adicionada aos logs por
esta política. O contrato da busca e as respostas autorizadas permanecem
iguais. Uma resposta200 pode conter conteúdo clínico autorizado.
Os handlers422 continuam sanitizando erros de entrada.

A política cobre os loggers Uvicorn configurados no pacote. Proxy,
coletores externos, futuras rotas que imprimam dados e configurações de
logging externas posteriores à importação exigem revisão própria.
Não habilite SQL echo, dump de headers/corpos ou logs brutos da URL.
