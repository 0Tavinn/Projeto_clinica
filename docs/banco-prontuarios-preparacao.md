# Banco de prontuários — preparação para revisão

Entrega técnica para Tarcísio, preparada em 18/11/2026. O esquema e os ensaios do banco funcionam sem iniciar a API, o frontend ou OpenCL. Nenhum banco ou volume preexistente foi migrado, apagado ou recriado.

## Linhagem

Base: branch `feat/clinical-records-2fa`, commit `b97f42479ff76001f1be38def489d482a807967f`. Preparação técnica na branch `feat/sistema-prontuarios`.

Cadeia preservada:

```text
50d77a928a7c -> 7a1d9e3b4c5d -> 8c2f4a1b6d7e -> 9d3e5f7a1b2c -> a6e8f0b2c4d6
```

As quatro revisões publicadas não foram modificadas. A nova revisão incremental é `a6e8f0b2c4d6_unify_clinical_access_schema.py`. O `env.py` passou a registrar também os modelos de prontuário e seus vínculos.

## Executar a verificação completa

Pré-requisitos: Bash no Linux/WSL e Docker acessível. A primeira execução precisa baixar as imagens/dependências se ainda não estiverem locais. A imagem mínima de migração instala apenas Alembic, SQLAlchemy, psycopg e pydantic-settings; não instala API ou OpenCL.

Na raiz do clone:

```bash
bash backend/database/verify_disposable.sh
```

Neste checkout Windows/Ubuntu:

```powershell
wsl.exe -d Ubuntu -- bash -lc 'cd /home/paulinho/Work/Projeto_clinica_clinical_2fa && bash backend/database/verify_disposable.sh'
```

O runner constrói `lumina-db-migrations:local` a partir de `backend/database/Dockerfile.migrations` somente se a imagem ainda não existir. A imagem permanece local para reutilização. Para reconstruí-la após alterar suas dependências:

```bash
docker build -f backend/database/Dockerfile.migrations -t lumina-db-migrations:local backend/database
```

É possível usar outra imagem já instalada com Alembic e as dependências mínimas:

```bash
DB_MIGRATION_IMAGE=nome-da-imagem:tag bash backend/database/verify_disposable.sh
```

O PostgreSQL padrão é `postgres:16-alpine`; `DB_POSTGRES_IMAGE` permite substituir a imagem. O ensaio foi executado com PostgreSQL 16.15.

Cada rodada cria rede, contêiner e bancos próprios, com nomes exclusivos. Não publica portas, não usa volumes e não consulta a configuração de bancos do host. O checkout é montado somente para leitura no contêiner de migração. Ao terminar ou falhar, o runner remove exclusivamente seus contêineres, rede e diretório temporário. Recursos de outros ambientes são preservados.

## O que o ensaio comprova

1. Cadeia Alembic completa em banco vazio.
2. Reversão da revisão nova até B e nova atualização, somente em banco descartável vazio.
3. Execução de `schema.sql` em outro banco vazio.
4. Comparação integral por `pg_dump --schema-only`: SQL e Alembic são idênticos, incluindo tipos, defaults, sequências, nomes de constraints, índices, funções e triggers. A única exclusão é a tabela de controle `alembic_version`.
5. Atualização de B com pacientes, consulta, prontuário e evolução finalizada fictícios. Conteúdo e data de finalização são preservados; prontuários ausentes são criados; consultas antigas não concedem vínculos.
6. Rejeição de evolução legada com finalização incoerente e de agenda ativa sobreposta. A restrição correta deve falhar, a revisão deve continuar em B e nenhuma coluna parcialmente migrada pode permanecer.
7. Unicidade de prontuário, versões positivas, descrição não vazia (incluindo tabulações e quebras de linha), coerência de finalização e evolução sem consulta.
8. Período calculado por trigger, consultas adjacentes permitidas e sobreposição ativa recusada por exclusão GiST.
9. Vínculo único, trilha de concessão/revogação/reativação, idempotência da origem consulta, versão única por evento e snapshot histórico preservado.
10. Recusa de alteração/exclusão de eventos e exclusão de origens ou vínculos com histórico.
11. Carga demonstrativa válida e recusa de reaplicação em banco preenchido.
12. Persistência após reinício do PostgreSQL e backup/restauração fictícios. Dumps de dados e sequências são comparados integralmente antes/depois; todas as garantias SQL são exercitadas novamente no banco restaurado.

