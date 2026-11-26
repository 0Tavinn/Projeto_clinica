# Organização do ambiente de desenvolvimento e banco de referência

Data de execução: 24/11/2026. Ambiente Ubuntu WSL e Docker Desktop.
Checkout: `/home/paulinho/Work/Projeto_clinica_clinical_2fa`.
Branch: `feat/paralelismo-agendamento`.
HEAD antes/depois: `f8f10c54a4a702b7d4feccbf5aeb98578db65909`.
Estado inicial limpo, sem stage. Ao final há somente os arquivos desta entrega
modificados/novos, sem stage, commit ou publicação.

## Resultado operacional

O ambiente principal de desenvolvimento é o projeto Compose
`lumina_pr18_tarcisio`. O nome foi mantido para reaproveitar o volume e a rede.
Há apenas três contêineres em execução ao fim: banco, API e frontend desse
projeto. Os seis serviços antigos de API/frontend foram parados. Seus
contêineres, redes e volumes foram preservados.

Interface: http://localhost:18088. API: http://localhost:18089/docs.
PostgreSQL: `127.0.0.1:55438`, banco `lumina_pr18`, schema `public`.
Volume externo reutilizado: `lumina_pr18_tarcisio_postgres_data`.
Rede preservada: `lumina_pr18_tarcisio_default`.
Configuração operacional versionável: `compose.yml` e helpers em `scripts/`.
Credenciais preservadas em `.env` protegido; seleção do volume em
`compose.local.yml`. Ambos estão ignorados.

## Conferência do banco e preservação

Servidor PostgreSQL 16.15. Revisão Alembic confirmada por SQL:
`a6e8f0b2c4d6`. Dez tabelas de negócio e a tabela de controle Alembic.
A origem histórica informada foi provisionamento por Alembic em 22/11,
seed SQL fictício e cadastros pela aplicação. Nesta execução foram conferidos
catálogo, marcador da revisão e dados agregados. Nenhum DDL ou migração foi
aplicado ao banco persistente.

| Tabela | Quantidade antes/depois |
| --- | --- |
| clinics | 1 / 1 |
| users | 4 / 4 |
| dentists | 2 / 2 |
| patients | 3 / 3 |
| appointments | 3 / 3 |
| medical_records | 3 / 3 |
| clinical_evolutions | 2 / 2 |
| clinical_access_links | 2 / 2 |
| clinical_access_events | 3 / 3 |
| audit_logs | 1 / 1 |

Além das contagens, o digest integral do dump de dados e sequências foi
preservado, removendo da comparação somente os tokens aleatórios de proteção
do pg_dump.

Antes da adoção da configuração, o banco PR18 original foi iniciado e
copiado. O backup foi restaurado em PostgreSQL 16.15 descartável sem rede.
Dados, sequências, contagens e revisão coincidiram; as verificações SQL da
entrega PR18 passaram sobre a restauração.

A adoção do Compose versionável recriou somente os três contêineres PR18.
Foram preservados volume, rede, portas e credenciais. O banco reutilizou o
cluster existente. A configuração privada original em
`/home/paulinho/.local/share/lumina-pr18/` foi mantida.

## Backup e restauração efetivamente executados

Backup inicial protegido:

`/home/paulinho/.local/state/lumina-dev/20261124-074333/reference.dump`

SHA-256:
`28494af6b5cebeebd420b89b3f27f7b401939d4b96c9d154f20ad24338b0e506`.

O helper compartilhável foi também exercitado no banco de referência:

`.local/backups/20261124-075346-eabb86/reference.dump`

SHA-256:
`1385409420217a412888b0bc515e776fa58c446c683dbe210cec9e5c5f546048`.

Seu `manifest.json` registra `restore_tested: true`, revisão, contagens e digest
dos dados/sequências. `restore-checks.log` registra a execução das garantias SQL
no destino restaurado. Papéis sem senhas foram capturados separadamente.
Os arquivos com dados ficaram locais e protegidos.

A primeira comparação textual das constraints restauradas encontrou mudança
de representação de casts de arrays feita pelo PostgreSQL. Dados e sequências
já coincidiam. A validação foi concluída com o mesmo dado restaurado e com os
ensaios funcionais SQL, conforme o comportamento já documentado no pacote PR18.
As cópias de restauração foram removidas após os ensaios.

Não foi feita restauração sobre banco persistente. Os backups são locais;
cópia externa e recuperação com escritas posteriores ainda dependem de plano
operacional. Nenhum backup dos três bancos históricos foi declarado executado.

## Verificações desta tarefa

| Verificação | Resultado |
| --- | --- |
| Build API com PostgreSQL, pacote e README presentes | Passou |
| Build frontend por npm ci e npm run build | Passou |
| Conexão a partir da API e catálogo crítico PR18 | Passou |
| API /health e frontend nas portas principais | HTTP 200 |
| Login fictício e /auth/me pelo proxy da interface | HTTP 200, tokens somente em memória |
| Backup/restauração do banco de referência | Passou |
| Dados e sequências preservados após a organização | Passou |
| Segundo helper concorrente no mesmo volume | Recusado |
| Outro contêiner montando o mesmo volume | Recusado |
| init sobre volume externo de referência | Recusado |
| Configuração privada e backups ignorados pelo Git | Confirmado |
| Sintaxe Python e git diff --check | Passou |
| Diff de backend/app, Alembic, SQL e frontend/src | Vazio |
| Stage | Vazio |

