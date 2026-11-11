# Requisitos do sistema — detalhamento clínico

**Consolidação documental:** 09/11/2026. **Branch:** `chore/sprint-07-docker-integration`. A correção está no commit `8eeddd5` e a revalidação foi publicada em `4c352b2`. A política aprovada em 25/10 e os identificadores existentes foram preservados.

Os IDs vêm do [catálogo geral](../requirements.md). Cada RF possui arquivo próprio, e as regras estão em [regras de negócio](../regras-de-negocio/README.md).

| Requisito | Situação consolidada |
|---|---|
| [RF-023 — Consultar prontuários clínicos](RF-023-prontuario-do-paciente.md) | Preparação e continuidade implementadas na API e SQL. Abertura explícita, implantação, legado e interface mantêm pendências. |
| [RF-024 — Registrar evoluções clínicas](RF-024-evolucoes-clinicas.md) | Criação, autoria, privacidade, finalização e controle de versão implementados. QA-01/QA-02 revalidados em PostgreSQL descartável, no recorte relatado. Conteúdo mínimo completo, CRO histórico e retificação seguem pendentes. |
| [RF-025 — Resumos de apoio por IA](RF-025-resumo-clinico-por-ia.md) | Proposta de produto dependente de D07. |

## Diretrizes e evidências

O prontuário acompanha o paciente e pode receber registros de diferentes dentistas. Cada evolução mantém autoria individual. A permissão de cadastro de pacientes ou operação da Agenda é independente da leitura clínica.

Paulo aprovou em 25/10 a preparação por confirmação confiável ativa e a continuidade por atendimento comprovado. A API persiste as evidências e consulta todas as origens válidas da dupla paciente–dentista na clínica. Cancelamento ou ausência deixam de sustentar preparação quando não há outra origem válida. Somente o autor lê ou altera seu rascunho, e dentistas autorizados leem finalizadas.

A [revalidação independente de 04/11](../relatorios/qa/2026-11-04-2f7dbfe-qa01-qa02/relatorio.md) aprovou QA-01/QA-02 com ressalvas no recorte testado. A execução final teve 10 testes aprovados em PostgreSQL 16.15 descartável e uma sondagem separada da migração. TestClient executou a API no processo dos testes. Em 09/11, os oito hashes de arquivos e o diff rastreado correspondem às evidências publicadas em `4c352b2`.

A imagem API implantada, a interface e a migração do banco da equipe ainda exigem verificação própria. O frontend precisa enviar `version` ao editar e `care_occurred_at` com fuso ao concluir. A migração preparada deve ser avaliada pelo DBA para o banco de destino.

As falhas do ensaio inicial de 23/10 e do QA de 31/10 permanecem registradas como histórico. Para o estado de QA-01/QA-02, usar a revalidação de 04/11. A tentativa SQLite inconclusiva do QA não entra como aprovação.

## Decisões parcialmente fechadas e pendentes

| Código | Situação | Próxima ação |
|---|---|---|
| D01 | Política, evidências e autorização implementadas. Legado, alteração excepcional dos participantes e correção de confirmação indevida seguem abertos. | DBA identifica a linhagem do destino e propõe migração/recuperação. Paulo define as exceções. |
| D02 | GET ainda pode criar prontuário. Separação entre consulta e abertura explícita continua pendente. | Fechar contrato com Paulo e alinhar API e frontend. |
| D03 | Conclusão pelo dentista responsável a partir de CONFIRMED confiável está implementada. Em 02/11, Paulo aprovou exigir evolução salva com descrição antes de concluir, podendo permanecer DRAFT, além de itens ou Sem cobrança. Essas condições novas estão planejadas. | Implementar o fluxo futuro conforme especificação. Definir estados restantes de escrita, atendimento avulso e correções indevidas. |
| D04 | Descrição antes da conclusão foi definida para o fluxo futuro. Conteúdo mínimo para finalizar evolução e registro em nome de terceiros continuam pendentes. | Refinar as validações sem equiparar concluir consulta a finalizar evolução. |
| D05 | Fotografia histórica de nome/CRO, legado e retificação continuam pendentes. | Paulo define regras, e DBA/backend detalham estrutura e contratos. |
| D06 | Acesso a paciente inativo continua pendente. | Paulo define leitura e escrita sem apagar histórico. |
| D07 | Resumo por IA continua proposto. | Definir escopo, fontes e revisão humana antes de implementar. |

Os códigos D identificam decisões locais. A aprovação de produto cabe a Paulo, e os responsáveis técnicos detalham contratos e efeitos em suas áreas.

## Planejamento da próxima implementação

A [especificação v0.4](../especificacoes/fluxo-atendimento-mvp-2026-11-02.md) e a [entrega para a equipe](../especificacoes/README.md) descrevem os seis fluxos pretendidos. Incluem segunda senha clínica, recuperação por credencial temporária de uso único, evolução salva antes da conclusão, itens de serviço ou Sem cobrança, encaminhamento administrativo e confirmação de pagamento externo pela recepção.

Administrador foi indicado para correção de serviços, com limites técnicos ainda propostos. Paralelismo do Argon2 permanece apenas sugestão de estudo. Essas propostas e decisões não constam como recursos entregues no código consolidado.

## Impactos e repasse

| Parte | Encaminhamento |
|---|---|
| API clínica | Manter autoria, vínculo, isolamento e controle de versão consolidados. Alterar contratos apenas na nova implementação identificada. |
| Frontend | Enviar version na edição e horário realizado com fuso na conclusão. Reproduzir o protótipo alinhado aos contratos. |
| Banco existente | Inventariar, preparar backup e ensaiar restauração antes de aplicar a migração adequada. Esquemas Alembic ou mistos exigem reconciliação. |
| Documentação | Preservar datas e versões dos relatórios históricos. Relacionar implementação, evidência e pendências pelos índices. |
| QA | Usar commit e ambiente identificados nos próximos ensaios. A revalidação de 04/11 encerra apenas o recorte exercitado de QA-01/QA-02. |

Anamnese, odontograma, anexos, consentimentos e retificação possuem escopos próprios. O detalhe de autoria histórica permanece em RN-032.
