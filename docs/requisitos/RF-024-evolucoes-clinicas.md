# RF-024 — Registrar evoluções clínicas

**Revisão:** 23/10/2026. **Situação:** implementação parcial; autoria individual definida por Paulo, demais detalhes operacionais para revisão. **Regras:** [RN-031](../regras-de-negocio/RN-031-acesso-e-responsabilidade-pelo-prontuario.md) e [RN-032](../regras-de-negocio/RN-032-preservacao-do-historico-clinico.md). **Decisões:** D03 a D06 no [índice](README.md).

## Objetivo e direção definida

Registrar cada atendimento no prontuário do paciente identificando o profissional responsável por aquela evolução. Diferentes dentistas podem registrar suas próprias evoluções no mesmo prontuário. O autor vem da sessão autenticada; o cliente não escolhe livremente outro autor.

**Ator:** dentista autenticado e elegível. **Entradas atuais:** paciente, descrição, procedimento e observações opcionais, agendamento opcional. **Dados de controle:** autor, identificação profissional histórica proposta, horário do registro, horário do atendimento a definir, estado e horário de finalização. **Estados existentes:** `DRAFT` e `FINALIZED`.

## Fluxo recomendado para aprovação

1. A API valida paciente, clínica e autorização para registrar; verifica profissional elegível. Se houver consulta, confere conjuntamente seus vínculos e a situação aprovada para essa ação. Atendimento avulso depende de regra própria (D03).
2. O dentista consulta o histórico e prepara o rascunho do atendimento. Ao reabrir a consulta, a proposta é recuperar o próprio registro existente em vez de criar outro.
3. Quando uma operação incluir abertura do prontuário e criação da evolução, tudo é confirmado na mesma transação ou revertido em caso de falha.
4. Somente o autor edita o próprio rascunho. A proposta mantém rascunhos privados e botões coerentes com as permissões.
5. Ao finalizar, a API confere conteúdo mínimo aprovado e identificação do atendimento, registra horário e preserva dados de autoria conforme RN-032. Conclusão da consulta e finalização da evolução são eventos distintos; as dependências precisam ser aprovadas.
6. Finalizado, o registro não recebe edição ou exclusão comum. Correções seguem a retificação aprovada, preservando o original. O botão de finalizar não equivale a assinatura certificada.

## Critérios de aceite

| ID | Resultado verificável após aprovação das regras dependentes |
|---|---|
| RF-024-CA01 | Autoria vem da sessão; enviar outro identificador não permite registrar em nome de outro profissional. |
| RF-024-CA02 | Consulta de outro paciente, dentista ou clínica é recusada; cancelamento/ausência e demais estados seguem a política explícita de atendimento. |
| RF-024-CA03 | O autor edita e finaliza seu rascunho; outro dentista não executa essas ações. |
| RF-024-CA04 | Finalização sem os campos mínimos aprovados é recusada; caso válido grava autoria e horários. Descrição vazia ou somente espaços deve ser recusada conforme proposta mínima. |
| RF-024-CA05 | Evolução finalizada não aceita edição/exclusão comum; a retificação aprovada preserva conteúdo e autoria anteriores. |
| RF-024-CA06 | Rascunho e finalização são recuperados no PostgreSQL após reiniciar; falha parcial não confirma apenas parte de uma operação composta. |
| RF-024-CA07 | Casos de administrador, recepção, outro dentista e outra clínica são testados por HTTP com dados fictícios. |
| RF-024-CA08 | Alteração posterior de nome/CRO no cadastro não reescreve a identificação histórica da evolução, respeitado o tratamento de dados antigos. |
| RF-024-CA09 | Reabrir uma consulta recupera o registro já criado; duplicidade recebe resposta previsível sem erro interno genérico. |
| RF-024-CA10 | Requisições concorrentes não editam conteúdo já finalizado nem sobrescrevem silenciosamente uma atualização. |

## Situação encontrada e impacto

Existem criação, edição e finalização. O autor é obtido da sessão e o serviço bloqueia edição comum após finalizar. Faltam validação conjunta de agendamento, descrição mínima, privacidade dos rascunhos, cópia histórica de nome/CRO e retificação. O repositório faz commits separados. Os testes isolados documentados no índice demonstraram parte dessas falhas; não constituem aceite HTTP/PostgreSQL.

Rever serviço, schemas, repositório e models de `backend/app/records/`. O DBA avalia campos, restrições, concorrência e atualização de tabelas existentes. A regra atual de uma evolução por agendamento precisa ser considerada ao modelar retificação. A interface deve retomar o rascunho e acompanhar mudanças do contrato.
