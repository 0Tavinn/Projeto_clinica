# Guia de Desenvolvimento Colaborativo — Lumina Odonto

## Objetivo

Este guia prepara o trabalho local da equipe para a Sprint 6. O planejamento
em [sprint-06.md](sprint/sprint-06.md) ainda é uma proposta. A base atual tem
autenticação, usuários, pacientes, dentistas e Agenda integrados no código;
Prontuário e Evolução Clínica permanecem pendentes.

## Estrutura atual do repositório

```text
Projeto_clinica/
├── README.md
├── .gitignore
├── backend/
│   ├── app/                 # API FastAPI organizada por domínio
│   ├── alembic/             # Revisões parciais; requer baseline
│   ├── database/            # Schema completo e migração SQL da Agenda
│   ├── scripts/             # Seed local
│   ├── tests/               # Testes com SQLite em memória
│   ├── Dockerfile
│   ├── compose.yaml
│   ├── pyproject.toml
│   └── README.md
├── docs/
│   ├── development.md      # Guia principal para começar a desenvolver
│   ├── guides/             # Guias operacionais e de integração
│   ├── reference/          # Arquitetura, requisitos e regras de negócio
│   └── sprint/             # Planejamentos das sprints
└── frontend/                # React/Vite, cliente HTTP e testes de sessão
```

Os routers de autenticação, usuários, pacientes, dentistas e Agenda estão
registrados em `backend/app/main.py`. A tela rotulada como prontuário apresenta
somente dados cadastrais do paciente; ainda não há acesso a conteúdo clínico.

## Pré-requisitos

- Git;
- Python 3.11 ou 3.12;
- PostgreSQL disponível localmente;
- Node.js 22 ou superior e npm para o frontend e seus testes locais;
- Ambiente Linux/WSL ou equivalente compatível com o projeto;

As versões suportadas do Python e as dependências do back-end estão em
`backend/pyproject.toml`.

## Configuração do ambiente local

Execute os comandos a seguir a partir de `backend/`:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

No Windows PowerShell, use o mecanismo equivalente de ativação do ambiente
virtual. Não versione a pasta `.venv/`.

### Variáveis de ambiente

Crie o arquivo local a partir do exemplo:

```bash
cp .env.example .env
```

O `.env.example` lista as chaves necessárias para ambiente, banco de dados,
JWT, expiração de tokens, CORS e limite de tentativas de login. Ajuste somente
o `.env` local com valores próprios do ambiente.

Regras obrigatórias:

- nunca envie `.env`, senhas, tokens ou URLs com credenciais para o GitHub;
- nunca compartilhe valores sensíveis em issues, commits, Pull Requests ou
  prints públicos;
- mantenha `.env.example` sem credenciais reais;
- use uma chave JWT forte e exclusiva fora do ambiente local de demonstração.

## PostgreSQL local

O PostgreSQL é o banco oficial da API. A URL de conexão é definida pela variável
`DATABASE_URL` no `.env`, usando o driver Psycopg configurado no projeto.

O procedimento detalhado para banco novo, banco anterior à Agenda e banco já
atualizado está em [database-setup.md](guides/database-setup.md). `schema.sql` é para
**banco vazio**; a migração SQL da Agenda é para um banco PostgreSQL com o
esquema anterior verificado. Não execute nenhum deles em um banco compartilhado
sem conferir o estado e a autorização do responsável.

Fluxo local recomendado para uma instalação nova:

1. criar o usuário e o banco PostgreSQL locais;
2. preencher `DATABASE_URL` no `.env` sem expor a senha;
3. aplicar `database/schema.sql` com `ON_ERROR_STOP=1` no banco vazio;
4. executar o seed local somente quando a equipe decidir criar os dados de
   demonstração;
5. iniciar a API e o frontend em terminais separados.

O seed procura evitar duplicar seus registros de demonstração, mas altera o
banco. Não o execute em bases compartilhadas sem autorização explícita. As
consultas fictícias são criadas em data futura; ajuste os filtros da Agenda
para localizá-las.

## Executar API e frontend

Terminal 1, na pasta `backend/`, com o ambiente virtual ativado e o PostgreSQL
configurado:

```bash
uvicorn app.main:app --reload
```

Terminal 2, na pasta `frontend/`:

