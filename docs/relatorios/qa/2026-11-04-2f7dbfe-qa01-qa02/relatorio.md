# Revalidação independente QA-01 e QA-02 — 04/11/2026

**Parecer:** QA-01 **pronto com ressalvas** e QA-02 **pronto com ressalvas** para os cenários exercitados na versão local identificada. Não é aceite da Sprint 7 nem prova da versão publicada.

## Versão e ambiente

- Repositório: `/home/paulinho/Work/Projeto_clinica`; branch `chore/sprint-07-docker-integration`; HEAD `2f7dbfe6d0d7a747f57dbeeede3a716938adc5fa`.
- As correções estão **sem commit**. `git-status-before.txt` identifica as alterações locais; `local-diff-tested.patch` guarda o diff rastreado de serviço, repositório de acesso, modelo, schema, testes e schemas clínicos. `file-hashes.txt` identifica também o SQL de migração ainda não rastreado. Documentos e requisitos locais foram consultados, não executados.
- API FastAPI executada no processo de testes por `TestClient` com o código local, conectada ao PostgreSQL 16.15 em contêiner descartável. Python 3.12.14, pytest 9.1.1; Docker 29.9.2, Compose v5.6.1. Não foi construída uma imagem de API nem exercido HTTP pela rede externa.
- Banco `lumina_qa_20261104_2f7dbfe` no contêiner `lumina_clinical_api_<sufixo>`, com rede e volume de mesmo prefixo, porta local dinâmica. O script recusa colisões, aplica `backend/database/schema.sql` local e usa somente dados fictícios. A migração usou outro PostgreSQL 16 descartável sem rede.
- O ensaio final durou 7,76 s de pytest, além da inicialização. O ensaio da migração concluiu separadamente. Os nomes dos recursos criados constam dos logs; contêineres, volumes e redes temporários foram removidos e a listagem final não mostrou resíduos. Recursos preexistentes `lumina_execucao_20261029_*` e `lumina_s07_review_20261023-*` não foram tocados.

## Resultados novos

**QA-01 — aprovado no recorte testado.** Em conexões independentes, a linha da evolução foi bloqueada, `pg_stat_activity` confirmou espera por `Lock`, a última consulta autorizadora foi cancelada com HTTP 200 e só então o bloqueio foi liberado. Edição e finalização responderam **403**. O rascunho permaneceu `DRAFT`, versão 1, sem `finalized_at` e com descrição original. Com outra confirmação válida, a edição respondeu 200 e versão 2; com atendimento anterior comprovado, a finalização respondeu 200 e versão 2. Evidência: `pytest-pg16-final.log`, casos `test_mutation_rechecks_access_after_evolution_lock`.

**QA-02 — aprovado no recorte testado.** Duas edições com `version=1` aguardaram o mesmo bloqueio PostgreSQL; após liberação, retornaram **200 e 409**. O conteúdo persistido foi o da edição aceita e a versão passou a 2. Uma nova edição com versão 1 foi recusada com 409; a versão 2 foi aceita e passou a 3. Versão ausente, zero, textual e nula retornou 422 `VALIDATION_ERROR`. O teste também confirmou rollback de falha simulada, 403 para outro autor e outra clínica e bloqueio após finalização. Evidência: `pytest-pg16-final.log`, caso `test_draft_version_rejects_concurrent_and_stale_edits`.

**Regressões relacionadas:** espera de edição durante finalização, reconferência após bloqueio da consulta, abertura do prontuário com rollback, confirmação/conclusão simultâneas e fluxo HTTP persistente passaram na mesma suíte. Total da execução final: **10 testes aprovados, 0 reprovados**. Uma sondagem da migração em outro banco PostgreSQL 16 preservou uma evolução anterior com versão 1 e recusou reaplicação e versão 0. Evidência: `migration-pg16.log`.

## Tentativas inconclusivas e limites

A primeira execução PostgreSQL teve 3 aprovações e 7 falhas de preparação por HTTP 429 no login do cliente de testes. O contador global de login permaneceu ativo entre casos porque a cópia da sondagem estava fora do diretório de testes. A cópia temporária foi ajustada para limpar **apenas o contador de teste** entre casos; a aplicação não foi alterada. A execução final passou integralmente. Esses resultados não são somados aos 10 testes finais. Evidências: `pytest-pg16.log` e `pytest-pg16-rerun.log`.

A tentativa complementar SQLite terminou pelo limite de 60 segundos sem saída; não conta como aprovação. Os cenários decisivos foram executados em PostgreSQL 16. Os testes usam `TestClient` e fixture; não demonstram implantação de uma imagem API, interface ou migração em banco da equipe. A sondagem de migração usa um schema anterior descartável, não o banco existente. As 9 advertências do pytest não impediram os testes; não foram classificadas como defeitos destas correções. Resultados de 31/10 em `../2026-10-31-2f7dbfe/` são históricos e não entram na contagem nova.

## Reprodução e evidências

1. Conferir `git-status-before.txt`, `local-diff-tested.patch` e `file-hashes.txt` para identificar exatamente o código local.
2. Executar `bash docs/relatorios/qa/2026-11-04-2f7dbfe-qa01-qa02/run_pg16_qa.sh`. O script cria, verifica e remove recursos Docker exclusivos; exige Docker acessível e `backend/.venv` instalado. Ele usa a cópia da sondagem em `test_clinical_pg16_qa.py`, adaptada ao banco exclusivo, com contador de login isolado e saídas dos bloqueios. Tempo máximo externo recomendado: 240 s.
3. Executar `bash backend/database/checks/run_20261031_evolution_version_pg16.sh` em outro PostgreSQL 16 descartável. A sondagem usa o SQL de migração local ainda não rastreado. Tempo máximo externo recomendado: 120 s.
4. Conferir `matriz.csv`, `pytest-pg16-final.log` e `migration-pg16.log`. Não usar os recursos Docker preexistentes para reproduzir.

## Resumo para Cassiano

Na branch `chore/sprint-07-docker-integration`, HEAD `2f7dbfe6d0d7a747f57dbeeede3a716938adc5fa`, com correções locais sem commit, QA-01 e QA-02 passaram em PostgreSQL 16.15 descartável. A perda da última autorização durante espera por bloqueio produziu 403 sem alterar o rascunho; outra origem válida preservou o acesso. Duas edições simultâneas da mesma versão produziram 200/409 sem sobrescrita silenciosa. A migração de `version` passou em outro banco descartável. O parecer limita-se ao código local e aos cenários de API/SQL executados; não atesta a versão publicada, a interface ou o banco da equipe.
