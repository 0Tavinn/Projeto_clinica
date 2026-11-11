# RF-023 — Consultar prontuários clínicos

**Revisão documental:** 09/11/2026. **Decisão de acesso:** 25/10/2026, preservada.
**Regra principal:** RN-031.
**Relacionados:** RF-012, RF-022 e RF-024.
**Situação:** política de preparação e continuidade aprovada; implementação parcial.

## 1. Objetivo

Permitir ao dentista autorizado consultar o prontuário do paciente para preparar o atendimento e acompanhar cuidados já realizados.

O prontuário é único para o paciente na clínica. Diferentes dentistas podem receber autorização, sem propriedade exclusiva e sem alteração da autoria dos registros existentes.

## 2. Fundamentos de autorização

O sistema deve distinguir:

- **Preparação:** acesso sustentado por consulta atualmente `CONFIRMED`, com confirmação confiável registrada para aquele paciente e dentista.
- **Continuidade:** acesso sustentado por atendimento registrado pela ação **Concluir atendimento**, com evidência válida, conforme RN-031.

Consulta apenas agendada, pertencimento à clínica e autoria antiga não concedem acesso isoladamente.

A realização do atendimento não deve ser presumida apenas pela confirmação, pelo horário agendado ou pela passagem do tempo. Somente o dentista responsável conclui uma consulta previamente confirmada; `COMPLETED` e a evidência da realização são gravados atomicamente.

## 3. Conteúdo disponível

O dentista autorizado pode:
1. Localizar e consultar o prontuário.
2. Consultar observações gerais.
3. Consultar evoluções finalizadas de todos os autores.
4. Identificar autoria e horários dos registros apresentados.
5. Consultar seus próprios rascunhos.
6. Retornar ao histórico enquanto houver fundamento válido de acesso.

Rascunhos de terceiros não devem ser retornados.

A lista de prontuários acessíveis deve considerar preparação e continuidade. Sua apresentação no painel será alinhada com RF-012 e não substitui o cadastro administrativo de pacientes.

## 4. Reavaliação do acesso

Após ausência ou cancelamento, o sistema deve avaliar todas as origens daquele paciente e dentista na clínica.

- Atendimento anterior válido mantém a continuidade.
- Outra consulta confirmada mantém a preparação.
- Sem atendimento válido e sem outra consulta confirmada, o acesso de preparação deixa de ser permitido.

A recepção registra a situação na Agenda. A API calcula a autorização sem exigir uma operação manual de desvinculação.

A reavaliação não deve apagar as evidências históricas de confirmação ou atendimento.

## 5. Segurança e limites

Cada rota que exponha conteúdo deve verificar autenticação, usuário ativo, perfil/cadastro profissional, clínica e autorização válida.

Administrador, recepção e outra clínica não recebem conteúdo clínico, inclusive observações gerais.

Leitura autorizada não permite alterar registros de terceiros nem escrever em qualquer situação. As condições de registro e finalização pertencem a RF-024.

O acesso destina-se ao acompanhamento assistencial, sem autorização implícita para aula, publicação ou pesquisa.

## 6. Abertura do prontuário

A proposta continua sendo separar consulta e abertura:

- GET consulta sem criar dados.
- Operação explícita abre o prontuário quando autorizada.
- Repetição ou concorrência não cria duplicidade.

O contrato permanece pendente em D02 e exige ajuste coordenado entre backend e frontend.

A existência da autorização não exige prontuário previamente aberto.

## 7. Critérios de aceite

Os IDs existentes foram preservados. O conteúdo dos critérios de permanência foi atualizado para a decisão de 25/10.

Critérios dependentes de decisões abertas continuam condicionais e não representam testes já aprovados.

