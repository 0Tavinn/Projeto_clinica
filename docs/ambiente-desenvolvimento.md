# Ambiente de desenvolvimento do Lumina Odonto

Referência preparada em 24/11/2026 sobre o PR #18, commit
`f8f10c54a4a702b7d4feccbf5aeb98578db65909`, na branch
`feat/paralelismo-agendamento`. Os ajustes de execução desta entrega ainda
precisam de commit. O banco atende aos módulos do projeto.

## Uso diário de Paulo no Ubuntu WSL

```bash
cd /home/paulinho/Work/Projeto_clinica_clinical_2fa
python3 scripts/dev.py up
python3 scripts/dev.py status
python3 scripts/dev.py stop
```

Execute somente a operação desejada. O início constrói as imagens, valida o
volume e a revisão do banco e inicia API/frontend. O status consulta o banco a
partir da API e verifica HTTP. Um healthcheck verde isolado não valida o catálogo.

| Recurso | Referência local de Paulo |
| --- | --- |
| Projeto Compose principal | `lumina_pr18_tarcisio` |
| Interface | http://localhost:18088 |
| API e documentação | http://localhost:18089/docs |
| Banco local | `127.0.0.1:55438`, banco `lumina_pr18` |
| Volume persistente | `lumina_pr18_tarcisio_postgres_data` |
| Revisão Alembic | `a6e8f0b2c4d6` |
| PostgreSQL verificado | 16.15 |
| Credenciais | `.env` protegido e ignorado, sem exposição neste guia |
| Reuso do volume | `compose.local.yml` ignorado, com volume externo explícito |

O override local de Paulo tem somente este conteúdo, sem credenciais:

```yaml
volumes:
  postgres_data:
    external: true
    name: lumina_pr18_tarcisio_postgres_data
```

Preserve o arquivo .env atual junto desse override na recuperação local. Um
clone novo usa seu próprio volume pelo procedimento abaixo.

O nome histórico do projeto foi mantido para reaproveitar volume, rede e portas.
O código de Tarcísio de outra branch continua sujeito à integração e ao QA próprios.

O frontend usa `/api/v1` na mesma origem e o Nginx encaminha para a API.
Assim, seu build dispensa endereço particular do computador. A API continua
disponível diretamente na porta documentada.

## Novo colaborador

Pré-requisitos: Ubuntu/WSL, Git, Python 3.12 ou posterior para os helpers e
Docker com Compose v2. O backend roda em Python 3.12 dentro da imagem.

Após clonar a branch que contém estes arquivos, na raiz do clone:

```bash
python3 scripts/setup_dev.py
python3 scripts/dev.py init
python3 scripts/dev.py status
```

O setup cria `.env` com segredos aleatórios, permissão 600 e nome de projeto
exclusivo. Recusa sobrescrever configuração existente. As portas padrão são
8080 para a interface, 8000 para a API e 55432 para PostgreSQL. Se estiverem
ocupadas, escolha outras no setup:

```bash
python3 scripts/setup_dev.py --project lumina_dev_joao --frontend-port 18082 --api-port 18010 --db-port 55440
```

Use apenas um dos comandos de setup. O template `.env.example` também permite
configuração manual com segredos URL-safe. O helper recusa placeholders.

`init` é uma ação explícita apenas para banco vazio local. Executa a cadeia
Alembic até a revisão de referência e inicia os serviços. Recusa volume externo
e banco com tabelas. `up` reutiliza banco preparado e não aplica migrações.
Esquema sem origem conhecida ou revisão divergente exige reconciliação.
O SQL consolidado é uma alternativa apenas para banco vazio e não marca Alembic.
Não combine SQL e migrações nem use stamp como correção.

Carga fictícia opcional, somente no ambiente novo:

```bash
python3 scripts/dev.py seed-demo
```

O seed SQL recusa banco preenchido e não deve ser executado no banco de Paulo.
Credenciais fictícias e cenário da carga estão em
[banco-prontuarios-preparacao.md](banco-prontuarios-preparacao.md).

## Backup e restauração ensaiada

