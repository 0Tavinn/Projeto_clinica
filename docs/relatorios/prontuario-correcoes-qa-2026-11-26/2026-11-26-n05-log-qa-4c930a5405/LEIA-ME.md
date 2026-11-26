# Entrega de QA — N05-LOG — 26/11/2026

**N05-LOG encerrado para a candidata e configuração testadas.**
Executor:agente de QA. Candidata sem Git,manifesto e3b28488163b174758f7e3782dbe916b0cc1cf8120cadf5a3cd5da79200e2825.

## Documentos

- [Relatório completo](relatorio.md)
- [Resumo para Paulo e Cassiano](resumo-cassiano.md)
- [Matriz CSV](matriz.csv)
- [Totais sem sobreposição](totais.json)
- [Reprodução](reproducao.md)
- [Tentativas preservadas](tentativas.csv)

## Provas principais

- [Captura inicial de resultados HTTP](http-results.json) e [objetivos finais](http-results-final.json).
- [Checagens iniciais de logs](privacy-log-check.json) e [consolidação rastreável](privacy-log-check-final.json).
- [stdout](api-stdout-sanitized.log) e [stderr](api-stderr-sanitized.log), ambos sanitizados.
- [Complemento TRACE](method-result.json) e [seu log](method-api-sanitized.log).
- [Testes recebidos](tests.log) e [JUnit](tests.xml).
- [Contrato OpenAPI](openapi-comparison.json).
- [Identidade](identity.json) e [diff](candidate-vs-baseline.patch).
- [Preservação principal](preservation.json),[final](preservation-final.json),[limpeza](cleanup.json) e [limpeza do complemento](method-cleanup.json).
- [Checkpoint concluído](CHECKPOINT-CONCLUIDO.md).

Os números antigos deQA eBackend não foram somados. O pacote original e os relatórios históricos não foram reescritos.
A captura inicial conserva dois campos falsos por um método rejeitado no parser; o relatório explica por que não é defeito e comoTRACE comprovou o caminho405/OTHER.
Nenhum PDF,print ouvídeo foi criado;as evidências são HTTP,SQL,logs e metadados reais.