```bash
npm ci
npm run dev
```

O frontend usa `http://localhost:5173` e chama por padrão
`http://localhost:8000/api/v1`. Para outra API, configure `VITE_API_URL` no
ambiente do frontend com o prefixo `/api/v1`. Inclua a origem exata do frontend
em `CORS_ORIGINS` no `.env` da API. Nunca publique URLs com credenciais.

Endereços locais:

| Recurso | Endereço |
|---|---|
| API | `http://localhost:8000` |
| Frontend | `http://localhost:5173` |
| Swagger | `http://localhost:8000/docs` |
| Health check | `http://localhost:8000/health` |

Use o Swagger para validar os contratos antes de integrar telas. Para login, a
API recebe formulário OAuth2: e-mail no campo `username` e senha no campo
`password`.

## Executar os testes existentes

Na pasta `backend/`, com o ambiente virtual ativado:

```bash
python -m pytest
```

Os testes existentes usam SQLite em memória e não usam o PostgreSQL local.
Eles cobrem autenticação, hash de senha, limite de login, health check,
permissões, usuários, pacientes e Agenda. Eles não substituem um ensaio com
PostgreSQL e dados descartáveis.

Na pasta `frontend/`, execute os testes do cliente de sessão e o build:

```bash
npm test
npm run build
```

Antes de declarar uma alteração concluída, execute a suíte aplicável e registre
o resultado no Pull Request ou no relatório individual da Sprint.

### Validação desta preparação (13/10/2026)

| Comando ou ensaio | Resultado | Limite |
|---|---|---|
| `cd backend && .venv/bin/python -m pytest -q` | 47 testes passaram | SQLite em memória; não prova o banco da equipe. O `TestClient` travou no sandbox desta preparação e a suíte foi executada fora dele, ainda isolada do PostgreSQL por `tests/conftest.py`. |
| `cd frontend && npm test` | 1 arquivo de teste passou, cobrindo 3 cenários de restauração de sessão | Cliente HTTP simulado; não testa navegador ou API real. |
| `cd frontend && npm run build` | TypeScript e Vite concluíram | Compilação não substitui ensaio visual. |
| PostgreSQL 18 descartável em `/tmp`: `schema.sql` em banco vazio; esquema anterior mais migração SQL em outro banco | O esquema novo criou 8 tabelas; a migração completou, preencheu o período de consulta existente e rejeitou sobreposição | Bancos isolados de teste; nenhum banco da equipe foi alterado. |
| FastAPI/TestClient com PostgreSQL descartável | Login, criação/listagem de dentista, criação de paciente e agendamento, e listagem da Agenda passaram | Fluxo parcial, sem frontend em navegador, reinício da API, múltiplas clínicas ou dados existentes da equipe. |

Os clusters descartáveis foram encerrados e removidos. Há avisos de
depreciação de dependências na suíte da API; eles não causaram falhas. O
procedimento em banco compartilhado continua dependente da inspeção e
autorização descritas em [database-setup.md](guides/database-setup.md).

## Docker e Alembic nesta base

Docker e Alembic ainda não reproduzem todo o esquema PostgreSQL utilizado pela
Agenda e previsto para a Sprint 6.

- `backend/compose.yaml` ainda contém configuração antiga de MySQL;
- a API e `database/schema.sql` foram direcionados para PostgreSQL;
- as revisões Alembic cobrem apenas parte do `schema.sql` e não substituem o
  procedimento de banco descrito acima;
- não execute `alembic upgrade head` em um banco com dados para tentar
  reconciliar estruturas divergentes;
- não use o Compose atual como ambiente PostgreSQL da Sprint 6.

Para esta base, use o fluxo local `frontend → API → PostgreSQL`. A estratégia
de migrações para bancos existentes e o ambiente Docker precisam de revisão
técnica antes de serem apresentados como reproduzíveis.

## Organização de branches

Não há um padrão formal de branches documentado no repositório. Use o padrão
recomendado abaixo até que a equipe adote outro oficialmente:

| Prefixo | Uso |
|---|---|
| `feat/` | Nova funcionalidade |
| `fix/` | Correção de comportamento |
| `docs/` | Documentação |
| `chore/` | Manutenção, configuração ou ferramentas |