O backup é restaurado com `pg_restore --exit-on-error`. O PostgreSQL pode reescrever a representação textual de casts em CHECKs ao restaurar; a comparação de backup usa conteúdo/sequências e verificações funcionais das garantias. A comparação canônica SQL versus Alembic compara a estrutura integralmente.

A saída final esperada é:

```text
OK: reinício e restauração preservaram dados integralmente; garantias SQL verificadas na restauração.
OK: todas as verificações passaram; removendo somente recursos descartáveis próprios.
```

## Revisar dados fictícios no DBeaver

O runner remove seus bancos ao terminar. Para uma demonstração separada, crie outro PostgreSQL descartável. O nome abaixo deve estar livre; não remova um contêiner existente para reutilizá-lo.

Na raiz do clone, no Bash/WSL:

```bash
docker run --rm -d --name lumina-tarcisio-demo \
  -e POSTGRES_PASSWORD=demo_only_change_me \
  -e POSTGRES_DB=lumina_demo \
  -p 127.0.0.1:55438:5432 postgres:16-alpine

for attempt in {1..30}; do
  docker exec lumina-tarcisio-demo pg_isready -h 127.0.0.1 -U postgres -d lumina_demo && break
  sleep 1
done

docker exec -i lumina-tarcisio-demo psql -X -U postgres -d lumina_demo \
  -v ON_ERROR_STOP=1 < backend/database/schema.sql

docker exec -i lumina-tarcisio-demo psql -X -U postgres -d lumina_demo \
  -v ON_ERROR_STOP=1 < backend/database/seed_demo.sql
```

Conexão: host `127.0.0.1`, porta `55438`, banco `lumina_demo`, usuário `postgres`, senha fictícia `demo_only_change_me`.

O contêiner usa armazenamento efêmero próprio. Reiniciá-lo preserva os dados; removê-lo encerra a demonstração e elimina esses dados:

```bash
docker restart lumina-tarcisio-demo
# Ao encerrar esta demonstração específica:
docker rm -f lumina-tarcisio-demo
```

Não se usa `docker compose down -v` nem remoção ampla de recursos.

## Carga demonstrativa SQL

`backend/database/seed_demo.sql` é independente dos modelos e do seed Python da aplicação. Recusa banco com cadastros existentes e nunca sobrescreve senhas. Não combine as duas cargas no mesmo banco.

| Item | Quantidade / cenário |
| --- | --- |
| Clínica | 1 fictícia |
| Usuários | 1 administrador e 1 dentista |
| Pacientes / prontuários | 3 / 3; um prontuário vazio |
| Consultas | 1 agendada e 1 concluída |
| Vínculos | 1 ACTIVE, 1 REVOKED e um paciente sem vínculo |
| Eventos | 2 concessões e 1 revogação administrativa |
| Evoluções | 1 DRAFT sem consulta e 1 FINALIZED com consulta |
| Auditoria geral | 1 registro da carga fictícia |

Credenciais fictícias armazenadas com Argon2id:

| Conta | E-mail | Senha de login | Senha clínica |
| --- | --- | --- | --- |
| Administrador | admin.demo@example.com | DemoLumina2026! | Ausente / NULL |
| Dentista | dentista.demo@example.com | DemoLumina2026! | ClinicaDemo2026! |

A carga é destinada à revisão do banco. A autenticação pela aplicação depende de sua configuração e da conclusão das alterações de backend. O runner SQL não certifica rotas HTTP.

## Contrato do banco e responsabilidades da aplicação

