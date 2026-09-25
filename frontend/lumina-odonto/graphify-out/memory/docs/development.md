# Guia de Desenvolvimento Colaborativo — Lumina Odonto

## Objetivo

Este guia descreve como a equipe deve preparar, executar e colaborar no projeto
Lumina Odonto durante a Sprint 4. Ele registra o estado atual do repositório e
separa o fluxo local obrigatório do trabalho de infraestrutura que ainda está
pendente.

## Estrutura atual do repositório

```text
Projeto_clinica/
├── README.md
├── .gitignore
├── backend/
│   ├── app/                 # API FastAPI organizada por domínio
│   ├── alembic/             # Migrações antigas; requer alinhamento
│   ├── database/schema.sql  # Estrutura PostgreSQL de referência
│   ├── scripts/             # Seed local
│   ├── tests/               # Testes com SQLite em memória
│   ├── Dockerfile
│   ├── compose.yaml
│   ├── pyproject.toml
│   └── README.md
├── docs/
│   └── sprint/sprint-04.md
└── frontend/                # Reservado para a interface web
```

No estado atual, não há código de front-end versionado dentro de `frontend/`.
O back-end contém os módulos `core`, `security`, `common`, `users` e
`patients`. As entidades de agenda, prontuário, evoluções, auditoria e IA ainda
não possuem implementação de API.

## Pré-requisitos

- Git;
- Python 3.11 ou 3.12;
- PostgreSQL disponível localmente;
- Ambiente Linux/WSL ou equivalente compatível com o projeto;
- Opcionalmente, Docker Desktop com integração WSL habilitada para o trabalho
  futuro de containerização.

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

O arquivo `backend/database/schema.sql` cria a estrutura atual do banco. Ele
deve ser aplicado somente em um banco novo ou em um ambiente autorizado pela
equipe, pois executa DDL. Antes de aplicá-lo, confirme o ambiente e faça backup
quando houver dados relevantes.

Fluxo local recomendado para uma instalação nova:

1. criar o usuário e o banco PostgreSQL locais;
2. preencher `DATABASE_URL` no `.env` sem expor a senha;
3. aplicar `database/schema.sql` no banco autorizado;
4. executar o seed local somente quando a equipe decidir criar os dados de
   demonstração;
5. iniciar a API e validar o Swagger.

O seed é idempotente para a clínica e o administrador de demonstração, mas ele
altera dados. Não o execute em bases compartilhadas sem autorização explícita.

## Executar a API e acessar o Swagger

Com o ambiente virtual ativado e o PostgreSQL configurado:

```bash
uvicorn app.main:app --reload
```

Endereços locais:

| Recurso | Endereço |
|---|---|
| API | `http://localhost:8000` |
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
Eles cobrem autenticação, hash de senha, rate limit, health check, permissões
básicas e um fluxo de CRUD de pacientes. Eles não substituem testes de
integração com PostgreSQL nem a validação do front-end.

Antes de declarar uma alteração concluída, execute a suíte aplicável e registre
o resultado no Pull Request ou no relatório individual da Sprint.

## Docker e Alembic durante a Sprint 4

Docker e Alembic requerem ajustes e não são a fonte de verdade para validar o
fluxo local atual.

- `backend/compose.yaml` ainda contém configuração antiga de MySQL;
- a API e `database/schema.sql` foram direcionados para PostgreSQL;
- a migração Alembic atual não corresponde ao schema PostgreSQL nem aos models
  atuais;
- não execute `alembic upgrade head` no estado atual;
- não use o Compose atual como caminho de validação da Sprint 4.

Primeiro valide localmente o fluxo `front-end → API → PostgreSQL`. Depois,
trate a atualização de Docker e a estratégia de migrações em branch e Pull
Request separados, com revisão técnica. O Docker não deve bloquear a conclusão
do fluxo funcional da Sprint 4.

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

## Escopo técnico imediato da Sprint 4

O objetivo imediato é validar o fluxo completo de login, cadastro de equipe e
gestão de pacientes entre front-end, API e PostgreSQL. As integrações de IA,
agenda, prontuário completo, Docker final, Alembic alinhado e infraestrutura de
produção permanecem como trabalho posterior ou paralelo, sem bloquear essa
validação local.
