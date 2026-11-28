# Entrega QA — novas rotas de pacientes clínicos e vínculos

**Pronto com ressalvas para integrar em ambiente de teste.** Execução pelo agente de QA em26/11/2026.
Fonte local31,manifesto95fb2b8e2fd21f7a5a9e125fcbb7aaeb110e74d610eb150f3a4bb7f8d33bfcd7.
Branchfix/prontuario-correcoes-qa,HEAD67068ac969cb7b34396b5d94e4ee09a7001ef8b4 mais alterações sem commit.

## Entrega

- [Relatório](relatorio.md)
- [Resumo para Cassiano](resumo-cassiano.md)
- [Matriz](matriz.csv)
- [Totais](totais.json)
- [Tentativas](tentativas.csv)
- [Reprodução](reproducao.md)
- [Encerramento](CHECKPOINT-CONCLUIDO.md)

## Evidências principais

- [HTTP/SQL](http-results.json) e [saída das sondagens](probe-execution.log).
- [Checagens dos logs](privacy-log-check.json),[stdout](api-stdout-sanitized.log),[stderr](api-stderr-sanitized.log).
- [JUnit](tests.xml),[testes distribuídos](tests.log),[OpenAPI](openapi-comparison.json).
- [Fonte antes](source-before.json),[depois](source-after.json),[identidade](identity.json),[diff local completo](local-complete.patch).
- [Preservação](preservation.json),[limpeza](cleanup.json),[tentativa abortada](attempt-1/preservation.json).
- [Reconciliação documental](source-reconciliation.json),[revisão de artefatos](artifact-review.json).
- [Manifesto dos artefatos](manifesto-evidencias-sha256.json).

58 verificações independentes e32 testes aprovados,com20 asserções transversais dosmesmos logs e1 contrato.
Não somar grupos sobrepostos,retentativas ou números doBackend/rodadas antigas.
Sem navegador,PDF,implantação diária ouaceite final daSprint.
