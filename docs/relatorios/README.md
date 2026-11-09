# Relatórios e evidências do Lumina Odonto

**Índice de consolidação:** 09/11/2026. Cada relatório mantém a data, a versão examinada e os limites de sua elaboração.

| Registro | Versão e finalidade |
|---|---|
| [Reunião de 29/10](reunioes/relatorio-parcial-reuniao-2026-10-29.md) · [PDF](reunioes/relatorio-parcial-reuniao-2026-10-29.pdf) | Encaminhamentos e propostas que deram origem ao refinamento do fluxo. |
| [Relatório técnico de 29/10](sprint-07/relatorio-tecnico-sprint-07-2026-10-29.md) · [PDF](sprint-07/relatorio-tecnico-sprint-07-2026-10-29.pdf) | Leitura técnica do estado disponível naquela data. |
| [QA de 31/10](qa/2026-10-31-2f7dbfe/relatorio-qa-sprint07.md) · [Matriz](qa/2026-10-31-2f7dbfe/matriz-testes.csv) | Base `2f7dbfe`, anterior às correções QA-01/QA-02. Os defeitos daquele ensaio são históricos para a versão identificada. |
| [Fechamento parcial da Sprint 7](sprint-07/relatorio-estado-atual-fechamento-parcial-sprint-07-2026-10-31.md) · [PDF](sprint-07/relatorio-estado-atual-fechamento-parcial-sprint-07-2026-10-31.pdf) | Registra as correções locais informadas pelo backend e a revalidação ainda prevista em 31/10. |
| [Sprint 8, consolidação parcial de 02/11](sprint-08/2026-11-02/relatorio-parcial-sprint-08.md) · [PDF](sprint-08/2026-11-02/Lumina-Odonto-Sprint-08-consolidacao-parcial-2026-11-02.pdf) | Distingue dificuldades, entregas práticas e planejamento posterior ao prazo informado de 31/10. Mantém as imagens fornecidas e as divergências documentadas. |
| [Revalidação de QA-01/QA-02 em 04/11](qa/2026-11-04-2f7dbfe-qa01-qa02/relatorio.md) · [Matriz](qa/2026-11-04-2f7dbfe-qa01-qa02/matriz.csv) | Aprovação com ressalvas dos cenários exercitados na versão local identificada, posteriormente consolidada. |

## Referência após a consolidação técnica

`8eeddd5` registra as correções e `4c352b2` publica a revalidação. Os oito hashes e o diff rastreado do QA correspondem aos arquivos consolidados na conferência de 09/11. A execução final de 04/11 teve 10 testes aprovados em PostgreSQL 16.15 descartável. O ensaio usa TestClient no processo da API, com sondagem de migração em outro banco descartável. Imagem implantada, interface e banco existente exigem validação própria.

O resultado posterior atualiza o acompanhamento de QA-01/QA-02. As dificuldades, falhas e pendências registradas nos relatórios anteriores mantêm seu contexto temporal. As contagens de execuções distintas não são somadas como se fossem uma única suíte.

## Planejamento do atendimento

Consultar as [especificações e a entrega v0.4](../especificacoes/README.md) para o escopo de segunda senha, serviços, encaminhamento, pagamento externo e correção administrativa. Esse material orienta a próxima implementação.

Os capítulos de Sprint 7 e Sprint 8 foram preparados para incorporação ao documento cumulativo. A composição e a identificação final do PDF de todas as sprints cabem à entrega acadêmica organizada pela equipe.

Na preparação documental, finais de linha e espaços finais de algumas cópias dos logs históricos foram normalizados para revisão no Git. Os resultados e os arquivos de implementação identificados pelo manifesto de QA foram preservados.