Feche conexões de escrita do DBeaver e combine uma pausa de edição. O comando
abaixo interrompe temporariamente API/frontend deste projeto, produz um dump
customizado e um manifesto e retoma os serviços que estavam ativos:

```bash
python3 scripts/dev.py backup
```

O último caminho impresso identifica o backup. Os arquivos ficam em
`.local/backups/<data-sufixo>/`, protegidos e ignorados. O manifesto registra
SHA-256, revisão, contagens e digest dos dados/sequências. Uma mudança detectada
durante a conferência exige repetir sem escritores. O dump é consistente por
snapshot do PostgreSQL, enquanto a comparação agregada requer essa pausa.

Para o backup efetivamente gerado nesta entrega:

```bash
python3 scripts/dev.py restore-test .local/backups/20261124-075346-eabb86/reference.dump
```

Para outro backup, substitua o argumento pelo caminho retornado pelo comando.
A restauração usa contêiner PostgreSQL 16 sem rede nem portas e sem volume do
usuário. Confere hash, dados, sequências, revisão e contagens e executa as
garantias SQL apenas no destino restaurado. Remove o contêiner e seu
armazenamento descartável. O manifesto registra o resultado. O arquivo de
papéis exclui senhas; senhas locais devem ser preservadas separadamente.

Retenha o backup anterior a cada alteração e somente descarte cópias após
revisão e autorização do responsável. Os helpers não apagam backups. As cópias
desta etapa são locais; uma cópia externa protegida ainda depende da operação
da equipe. Recuperar após perda de escritas posteriores exige conciliação.
O helper não restaura sobre banco persistente.

## Reprodução e proteções

```bash
python3 scripts/verify_dev.py
```

O executor exporta os arquivos da aplicação do HEAD e sobrepõe a lista explícita
de arquivos desta entrega. Exclui o ambiente Python local versionado na raiz e
configurações privadas. Cria projeto, banco e volume exclusivos, exercita início,
status, seed, recusa de reaplicação, backup/restauração e parada/reinício.
Uma revisão divergente é simulada apenas nesse banco QA. Logs ficam em
`.local/test-runs/`. Ao terminar remove somente os recursos exclusivos.

Os helpers serializam operações pelo volume e recusam outro contêiner ativo
que já o utilize. Use esses comandos para a operação diária. Comandos Docker
diretos podem contornar as proteções. Evite `down -v`, prune e remoção manual
de volumes. `stop` preserva contêineres, rede e dados.

## Ambientes históricos

| Projeto | Volume preservado | Portas antigas API/interface | Estado após organização |
| --- | --- | --- | --- |
| `lumina_execucao_20261029` | `lumina_execucao_20261029_postgres_data` | 18018 / 18090 | API/frontend parados; banco continuou parado |
| `lumina_s07_review_20261023` | `lumina_s07_docker_review_20261023` | 18008 / 18080 | API/frontend parados; banco continuou parado |
| `lumina_ui_20261111175549_186409` | `lumina_ui_20261111175549_186409_postgres_data` | 18009 / 18081 | API/frontend parados; banco continuou parado |

Os contêineres e configurações históricos foram preservados. Alguns bancos
antigos têm falha de bind e os overrides temporários de origem podem estar
ausentes. Sua recuperação exige conferir os mounts e configurações antes de
iniciar. O inventário sanitizado da organização está no diretório de evidências
local registrado no relatório.

## Como código e dados se relacionam

A branch seleciona o código. API e frontend são aplicações construídas desse
código. PostgreSQL executa o banco, cujo schema descreve tabelas e restrições.
O volume guarda os dados além da vida dos contêineres. Trocar branch ou construir
imagem não atualiza automaticamente o schema.

A integração futura deve escolher os commits de aplicação e conferir sua
compatibilidade com o mesmo banco de referência. Mudanças estruturais exigem
migração revisada, backup e restauração ensaiada e autorização do destino.
Testes e benchmarks usam recursos descartáveis separados.

A implementação própria de Tarcísio, o contrato clínico integrado e OpenCL na
Agenda seguem etapas posteriores. Esta entrega padroniza a infraestrutura da
base PR18. Os módulos não devem criar bancos persistentes independentes por
comodidade.
