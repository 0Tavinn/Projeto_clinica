# RF-023 — Consultar prontuários clínicos

**Revisão:** 24/10/2026.
**Regra principal:** RN-031.
**Relacionados:** RF-012, RF-022 e RF-024.
**Situação:** concessão e permanência aprovadas por Paulo Sérgio; implementação parcial.

## 1. Objetivo

Permitir ao dentista autorizado consultar o prontuário do paciente para preparar e acompanhar seu atendimento.

O paciente mantém um prontuário na clínica, compartilhado entre os profissionais autorizados. A autoria de cada evolução permanece individual.

## 2. Ator e autorização

O ator é o dentista autenticado, ativo e com cadastro profissional elegível.

A autorização é concedida quando uma consulta entre aquele paciente e dentista é confirmada pela operação autorizada da Agenda.

Uma consulta apenas agendada não concede acesso.

A autorização permanece após conclusão, ausência ou cancelamento posteriores à confirmação, conforme RN-031.

## 3. Funcionalidade

O sistema deve permitir ao dentista autorizado:

1. Localizar e consultar o prontuário do paciente.
2. Consultar suas observações gerais.
3. Consultar as evoluções finalizadas de todos os autores.
4. Identificar autoria e horários apresentados nos registros.
5. Consultar seus próprios rascunhos.
6. Retornar ao prontuário posteriormente para acompanhamento.

A apresentação de uma lista de prontuários autorizados deve ser alinhada ao painel do dentista em RF-012. Essa lista não deve ser confundida com o cadastro geral de pacientes da clínica.

Rascunhos de outros autores não devem ser disponibilizados.

## 4. Verificações em cada consulta

A API deve validar usuário ativo, perfil profissional, clínica e autorização persistida.

A existência do paciente no cadastro, uma URL conhecida ou um botão na interface não substitui essas verificações.

Administrador, recepção e outra clínica não devem obter conteúdo clínico por rotas alternativas, inclusive pelo campo de observações gerais.

## 5. Abertura do prontuário

A consulta e a abertura do prontuário são operações distintas no comportamento proposto.

A proposta é:

- GET consulta sem criar dados.
- Operação explícita abre o prontuário quando autorizada.
- Tentativas repetidas ou concorrentes não criam prontuários duplicados.

Essa alteração depende da decisão D02 e do contrato coordenado entre backend e frontend. A política de acesso aprovada não representa aprovação automática desse contrato.

## 6. Critérios de aceite

Os IDs anteriores foram preservados. Os critérios representam o comportamento esperado; não são resultados de testes já aprovados.

| ID | Resultado esperado |
|---|---|
| RF-023-CA01 | Dentista autorizado consulta prontuário existente sem criar duplicidade. |
| RF-023-CA02 | Após aprovação de D02, consultar prontuário inexistente não escreve no banco; abertura explícita gera no máximo um prontuário, inclusive sob concorrência. |
| RF-023-CA03 | Administrador, recepção e outra clínica não obtêm conteúdo clínico por telas ou rotas alternativas. |
| RF-023-CA04 | A API verifica a concessão definida em RN-031 em toda leitura clínica. |
| RF-023-CA05 | Dentista autorizado recebe evoluções finalizadas de todos os autores e somente seus próprios rascunhos. |
| RF-023-CA06 | Dentistas autorizados utilizam o mesmo prontuário, preservando autoria; as operações de escrita seguem RF-024. |
| RF-023-CA07 | Acesso negado, prontuário inexistente e falha de conexão recebem tratamento distinto, sem exposição indevida. |
| RF-023-CA08 | Após confirmação e conclusão da consulta, a autorização permanece para acompanhamento. |
| RF-023-CA09 | Dentista sem autorização não recebe conteúdo apenas por pertencer à clínica ou ter autoria antiga. |
| RF-023-CA10 | Consulta somente agendada, sem autorização anterior, não libera acesso; confirmação concede ao paciente e dentista corretos. |
| RF-023-CA11 | Cancelamento ou ausência posteriores à confirmação mantêm o acesso, inclusive quando aquela era a única consulta entre os participantes. |
| RF-023-CA12 | Repetição ou concorrência na confirmação não produz concessões inconsistentes; falha da operação não deixa autorização indevida. |
| RF-023-CA13 | Confirmar consulta de outro paciente ou dentista não concede acesso ao profissional errado. |
| RF-023-CA14 | A autorização permanece verificável após reiniciar API e PostgreSQL. |
| RF-023-CA15 | Usuário inativo ou fora da clínica autorizada não consegue utilizar a concessão para acessar conteúdo. |
| RF-023-CA16 | Registros antigos seguem tratamento explícito, sem presumir confirmação somente pelo estado atual da consulta. |

## 7. Escopo futuro e pendências

A revogação individual pelo administrador fica fora do MVP.

Continuam pendentes:

- Abertura explícita e contrato HTTP — D02.
- Condições para escrever e finalizar — D03/D04.
- Tratamento de paciente inativo — D06.
- Migração das autorizações antigas e alteração posterior dos participantes — D01.

A leitura autorizada não permite editar registros de terceiros nem registrar atendimento em qualquer situação.

## 8. Implementação encontrada

Na referência `9b26c81`, o GET cria prontuário ausente, e a autorização utiliza basicamente perfil e clínica. A listagem pode incluir rascunhos de outros autores.

Esse comportamento ainda não atende à política de RN-031.

Alterações ou testes realizados em outros checkouts não devem ser apresentados como integrados nesta pasta sem conferência.

A implementação deverá envolver autorização clínica, confirmação da Agenda, persistência, interface e testes no PostgreSQL utilizado pelo projeto.