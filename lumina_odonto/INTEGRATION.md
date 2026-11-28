# Ambiente de integração do prontuário corrigido

Esta entrega executa a API de `lumina_odonto/`, da branch
`fix/prontuario-correcoes-qa`. A base funcional corrigida é `94e8e22`;
a preparação de ambiente vem em commit próprio nessa mesma branch.
Ela permanece separada da entrega `feat/paralelismo-agendamento`.
Não representa uma versão integrada das duas APIs ou aceite da interface.

## Iniciar em clone da branch

Pré-requisitos: Ubuntu/WSL, Git, Python 3.12 ou posterior para o helper,
Docker Desktop/Engine com Compose disponível. Python e OpenCL da API são
instalados dentro da imagem; não é necessário instalar esses pacotes no host.

Da raiz do repositório, na branch correta:

```bash
git branch --show-current
cd lumina_odonto
python3 scripts/integration.py setup
python3 scripts/integration.py up
python3 scripts/integration.py seed
python3 scripts/integration.py status
```

`setup` cria `.env.integration` com permissão 600 e segredos aleatórios.
Não sobrescreve configuração existente. `integration.env.example` descreve
as opções sem conter senhas reais. `up` constrói a API desta pasta e cria
somente o projeto `lumina_prontuario_integracao`, com volume e rede próprios.
`seed` é opcional e permitido apenas no banco novo sem cadastros; a segunda
execução falha sem sobrescrever dados. Nunca copie `.env` da Agenda.

Para outro nome/portas, escolha antes do primeiro setup:

```bash
python3 scripts/integration.py setup --project lumina_prontuario_otavio --api-port 18101 --db-port 55451
```

Use apenas uma das alternativas de setup. Em uma configuração já criada,
execute diretamente `up` e `status`. Não rode novamente `setup` ou `seed`
como procedimento cotidiano e não troque a senha do arquivo após criar o volume.

## Endereços e dados fictícios

| Recurso | Padrão local |
| --- | --- |
| Swagger da API corrigida | http://localhost:18100/docs |
| OpenAPI | http://localhost:18100/openapi.json |
| Saúde da API/banco | http://localhost:18100/health |
| Base para o frontend | http://localhost:18100/api/v1 |
| PostgreSQL | 127.0.0.1:55450, banco lumina_prontuario_integracao |
| Volume | lumina_prontuario_integracao_integration_data |

As portas são locais ao computador de cada colaborador. O ambiente não publica
uma interface de usuário; `/docs` é a documentação interativa da API.
A interface da Agenda em `18088` não foi convertida em interface deste backend.

| Perfil fictício | E-mail | Senha de entrada | Senha clínica |
| --- | --- | --- | --- |
| Administrador | admin.demo@example.com | DemoLumina2026! | Não utiliza |
| Dentista | dentista.demo@example.com | DemoLumina2026! | ClinicaDemo2026! |

A carga contém um paciente vinculado, um vínculo revogado e um paciente sem
vínculo, incluindo prontuário vazio e evoluções de demonstração. Use os IDs
retornados pelas rotas; não presuma que `user_id` e `dentist_id` são iguais.
O seed não cria conta de recepção. Não usar dados de pacientes reais neste ambiente.

## Contrato para Otávio e Caio

O guia detalhado é [FRONTEND.md](FRONTEND.md), com exemplos nos documentos
[de autenticação](docs/frontend/authentication-and-search.md),
[de evoluções](docs/frontend/records-and-evolutions.md) e
[de pacientes e vínculos](docs/frontend/clinical-patients-and-links.md).

1. Login JSON em `POST /api/v1/auth/login` com `email` e `password`.
2. Usar `access_token` nas rotas administrativas e de cadastro.
3. Dentista envia sua senha clínica em `POST /api/v1/auth/clinical-unlock`.
4. Usar `clinical_token` em `/clinical/patients`, prontuários, evoluções e busca.
5. Atualizar e finalizar evolução enviando a `version` lida; tratar conflito 409.
6. Admin gerencia vínculos em `POST /api/v1/admin/access` e consulta
   `GET /api/v1/access-links`. A revogação não apaga histórico.

O frontend precisa implementar esses contratos antes de apontar seu cliente
para a nova base. Não basta trocar a URL do cliente antigo: login, cancelamento,
respostas e operações de Agenda têm diferenças que ainda exigem integração.
A conclusão pelo dentista da branch de Agenda não foi portada por esta preparação.
O OpenCL desta API pertence à busca clínica, não ao comparador de horários.

A configuração CORS inicial permite origens locais nas portas 5173 e 3000.
Se a interface usar outra origem, acrescente-a explicitamente em
`CORS_ORIGINS` de `.env.integration` e execute `up`. Nunca coloque segredo JWT
ou senha de PostgreSQL no frontend. Swagger usa JSON e não exige configurar CORS.

## Banco, preservação e operação

O `sql/schema.sql` desta API é idêntico ao esquema preparado no PR18.
O PostgreSQL executa esse SQL somente no primeiro início de um volume vazio.
Este caminho não aplica migrações, não copia dados existentes e não cria
`alembic_version`: não usar stamp para simular que a cadeia Alembic foi executada.
O banco diário da Agenda permanece em `lumina_pr18`/porta 55438 e não é o alvo
deste Compose. O nome deste candidato não indica um novo banco principal.

Para parar preservando dados:

```bash
python3 scripts/integration.py stop
```

Para retomar, execute `up` e `status`. O helper não contém comando de remoção,
não apaga volumes e recusa objetos sem propriedade reconhecida. Não use
`down -v`, prune ou cópia do schema sobre banco existente. Um catálogo divergente
requer avaliação do DBA. Esta configuração não é migração nem configuração de produção.

## Roteiro mínimo do aceite pela interface

Login administrativo; consulta de vínculos; login do dentista; desbloqueio
clínico; listagem dos pacientes autorizados; prontuário vazio; criação/edição
com versão; conflito de duas abas; finalização; busca CPU/OpenCL; revogação e
remoção do conteúdo da tela; reativação; privacidade de rascunhos e isolamento
entre clínicas. Registrar branch/commit, dados fictícios, passos, esperado,
obtido e evidências. Testes históricos de backend não substituem esse aceite.

Ainda há lacunas documentadas para recuperação clínica administrativa e impressão
individual/identificação histórica do autor. Não anunciar essas telas como integradas.

## Sessão para integrar Vínculos e Prontuários

O [contrato compartilhado de sessão](docs/frontend/shared-session.md) descreve
o segundo login temporário, tokens separados do legado, `expires_in`,
POST `/api/v1/auth/logout` e POST `/api/v1/auth/clinical-lock`.
Após atualizar a branch, reconstruir a API com `python3 scripts/integration.py up`.
O seed é somente para banco novo; não reaplicar em banco existente.
