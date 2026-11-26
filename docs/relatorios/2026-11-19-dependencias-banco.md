# Relatório DBA — dependências do banco

Data: 19/11/2026. Guia operacional: [banco-prontuarios-preparacao.md](../banco-prontuarios-preparacao.md).

## Conclusão

O pacote do banco está pronto para Tarcísio usar em PostgreSQL 16 e integrar à própria implementação de prontuário. **Não foi identificada dependência DBA faltante neste ambiente.** Não foi necessário reinstalar pacotes nem alterar SQL, aplicação, imports ou dependências da API nesta revisão.

O pacote foi testado com o código original B da aplicação, sem os novos módulos do prontuário. Não há impedimento DBA para o primeiro commit autônomo. Esse resultado valida o banco e suas migrações; a aplicação B original ainda não implementa os novos fluxos.

## Dependências conferidas

| Componente | Resultado observado |
| --- | --- |
| Docker CLI / daemon | 29.9.3 / 29.9.3; acessíveis pelo Ubuntu WSL |
| Bash, diff, grep, mktemp | Disponíveis no WSL |
| Imagem mínima de migração | Funcional; construção automática já validada; separada da API/OpenCL |
| Python / Alembic / SQLAlchemy | 3.12.16 / 1.19.1 / 2.0.52 |
| psycopg / psycopg-binary | 3.3.9 / 3.3.9; implementação efetiva `binary`; libpq embarcada 180006 |
| Pydantic / pydantic-settings | 2.14.3 / 2.15.0 na imagem mínima; imports da configuração B funcionaram |
| Consistência de pacotes | `pip check`: `No broken requirements found.` |
| PostgreSQL / btree_gist | 16.15; extensão criada e exclusão GiST exercitada com sucesso |
| Clientes PostgreSQL | psql, pg_dump e pg_restore utilizados dentro do contêiner; não precisam estar no host |
| FastAPI / NumPy / PyOpenCL | Ausentes da imagem mínima e dispensáveis para este pacote |

As versões são as efetivamente observadas nesta revisão; a imagem mínima não exige todas as dependências da API. A primeira construção precisa obter imagens/dependências ainda não locais. Em outro servidor PostgreSQL, é preciso disponibilizar `btree_gist` e usar um usuário autorizado a criá-la, ou providenciar sua instalação administrativa prévia.

## Autonomia do primeiro commit: ensaio realizado

A lacuna de evidência era comprovar a execução antes dos novos arquivos da aplicação. Foi resolvida por este ensaio:

1. Extração de `git archive b97f424 backend` para pasta temporária própria.
2. Sobreposição somente de `alembic/env.py`, nova revisão, seis arquivos de `database` e guia do banco.
3. Confirmação de ausência de `app.records.access_models` e de identidade dos **43 arquivos de backend/app** com os blobs Git de B.
4. Execução do runner padrão, sem override de imagem, iniciada de `/tmp`, fora do clone, com o checkout em caminho contendo espaços.
5. Resultado: **código de saída 0**, com limpeza automática dos recursos Docker descartáveis.

O módulo `app.records.models` já existe na base B. Sua inclusão no `alembic/env.py` nesta entrega dispensa os novos módulos do prontuário. Os caminhos do runner apontam para o próprio checkout montado somente para leitura. A pasta ensaiada foi `/tmp/lumina-dba-baseline com espaco-azsqbct7`.

Resultados aprovados:

- Criação por Alembic e SQL; `pg_dump --schema-only` integralmente idêntico, excluindo apenas `alembic_version`.
- Atualização de B com histórico fictício preservado, criação de prontuário ausente e nenhuma concessão por consulta antiga.
- Rejeição de finalização legada incoerente e agenda ativa sobreposta, com rollback integral.
- Constraints de prontuário/evolução/versões, descrição vazia inclusive tabulações e quebras, agenda, idempotência, snapshots e eventos imutáveis.
- Seed fictício e recusa de reaplicação; reinício PostgreSQL; backup/restauração com dados e sequências idênticos e checks reaplicados na restaurada.
- `bash -n` e `git diff --check` sem erros.

## Linhagem e integridade

Base: `b97f42479ff76001f1be38def489d482a807967f`; trabalho em `feat/sistema-prontuarios`.

Cadeia linear preservada: `50d77a928a7c -> 7a1d9e3b4c5d -> 8c2f4a1b6d7e -> 9d3e5f7a1b2c -> a6e8f0b2c4d6`.

As quatro revisões publicadas permanecem idênticas à base B. Os 11 hashes de migrações e artefatos DBA registrados no guia correspondem aos arquivos atuais. O primeiro pacote inclui env Alembic, nova revisão, seis arquivos de database, guia e este relatório; não requer os novos modelos/serviços.

## Uso e limites da integração própria

Na raiz do clone, a validação completa é:

~~~bash
bash backend/database/verify_disposable.sh
~~~

O runner não deixa banco em execução. O guia contém a criação da demonstração PostgreSQL/DBeaver e os comandos para executar `schema.sql` e o seed opcional em banco próprio vazio. A URI do psql usa `postgresql://`; a do Alembic/SQLAlchemy usa `postgresql+psycopg://`.

O backend de Tarcísio deve implementar os estados, as permissões por clínica/ator/autoria, a criação transacional de paciente/prontuário, as concessões/revogações/reativações com versão e evento, a concorrência das evoluções, a imutabilidade de FINALIZED na API e a invalidação de tokens. As FKs e CHECKs não substituem essas regras. Consultas antigas não podem reativar vínculos; mudanças de status preservam o vínculo. O período de agenda é preenchido pelo servidor.

O ensaio com B comprova execução de migrações, não alinhamento dos metadados ORM antigos para autogenerate. Os modelos correspondentes devem ser integrados antes de gerar futuras revisões a partir deles.

`schema.sql` não cria nem marca `alembic_version`. Não execute `alembic upgrade head` automaticamente após provisionar por SQL. Para seguir a cadeia deste projeto, prefira criar o banco por Alembic; eventual adoção de baseline exige catálogo previamente conferido e decisão explícita, sem stamp automático.

Nenhum banco ou volume existente foi alterado. O DBA não realizou stage, commit ou push; nesta revisão acrescentou somente este relatório.