| ID | Resultado esperado |
|---|---|
| RF-023-CA01 | Dentista autorizado consulta prontuário existente sem criar duplicidade. |
| RF-023-CA02 | Após aprovação de D02, consultar prontuário inexistente não escreve no banco; abertura explícita gera no máximo um prontuário, inclusive sob concorrência. |
| RF-023-CA03 | Administrador, recepção e outra clínica não obtêm conteúdo por telas ou rotas alternativas. |
| RF-023-CA04 | Toda leitura clínica verifica fundamento válido de preparação ou continuidade conforme RN-031. |
| RF-023-CA05 | Dentista autorizado recebe finalizadas de todos os autores e somente seus próprios rascunhos. |
| RF-023-CA06 | Dentistas autorizados utilizam o mesmo prontuário, preservando autoria; escrita segue RF-024. |
| RF-023-CA07 | Acesso negado, prontuário inexistente e falha de conexão recebem tratamento distinto, sem exposição indevida. |
| RF-023-CA08 | Atendimento concluído pelo dentista responsável a partir de `CONFIRMED`, com evidência válida da realização, sustenta acompanhamento futuro, mesmo com cancelamento ou ausência em consultas posteriores. |
| RF-023-CA09 | Perfil, clínica comum ou autoria antiga não concedem acesso sem fundamento válido. |
| RF-023-CA10 | Consulta apenas agendada não concede preparação; confirmação confiável com consulta atualmente `CONFIRMED` sustenta acesso para o paciente e dentista corretos. |
| RF-023-CA11 | Cancelamento ou ausência retiram a preparação somente quando não houver atendimento válido nem outra consulta confirmada que sustente acesso. |
| RF-023-CA12 | Repetição, concorrência e falhas parciais na confirmação ou na conclusão atômica de atendimento não geram autorização indevida. |
| RF-023-CA13 | Eventos de outro paciente ou dentista não concedem nem transferem acesso ao profissional errado. |
| RF-023-CA14 | Após reiniciar API e PostgreSQL, evidências e avaliação de preparação/continuidade permanecem consistentes. |
| RF-023-CA15 | Usuário inativo ou fora da clínica autorizada não consegue utilizar evidências históricas para acessar conteúdo. |
| RF-023-CA16 | Registros antigos seguem procedimento explícito, sem presumir confirmação ou atendimento somente pelo estado atual da consulta. |

## 8. Escopo futuro e pendências

A revogação individual pelo administrador fica fora do escopo obrigatório do MVP e deve permanecer registrada como melhoria futura.

Continuam pendentes:
- Dados antigos, correção de confirmação indevida e alterações dos participantes — parte aberta de D01. A persistência e a consulta das evidências já estão implementadas na API e no SQL.
- Abertura explícita — D02.
- Correção de realização indevida, estados de rascunho/finalização da evolução e atendimento avulso — parte aberta de D03.
- Conteúdo mínimo — D04.
- CRO histórico e retificação — D05.
- Paciente inativo — D06.

## 9. Implementação e impacto

A API registra evidências de confirmação e realização e calcula preparação ou continuidade. As rotas clínicas aplicam a elegibilidade do profissional, a clínica e o fundamento assistencial. A consulta inicial de prontuário ainda pode criá-lo, conforme contrato atual e pendência D02.

A entrega inicial `01a0157` foi complementada por `be7c2f2` no SQL e `ac180a7` na aplicação. O commit `8eeddd5` consolida QA-01 e QA-02. O commit `4c352b2` publica os contratos e as evidências de revalidação.

O [QA de 04/11](../relatorios/qa/2026-11-04-2f7dbfe-qa01-qa02/relatorio.md) exercitou o código então local em PostgreSQL 16.15 descartável, com 10 testes aprovados. Os hashes dos oito arquivos foram reconferidos em 09/11 e correspondem aos arquivos consolidados. O ensaio usou TestClient conectado ao PostgreSQL e uma sondagem de migração em outro banco descartável.

Permanecem a implantação em imagem da API, a adaptação do frontend e a atualização do banco existente. O cliente deve enviar `version` ao editar evolução e `care_occurred_at` com fuso ao concluir consulta. A migração do banco existente depende de inventário e plano de recuperação do DBA.

As decisões adicionais de 02/11 sobre segunda senha, evolução salva antes de concluir, itens ou Sem cobrança, encaminhamento, pagamento externo e correção administrativa estão na [especificação v0.4](../especificacoes/fluxo-atendimento-mvp-2026-11-02.md). Sua implementação terá etapa própria, com os limites e pendências indicados nessa fonte.