| Garantia no banco | Complemento na aplicação |
| --- | --- |
| Um `medical_records` por paciente, FK RESTRICT | Criar paciente e prontuário vazio na mesma transação. A migração preenche apenas os pacientes anteriores sem prontuário. |
| Vínculo único por clínica/paciente/dentista; ACTIVE ou REVOKED; versão >= 1 | Validar pertencimento à clínica e permissões; serializar alteração do vínculo; incrementar versão e registrar evento na mesma transação. |
| Evento com ator, data, fonte, versão e snapshot do horário original | Novo agendamento SCHEDULED concede/reativa imediatamente. Atualização de consulta antiga não concede acesso. Cancelamento, falta e conclusão preservam o vínculo. |
| Consulta única como origem de concessão; evento único por vínculo/versão | Administrador pode conceder, revogar e reativar sem consulta; evitar reprocessar origem antiga após revogação. |
| Eventos protegidos contra UPDATE/DELETE; FKs RESTRICT | Não disponibilizar operação de apagamento de histórico; consultar auditoria sem modificá-la. |
| Evolução com descrição não vazia, versão >= 1 e finalização coerente; consulta opcional única | Validar autoria, vínculo ativo e clínica; impedir edição de FINALIZED e atualizações com versão antiga. A imutabilidade da evolução finalizada é uma regra da API. |
| `session_version` e `clinical_version` positivas, default 1; hash clínico disponível | Validar versões nos tokens e incrementá-las na redefinição apropriada de senha. |
| Agenda com período calculado e exclusão GiST para SCHEDULED/CONFIRMED | Apresentar conflito de agenda como erro de negócio e validar acesso à clínica. |

A migração não apaga conteúdo clínico e não corrige silenciosamente dados legados inválidos. Ela falha integralmente se houver sobreposição ativa, descrição vazia ou finalização incoerente. A revisão de dados incompatíveis de um banco real é uma etapa posterior, não executada nesta entrega.

As garantias antes presentes apenas no antigo SQL — agenda GiST/período, gatilhos de atualização e `audit_logs` — agora também integram Alembic. A senha clínica anteriormente ausente do SQL está incluída.

`schema.sql` destina-se a banco vazio e não cria nem marca `alembic_version`. Para ambientes que usarão as migrações da aplicação, prefira criar o banco por Alembic. O script SQL não deve ser tratado como migração incremental de um banco existente. A reversão testada cobre exclusivamente a revisão nova em banco descartável; não representa uma reversão de dados clínicos reais.

## Arquivos e hashes SHA-256

Verificação dos arquivos:

```bash
sha256sum backend/alembic/versions/*.py backend/database/*.sql \
  backend/database/verify_disposable.sh backend/database/Dockerfile.migrations

git diff b97f424 -- backend/alembic/versions/50d77a928a7c_create_clinics_and_users_tables.py \
  backend/alembic/versions/7a1d9e3b4c5d_create_patients_dentists_appointments.py \
  backend/alembic/versions/8c2f4a1b6d7e_create_medical_records.py \
  backend/alembic/versions/9d3e5f7a1b2c_add_clinical_password_hash.py
```

O segundo comando deve produzir saída vazia. Hashes dos artefatos desta entrega:

```text
63a65d967041a3dd26a46c3c7adaee46ffdcd4426631854355d811df9e28a9f1  50d77a928a7c_create_clinics_and_users_tables.py
d67b1b784999ab9efafa48972168ac08869b851c0311cf54342d83b14fd3894e  7a1d9e3b4c5d_create_patients_dentists_appointments.py
0373b20b38e3bd1d488d1785ef17c5007140453ddb24124eed8cbcb1fe2a461e  8c2f4a1b6d7e_create_medical_records.py
a1864b68a6da3f23909b3136bd0cc4aeac71c8a4eff5e5c47d54b106add5ae5c  9d3e5f7a1b2c_add_clinical_password_hash.py
7427e6572198b13f71db8d63a181c5c8226f702d1867c2ad343db60f2f1c3b0b  a6e8f0b2c4d6_unify_clinical_access_schema.py
2ca830bda08ba3711f69408fe5848a5fd3304156373020f90310b04e746eda81  schema.sql
9007fc2d78e392a05f34487bd21a8e40470ebceb89cf9f0a8ede5c95b808c0d2  check_clinical_schema.sql
9c01f7b876685aac8d3fd8e4d7e02de67ce92460b4eaec445209390a5852fb54  fixture_9d3e5f7a1b2c.sql
71247459c83cd9cdfe939f90adc4412153a0e7d44185f9660486c759f071aabd  seed_demo.sql
2b91ae5d41d00b4eb7cad7bf69f9dc52dbadfbe418f02be01a6bef55bdef348b  verify_disposable.sh
66c587551ff34fb5faafadd83278e9468c63c07c864296b1af2de9851119499a  Dockerfile.migrations
```
