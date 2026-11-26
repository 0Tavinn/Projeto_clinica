# Entrega de QA — prontuários/OpenCL

Execuções:25/11/2026. Finalização:26/11/2026. Executor:AGENTE DE QA.
Candidata semGit:manifesto987ee7199972977bc549346246d0ee5bf46d4611b9d15c3c8fc89fdfbd41fe40.
Parecer:não pronto para integração desta candidata;N05-LOG permanece aberto.

## Leitura recomendada

1. [Resumo para Cassiano](resumo-cassiano.md)
2. [Relatório técnico completo](relatorio.md)
3. [Matriz CSV](matriz.csv)
4. [Comparativo de contratos](comparativo-contratos.md)
5. [Roteiro de reprodução](reproducao.md)
6. [Contagens](totais.json) e [tentativas preservadas](tentativas.csv)

## Evidências principais

- Privacidade pendente:[checagem do log](privacy-log-check.json) e [access log sanitizado](api-sanitized.log).
- Espera SQL/concorrência:[saída](concurrency-replay.log),[agenda em horário livre](appointment-race-final.log).
- Revogação durante kernel real:[telemetria](instrumentation-probe.log).
- Testes fornecidos:[saída](provided-tests.log) e [JUnit](provided-tests.xml).
- Preservação:[resultado](preservation.json);[limpeza](cleanup.json).
- Identidade:[manifesto da candidata](candidate-files-sha256.json),[inventário](identity.json),[mudanças](changes.json).
- Verificação documental de26/11:[auditoria](revisao-artefatos-2026-11-26.json).
- Encerramento:[checkpoint final](CHECKPOINT-CONCLUIDO.md);o checkpoint de pausa foi preservado.
- Integridade dos artefatos:[digests](manifesto-evidencias-sha256.json).

O ZIP de distribuição contém os artefatos e os roteiros,não uma instalação da aplicação nem uma nova candidata.
A cópia baseline-4ccdc30 é somente a referência estática anterior;não confundir com o pacote ensaiado.
Não há arquivo de segredo efêmero,PDF,prints de navegador ou vídeos.
