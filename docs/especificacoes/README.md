# Especificações do atendimento odontológico

**Consolidação documental:** 09/11/2026. Este índice organiza a especificação para a próxima implementação e identifica suas fontes históricas.

## Documento de trabalho

- [Especificação funcional v0.4, de 02/11](fluxo-atendimento-mvp-2026-11-02.md).
- [Roteiro dos seis fluxogramas](roteiro-fluxogramas-mvp-2026-11-02.md).
- [Complemento Mermaid de pagamento externo e correção administrativa](fluxogramas-complementares-mvp-2026-11-02.md).
- [Parecer de backend](pareceres-2026-11-02/backend.md), [frontend](pareceres-2026-11-02/frontend.md) e [QA](pareceres-2026-11-02/qa.md).

## Entrega para a equipe

- [PDF v0.4](entrega-2026-11-02/Lumina-Odonto-Fluxo-atendimento-MVP-v0.4.pdf).
- [Fonte textual da entrega](entrega-2026-11-02/fluxo-atendimento-mvp-v0.4.md).
- [Instruções e dependências de renderização](entrega-2026-11-02/README-renderizacao.md).

A entrega inclui os seis fluxos lógicos, divididos em dez painéis, com fontes Mermaid e imagens renderizadas. O pagamento externo substitui a proposta inicial de digitar valor recebido e forma. O paciente participa externamente à plataforma. As classificações de decisão aprovada, recomendação técnica e pendência permanecem identificadas.

## Atualização posterior ao documento v0.4

A especificação e seus pareceres são registros datados de 02/11. As referências à revisão independente de QA-01/QA-02 como pendente descrevem o estado daquele dia. Em 04/11, o QA revalidou as correções no recorte descrito no [relatório](../relatorios/qa/2026-11-04-2f7dbfe-qa01-qa02/relatorio.md), com 10 testes aprovados em PostgreSQL 16.15 descartável. `8eeddd5` consolida o código e `4c352b2` publica as evidências. Os oito hashes foram reconferidos em 09/11.

Para o estado atual dos requisitos e das pendências, consultar o [índice clínico](../requisitos/README.md). As novas funcionalidades de segunda senha, encaminhamento, confirmação de pagamento e correção administrativa permanecem no planejamento da próxima implementação. A avaliação de paralelismo continua uma sugestão de estudo.

Os relatórios datados e o PDF v0.4 foram preservados como referência de suas versões. O estado consolidado acima acompanha a revisão posterior de QA, sem atribuir essa execução aos pareceres de 02/11.
