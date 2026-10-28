# RF-025 — Disponibilizar resumos de apoio ao dentista por IA

**Revisão:** 23/10/2026. **Situação:** proposta discutida com Paulo; sem implementação ou inclusão automática na entrega de 24/10. **Regra:** [RN-033](../regras-de-negocio/RN-033-RF-025-ia-como-apoio-ao-profissional.md). **Decisões:** D01 e D07 no [índice](README.md).

## Objetivo e fluxo proposto

Ao abrir o atendimento, apresentar um resumo do histórico clínico autorizado para apoiar a leitura pelo dentista. O quadro deve ser identificado como apoio por IA e coexistir com histórico original e editor da evolução atual. O resumo trata de registros anteriores; a evolução do dia é registrada e revisada pelo profissional.

1. Autorizar o acesso ao paciente antes de recuperar ou gerar o resumo.
2. Selecionar evoluções finalizadas autorizadas, conforme política aprovada. Informar se o resumo cobre todo o histórico disponível ou um recorte.
3. Exibir origem dos registros, data de geração e indicação de desatualização quando o histórico mudar.
4. Permitir abrir os registros originais. Não incorporar automaticamente o resumo à evolução nem finalizar conteúdo pelo dentista.
5. Sem histórico, informar que não há conteúdo para resumir; em erro ou indisponibilidade, manter histórico e editor utilizáveis.

## Critérios de aceite propostos

| ID | Resultado esperado |
|---|---|
| RF-025-CA01 | Usuário sem autorização não recebe resumo nem provoca processamento de conteúdo daquele paciente. |
| RF-025-CA02 | São identificados os registros utilizados, a cobertura e o momento da geração; o original continua acessível. |
| RF-025-CA03 | Não há geração de fatos clínicos fictícios quando não existe histórico; a tela informa ausência ou falha. |
| RF-025-CA04 | Falha da IA não impede ler o prontuário ou salvar rascunho próprio. |
| RF-025-CA05 | Conteúdo de apoio não se torna evolução finalizada ou assinatura automaticamente. |

O processamento, a atualização, os dados autorizados e eventual uso de serviço externo dependem de D07. Não há decisão de fornecedor, modelo, OpenCL ou processamento noturno. Dependências e aceite deste RF não bloqueiam a correção de RF-023 e RF-024.
