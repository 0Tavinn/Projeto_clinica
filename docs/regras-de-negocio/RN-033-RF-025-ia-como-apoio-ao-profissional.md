# RN-033 — IA como apoio ao profissional

**Revisão:** 24/10/2026. **RF relacionado:** [RF-025](../requisitos/RF-025-resumo-clinico-por-ia.md). **Situação:** proposta; não implementada. **Dependências:** a política de leitura de D01 foi aprovada, mas sua autorização persistente ainda depende de desenho e implementação; D07 e a proposta de IA continuam pendentes no [índice](../requisitos/README.md).

O resumo deve ser identificado como conteúdo de apoio, com origem e momento de geração. Sua leitura e processamento obedecem à mesma autorização do histórico utilizado. A proposta usa evoluções finalizadas autorizadas; rascunhos de terceiros e dados de outra clínica não devem compor o processamento.

O dentista deve poder conferir as fontes originais e continuar o atendimento se a IA estiver indisponível. O sistema informa quando o resumo cobre apenas parte do histórico ou está desatualizado. Ausência de registros deve produzir uma mensagem de ausência, sem inventar fatos.

O resumo não é automaticamente incorporado à evolução, não substitui revisão profissional e não confirma atendimento, diagnóstico ou assinatura. O fluxo, o uso de dados e eventual processamento externo precisam ser aprovados antes da implementação. Não há arquitetura, fornecedor ou aceleração escolhidos por esta regra.