A cópia limpa usou os arquivos da aplicação do HEAD com a sobreposição
explícita dos arquivos operacionais desta entrega. O executor
`python3 scripts/verify_dev.py` criou recursos próprios e concluiu 14 etapas:
recusa do template inseguro e da sobrescrita de configuração, init em banco
vazio, up, status, seed fictício, recusa de seed repetido e init em banco
preenchido, backup, restauração, stop, retomada, preparação de revisão inválida
no QA e recusa dessa origem pelo status.

A primeira tentativa da exportação encontrou um link absoluto no venv
historicamente versionado na raiz e parou antes de criar recursos Docker.
O executor foi ajustado para exportar somente os caminhos da aplicação e os
arquivos operacionais necessários. Duas rodadas completas subsequentes
passaram, a última incluindo o setup compartilhável.

Evidências da rodada final:
`.local/test-runs/lumina_devcheck_d43f2377f9eb/`.
Os logs de cada etapa e `result.json` ficaram locais. Contêineres, rede e volume
dessa rodada foram removidos ao final. Os contêineres de restauração e de
verificação de guarda também foram removidos.

## Inventário histórico preservado

| Projeto | Banco | Volume | API/interface | Estado final |
| --- | --- | --- | --- | --- |
| lumina_execucao_20261029 | clinic_management | lumina_execucao_20261029_postgres_data | 18018/18090 | Três serviços parados |
| lumina_s07_review_20261023 | clinic_management | lumina_s07_docker_review_20261023 | 18008/18080 | Três serviços parados |
| lumina_ui_20261111175549_186409 | lumina_interface_teste | lumina_ui_20261111175549_186409_postgres_data | 18009/18081 | Três serviços parados |

Os bancos antigos já estavam parados. Foram parados nesta tarefa apenas os
seis serviços de API/frontend que continuavam ativos. Nenhum dado foi fundido
ao banco principal. A origem de código dos ambientes antigos foi registrada
por imagem/configuração, sem atribuir commit apenas a partir de uma tag.

Inventário sanitizado antes/depois e verificações iniciais:
`/home/paulinho/.local/state/lumina-dev/20261124-074333/`.
Logs adicionais de build, backup e reprodução:
`/home/paulinho/.local/state/lumina-dev/`.

Imagens principais executadas após o build:

- PostgreSQL: `sha256:f4610795587492cd4fb887c2dc3de301b813278bb6f616992061141b5f15ac36`.
- API: `sha256:7c45c4dac8cdd6fac1feea341ab4a86850622cd6b623003ab156f014d3830eee`.
- Frontend: `sha256:59f9d41187e9cc539c7dc651ef3f52efc43dd0c2edb9c72f793dcfbf9e7a7c2a`.

As imagens da aplicação contêm a referência Git em label. O build também
inclui os arquivos operacionais locais ainda sem commit. As tags das imagens
base podem receber atualizações; os IDs acima identificam esta execução.

## Arquivos da entrega

Modificados:

- `.gitignore`;
- `README.md`;
- `backend/Dockerfile`.

Novos:

- `.env.example`;
- `compose.yml`;
- `backend/.dockerignore`;
- `backend/scripts/check_database.py`;
- `frontend/.dockerignore`;
- `frontend/Dockerfile`;
- `frontend/nginx.conf`;
- `scripts/setup_dev.py`;
- `scripts/dev_support.py`;
- `scripts/dev.py`;
- `scripts/dev_backup.py`;
- `scripts/verify_dev.py`;
- `docs/ambiente-desenvolvimento.md`;
- este relatório.

## Uso diário e próximas integrações

```bash
cd /home/paulinho/Work/Projeto_clinica_clinical_2fa
python3 scripts/dev.py up
python3 scripts/dev.py status
python3 scripts/dev.py stop
```

As instruções completas de clone, backup e restauração de teste estão em
[ambiente-desenvolvimento.md](../ambiente-desenvolvimento.md).

O banco de referência está pronto para desenvolvimento da base PR18.
A integração do backend corrigido de Tarcísio exige seu contrato e reteste
próprios. A aplicação de `tata2005-patch-1` não foi incorporada, e OpenCL na
Agenda continua planejado. Não houve aceite clínico integrado nesta tarefa.
Novas mudanças estruturais no banco persistente exigem avaliação e autorização
específicas. Testes futuros devem usar recursos descartáveis.

## Commit manual seletivo

O stage estava vazio ao terminar. Se aparecer conteúdo preparado por outra
tarefa, resolva sua separação antes de executar este bloco. Confira a branch
e os diffs e use somente os caminhos desta entrega:

```bash
cd /home/paulinho/Work/Projeto_clinica_clinical_2fa
git status --short --branch
git diff
git diff --cached
git add -- .gitignore README.md .env.example compose.yml \
  backend/Dockerfile backend/.dockerignore backend/scripts/check_database.py \
  frontend/Dockerfile frontend/.dockerignore frontend/nginx.conf \
  scripts/setup_dev.py scripts/dev_support.py scripts/dev.py \
  scripts/dev_backup.py scripts/verify_dev.py \
  docs/ambiente-desenvolvimento.md \
  docs/relatorios/2026-11-24-organizacao-ambiente-desenvolvimento.md
git diff --cached --check
git diff --cached --stat
git diff --cached
```

Depois de revisar o conteúdo preparado:

```bash
git commit -m "chore(dev): padronizar ambiente PostgreSQL de desenvolvimento"
```

Nenhum comando de publicação foi executado.
