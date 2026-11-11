# Regras de negócio — prontuário e evoluções

**Revisão documental:** 09/11/2026. IDs e decisões de acesso de 25/10 preservados. A API e o SQL implementam preparação e continuidade, e as correções QA-01/QA-02 foram revalidadas no recorte descrito pelo [QA de 04/11](../relatorios/qa/2026-11-04-2f7dbfe-qa01-qa02/relatorio.md). Os limites funcionais ainda abertos constam no [índice de requisitos](../requisitos/README.md).

| Regra | Objeto | Situação |
|---|---|---|
| [RN-031](RN-031-RF-023-acesso-ao-prontuario.md) | Prontuário por paciente, preparação por confirmação ativa e continuidade por atendimento realizado | Política aprovada em 25/10, implementada na API e SQL. QA-01/QA-02 consolidados em `8eeddd5`, com evidências em `4c352b2`; implantação e legado seguem pendentes. |
| [RN-032](RN-032-RF-024-preservacao-do-historico-clinico.md) | Autoria, privacidade dos rascunhos, estados, CRO histórico e retificação | Autoria e privacidade definidas em RN-031; conteúdo mínimo, CRO histórico e retificação ainda propostos. |
| [RN-033](RN-033-RF-025-ia-como-apoio-ao-profissional.md) | Limites do resumo de apoio por IA | Proposta pendente de D07, sem implementação. |

RN-001 (clínica), RN-015 (número cadastral), RN-017 (participantes), RN-021/RN-025 (Agenda), RN-024 (transições) e RN-034 (rastreabilidade) continuam no catálogo geral. A permissão administrativa para operar a Agenda não concede ao administrador ou à recepção leitura clínica. Confirmação confiável com consulta atualmente `CONFIRMED` sustenta preparação; somente a ação **Concluir atendimento** pelo dentista responsável registra a realização que pode sustentar continuidade. Esses mecanismos estão implementados na API. A [especificação de 02/11](../especificacoes/fluxo-atendimento-mvp-2026-11-02.md) descreve a próxima implementação, incluindo autenticação adicional e encaminhamento administrativo.

Ver [decisões parcialmente fechadas e pendentes, impactos e repasse](../requisitos/README.md). Esta revisão não renumera as regras nem declara o módulo clínico validado.
