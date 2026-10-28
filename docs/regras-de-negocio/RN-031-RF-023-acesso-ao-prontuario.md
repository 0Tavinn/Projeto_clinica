# RN-031 — Acesso e responsabilidade pelos registros clínicos

**Revisão:** 24/10/2026.
**Requisito principal:** RF-023.
**Requisito relacionado:** RF-024.
**Aprovação:** Paulo Sérgio, líder da equipe.
**Situação:** política de concessão e permanência aprovada; implementação pendente.

## 1. Prontuário e responsabilidade

O prontuário pertence ao paciente no contexto da clínica. Ele reúne registros de diferentes profissionais e não possui um dentista exclusivo.

Cada evolução identifica individualmente o dentista responsável por sua autoria. A autorização para consultar o prontuário não permite alterar registros de outros profissionais.

## 2. Concessão do acesso

A confirmação de uma consulta concede ao dentista responsável autorização para consultar o prontuário do paciente daquela consulta, na mesma clínica.

A confirmação deve ser registrada pela operação autorizada da Agenda. Ela representa a confirmação da consulta, não a comprovação de comparecimento ou realização do atendimento.

Uma consulta apenas agendada não gera autorização. Perfil de dentista, pertencimento à clínica, presença do paciente no cadastro e autoria antiga, isoladamente, não concedem acesso.

## 3. Permanência da autorização

Depois da confirmação, a autorização permanece para acompanhamento clínico, mesmo quando a consulta passar para:

- Concluída — `COMPLETED`.
- Ausência — `NO_SHOW`.
- Cancelada — `CANCELED`.

Não haverá expiração automática decorrente dessas alterações no MVP.

Uma nova consulta apenas agendada não remove uma autorização anteriormente concedida.

Uma consulta concluída, cancelada ou com ausência, sem evidência de confirmação anterior, não concede autorização automaticamente.

## 4. Conteúdo permitido

O dentista autorizado pode consultar:

- Dados e observações gerais do prontuário.
- Evoluções finalizadas de todos os profissionais daquele prontuário.
- Seus próprios rascunhos.

Rascunhos de outro autor não devem ser retornados pela API nem apresentados pela interface.

O acesso destina-se ao acompanhamento assistencial do paciente. Não inclui autorização para aula, publicação ou pesquisa.

## 5. Restrições permanentes

Toda requisição deve verificar:

- Autenticação e usuário ativo.
- Perfil de dentista e cadastro profissional elegível.
- Correspondência entre a clínica do usuário, do paciente e da autorização.
- Existência da autorização concedida.

Administrador, recepcionista e usuário de outra clínica não recebem conteúdo clínico por essa autorização.

A permissão para confirmar consultas não concede ao administrador ou à recepção leitura do prontuário.

Somente o autor pode editar e finalizar seu rascunho, observadas as condições específicas do RF-024.

## 6. Revogação futura

A revogação individual do acesso pelo administrador, inclusive por solicitação do paciente, fica fora do MVP.

Essa funcionalidade deverá ser especificada em uma versão posterior. Sua futura implementação não deverá exigir que o administrador leia conteúdo clínico.

Não apresentar essa revogação como funcionalidade disponível.

## 7. Persistência necessária

A concessão deve permanecer verificável após alterações de estado da consulta e reinício da aplicação ou do banco.

Consultar somente o estado atual da consulta não é suficiente para implementar esta regra.

DBA e backend deverão propor como preservar:

- Paciente autorizado.
- Dentista beneficiado.
- Clínica.
- Consulta de origem.
- Data e hora da concessão.

A confirmação e a concessão precisam ser consistentes e atômicas. Repetição ou concorrência não pode produzir autorizações indevidas ou duplicidades inconsistentes.

Este documento não determina uma tabela específica nem autoriza executar migrações.

## 8. Pendências

Continuam pendentes:

- Tratamento de consultas antigas e comprovação de confirmação anterior.
- Alteração de paciente ou dentista depois da confirmação, sem transferência automática da autorização.
- Acesso quando o paciente estiver inativo.
- Contrato de abertura do prontuário.
- Estados permitidos para criar rascunho e finalizar evolução.
- Atendimento sem agendamento.

A autorização duradoura de leitura não permite registrar atendimento em qualquer estado da consulta.

## 9. Situação da implementação

Na referência `9b26c81`, o serviço clínico utiliza basicamente perfil e clínica, sem implementar a concessão persistente definida aqui.

A aprovação desta regra não representa implementação ou aceite dos testes.

**Referências:** RF-023, RF-024, RN-032 e decisões D01–D06.