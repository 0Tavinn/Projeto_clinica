# RN-031 — Acesso e responsabilidade pelos registros clínicos

**Revisão:** 23/10/2026. **RF relacionados:** [RF-023](../requisitos/RF-023-prontuario-do-paciente.md) e [RF-024](../requisitos/RF-024-evolucoes-clinicas.md).

## Direção definida por Paulo

- O prontuário é do paciente na clínica e reúne atendimentos de profissionais diferentes. Não é atribuído a um dentista exclusivo permanente.
- Cada evolução identifica o dentista responsável por aquele registro. Um novo profissional acrescenta sua própria evolução ao mesmo prontuário, preservando a autoria das anteriores.
- Consulta mantém seu responsável pelo atendimento. A relação consulta–dentista organiza a Agenda; não transfere o prontuário para esse profissional.

## Regras operacionais propostas

1. Validar perfil, clínica, elegibilidade profissional e política de acesso em toda leitura e escrita, inclusive resumo de IA. Não confiar apenas em filtros ou botões da tela.
2. Conservar o bloqueio de conteúdo clínico para administrador, recepção e outra clínica. O alcance da leitura entre dentistas da mesma clínica depende de D01; ausência de vínculo exclusivo não significa acesso irrestrito.
3. Limitar leitura de rascunho ao autor; permitir histórico finalizado de outros autores conforme D01. O histórico é compartilhável para continuidade do cuidado quando autorizado.
4. Ler por GET sem criar dados e oferecer abertura explícita conforme D02. Criar no máximo um prontuário por paciente, inclusive diante de concorrência.
5. Separar permissões para preparar atendimento, salvar rascunho e finalizar. A proposta anterior de exigir `COMPLETED` para todo o fluxo foi revisada; os estados exatos seguem D03.
6. Quando houver agendamento, verificar conjuntamente paciente, clínica, dentista e situação permitida. Atendimento avulso exige regra aprovada para identificar atendimento, profissional e momento; um campo nulo não comprova autorização.

## Situação encontrada

A API usa paciente e clínica no prontuário e dentista em cada evolução, compatíveis com a direção definida. Ela bloqueia outros perfis e outra clínica, porém não aplica política assistencial específica nem privacidade dos rascunhos. O GET abre automaticamente. A Agenda restringe próprias consultas, mas o cadastro lista os pacientes da clínica inteira.

**Pendências:** D01, D02, D03 e D06 no [índice de decisões](../requisitos/README.md). A implementação dependente deve aguardar a política pertinente; correções independentes de integridade podem avançar. Nenhuma nova relação exclusiva paciente–dentista é requerida por esta regra.
