# RN-032 — Preservação do histórico clínico

**Revisão:** 23/10/2026. **RF relacionado:** [RF-024](../requisitos/RF-024-evolucoes-clinicas.md). **Direção definida por Paulo:** responsabilidade individual por evolução, com múltiplos profissionais no mesmo prontuário.

## Refinamento proposto

1. Extrair autor da sessão e validar seu cadastro profissional. Para este MVP, cada dentista registra o atendimento que realizou; registrar em nome de outro exige regra específica em D04.
2. Manter rascunho editável e finalizável somente pelo autor; restringir sua leitura ao autor conforme RN-031 proposta.
3. Finalizar somente com conteúdo mínimo aprovado (proposta: descrição não vazia), dados do atendimento e autoria consistentes. Distinguir criação do registro, realização do atendimento e finalização; não inventar horário clínico com base apenas no horário de digitação.
4. Preservar identificação profissional histórica, inclusive nome e CRO/UF. O momento da cópia é decisão D05. Para evoluções antigas, o cadastro atual não deve ser apresentado como evidência comprovada do CRO da época; registrar a limitação da atualização.
5. Após finalizar, bloquear edição e exclusão comuns, inclusive sob requisições concorrentes. Finalização é estado da aplicação; não constitui assinatura certificada.
6. Retificação, se aprovada, é um novo registro associado ao original com motivo, conteúdo, autor e data/hora. O original permanece legível e intacto. Quem pode retificar e a modelagem são decisões D05.
7. Preservar registros diante de inativação de paciente ou profissional, com acesso conforme política aprovada. Uma operação composta deve confirmar por inteiro ou reverter; duplicidade e conflito recebem erros previsíveis.

## Situação encontrada e dependências

A aplicação guarda autor e horários e bloqueia edição comum após finalizar. Aceita descrição vazia, não copia a identificação profissional e não implementa retificação. Também não demonstrou a proteção de edição/finalização concorrentes. A unicidade atual de `appointment_id` limita cada consulta a uma evolução; retificação requer desenho compatível ou revisão explícita dessa restrição.

O DBA define alteração de bancos existentes e preservação dos dados; o backend aplica validações, transações e proteção concorrente; João testa esses comportamentos no PostgreSQL. Eventos de autoria/finalização/retificação dependem do escopo de auditoria RN-034, que ainda não está implementado. **Pendências:** D04, D05 e D06 no [índice](../requisitos/README.md).