Exemplos:

```text
feat/api-listar-usuarios
fix/api-permissoes-pacientes
docs/guia-integracao-api
chore/docker-postgresql
```

Crie branches curtas, com objetivo único, a partir da branch definida pela
equipe. Não misture alterações de Docker, banco, front-end e regras de negócio
sem necessidade no mesmo Pull Request.

## Padrão de commits

Use commits pequenos, revisáveis e com escopo claro. Enquanto não houver uma
convenção oficial diferente, adote o padrão `tipo(escopo): resumo`.

Exemplos recomendados:

```text
feat(frontend): integrar login com API
feat(api): listar usuários da clínica
fix(api): ajustar permissões de pacientes
docs(sprint): adicionar planejamento da sprint 4
chore(docker): migrar ambiente para PostgreSQL
```

Evite mensagens vagas como `ajustes`, `teste` ou `mudanças`. Nunca inclua
segredos, dados de pacientes ou dumps de banco em commits.

## Processo recomendado para Pull Requests

1. atualize sua branch a partir da base definida pela equipe;
2. faça uma alteração com objetivo limitado;
3. execute os testes aplicáveis e revise o diff localmente;
4. descreva no Pull Request o objetivo, os arquivos afetados, como testar e os
   riscos conhecidos;
5. inclua prints ou evidências quando houver impacto visual ou integração;
6. solicite revisão de alguém responsável pelo domínio afetado;
7. corrija os comentários antes de mesclar;
8. mantenha o histórico sem commits de depuração ou arquivos locais.

Para mudanças no contrato da API, informe explicitamente o impacto esperado no
front-end. Para mudanças de banco, não mescle sem confirmar a estratégia de
schema e migração com a pessoa responsável pelo ambiente.

## Checklist antes de enviar uma alteração

- [ ] A alteração tem escopo único e está na branch correta.
- [ ] Arquivos locais, `.env`, credenciais, tokens e banco local não aparecem
      no diff.
- [ ] Os campos e permissões continuam coerentes com o contrato da API.
- [ ] Os testes aplicáveis foram executados e o resultado foi registrado.
- [ ] O Swagger e a documentação foram revisados quando uma rota mudou.
- [ ] A integração entre front-end, API e PostgreSQL foi validada quando
      aplicável.
- [ ] Mensagens de erro não expõem detalhes internos ou dados sensíveis.
- [ ] O Pull Request explica como revisar e testar a alteração.

## Evidências e relatórios da Sprint 4

O planejamento da Sprint solicita relatório individual, resultados de testes e
evidências de telas, Swagger, terminal ou PostgreSQL. Organize os materiais no
Drive usando a estrutura definida em `docs/sprint/sprint-04.md`:

```text
Sprint 04/
├── Relatórios Individuais/
├── Evidências/
└── Relatório Final/
```

Use o padrão sugerido `S04_NomeDoIntegrante_RelatorioIndividual` para o
relatório individual. Registre apenas dados de demonstração e jamais inclua
senhas, tokens, URLs com credenciais, dados reais de pacientes ou dumps de
banco nas evidências compartilhadas.

## Segurança e dados sensíveis

- O arquivo `.env` é local e deve permanecer ignorado pelo Git.
- Senhas devem ser tratadas apenas como entrada de formulário; não as registre
  em logs, testes de evidência ou documentação.
- Tokens JWT não devem ser inseridos em commits, screenshots públicos ou
  mensagens de Pull Request.
- Não envie bancos SQLite, dumps PostgreSQL ou dados de pacientes ao GitHub.
- Use contas e dados de demonstração somente em ambientes autorizados.
- Revise o diff antes de cada push para detectar arquivos acidentais.

## Escopo técnico imediato da Sprint 6

A base já contém autenticação, usuários, pacientes, dentistas e Agenda. O
terceiro módulo previsto é Prontuário e Evolução Clínica; o
[planejamento](sprint/sprint-06.md) ainda deve ser alinhado pela equipe e a
[revisão clínica](reference/clinical-records-review.md) registra decisões pendentes. O
frontend, a API e o PostgreSQL precisam ser ensaiados em conjunto antes da
demonstração. Docker e a estratégia de migrações para bancos existentes não
estão concluídos nesta base.
