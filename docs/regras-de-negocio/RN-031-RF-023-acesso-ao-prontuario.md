# RN-031 — Acesso e responsabilidade pelos registros clínicos

**Revisão documental:** 09/11/2026. **Decisão de acesso:** 25/10/2026, preservada.
**Requisito principal:** RF-023.
**Requisito relacionado:** RF-024.
**Aprovação:** Paulo Sérgio, líder da equipe.
**Situação:** política aprovada e implementada na API, com revalidação delimitada em PostgreSQL descartável. Implantação e decisões remanescentes seguem pendentes.

## 1. Prontuário e autoria

O prontuário pertence ao paciente no contexto da clínica. Diferentes dentistas autorizados podem consultar o mesmo prontuário e acrescentar suas próprias evoluções, respeitando as condições de escrita.

Não existe dentista proprietário exclusivo do prontuário. Cada evolução mantém seu autor individual.

## 2. Duas condições de acesso

O acesso assistencial pode ser sustentado por:

1. **Preparação:** consulta atualmente `CONFIRMED`, com confirmação confiável registrada para aquele paciente e dentista, na mesma clínica.
2. **Continuidade do cuidado:** atendimento realizado e registrado de forma confiável entre aquele paciente e dentista, na mesma clínica, com evidência da confirmação correspondente.

A confirmação representa a intenção de comparecer. Não comprova presença nem realização do atendimento.

Um agendamento ainda não confirmado não concede acesso por si só.

## 3. Acesso de preparação

A operação autorizada de confirmação da consulta concede acesso de preparação ao dentista responsável.

Esse acesso permite consultar o prontuário, as evoluções finalizadas e os próprios rascunhos, sem dispensar as verificações de perfil, clínica e elegibilidade.

Enquanto a consulta permanecer `CONFIRMED` e a confirmação confiável estiver registrada, ela pode sustentar esse acesso.

A permissão de leitura não autoriza automaticamente criar ou finalizar uma evolução. As condições de escrita continuam em RF-024 e D03/D04.

## 4. Continuidade após atendimento realizado

Quando houver atendimento realizado e registrado com evidência confiável, o dentista mantém acesso para acompanhamento futuro.

Cancelamento ou ausência em consultas posteriores não retiram esse acesso.

O fundamento é a realização do atendimento com aquele profissional, não o tempo de cadastro, a quantidade de agendamentos ou a existência de evoluções antigas.

A ação **Concluir atendimento** registra a realização. Somente o dentista responsável pela consulta pode executá-la, quando a consulta estiver `CONFIRMED` com confirmação confiável registrada. A operação deve gravar `COMPLETED` e a evidência da realização atomicamente: responsável pelo registro, instante do registro e horário informado da realização. O PATCH genérico e a rota específica devem aplicar a mesma regra. Administrador e recepção não podem registrar a conclusão.

A comprovação operacional precisa distinguir:
- Confirmação da consulta.
- Registro de que o atendimento ocorreu.
- Instante e responsável pelo registro, além do horário informado da realização.

O SQL e a API já registram consulta de origem, confirmador e os campos de realização, conforme `be7c2f2` e `ac180a7`. A correção de uma realização indevida continua pendente em D03. Não se presume realização pelo horário agendado ou pela passagem do tempo.

O estado `COMPLETED` isolado, sem evidência suficiente da operação e dos participantes, não deve gerar autorização retroativa automaticamente.

## 5. Ausência ou cancelamento

Ao registrar ausência ou cancelamento na Agenda, o sistema deve reavaliar o acesso daquele paciente e dentista na clínica:

1. Se houver atendimento anterior válido que sustente continuidade, manter o acesso.
2. Caso contrário, se houver outra consulta confirmada que sustente preparação, manter esse acesso de preparação.
3. Se não houver nenhum desses fundamentos, deixar de permitir o acesso de preparação.

A recepção mantém as operações autorizadas de confirmação, cancelamento e registro de ausência na Agenda. Não registra a conclusão nem administra diretamente vínculos de prontuário.

A avaliação considera todas as origens válidas daquele paciente e dentista. O cancelamento de uma consulta não pode eliminar o acesso sustentado por outra origem.

Não apagar concessões ou evidências históricas apenas para retirar uma permissão temporária. A aplicação deve verificar a validade do acesso em cada requisição.

## 6. Visibilidade e restrições

O dentista autorizado pode consultar:
- Dados e observações gerais do prontuário.
- Evoluções finalizadas de todos os autores.
- Seus próprios rascunhos.

Rascunhos de terceiros são privados. Somente o autor pode editar e finalizar seu rascunho, observadas as condições do RF-024.

A autoria de um rascunho não contorna a ausência de autorização para acessar o prontuário.

Toda requisição deve verificar:
- Autenticação e usuário ativo.
- Perfil de dentista e cadastro profissional elegível.
- Clínica do usuário, do paciente e da origem da autorização.
- Existência de fundamento válido de preparação ou continuidade.

Administrador, recepcionista e outra clínica não recebem conteúdo clínico. Poder operar a Agenda não concede leitura do prontuário.

O acesso é para acompanhamento assistencial, sem autorização implícita para aula, publicação ou pesquisa.

## 7. Revogação administrativa futura

A revogação individual de acesso pelo administrador fica registrada como melhoria futura, fora do escopo obrigatório deste MVP.

Essa funcionalidade deverá permitir tratar solicitações de desvinculação sem apagar evoluções e sem exigir leitura clínica pelo administrador.

A perda automática do acesso de preparação por ausência de fundamento válido é diferente dessa futura revogação administrativa.

## 8. Persistência e consistência

O sistema deve preservar as evidências necessárias para distinguir:
- Quem recebeu acesso por confirmação.
- Qual consulta originou essa preparação.
- Se houve atendimento realizado que sustente continuidade.
- Quando e por quem os eventos foram registrados.

Confirmação e registro de sua origem devem ser consistentes e atômicos. Concluir atendimento deve persistir `COMPLETED` e a evidência da realização na mesma operação; a mudança de estado isolada não comprova atendimento. A passagem direta de `SCHEDULED` para `COMPLETED` fica vedada nas novas operações.

Repetição, concorrência ou falha parcial não podem produzir autorização indevida.

A confirmação não deve exigir que o prontuário já esteja aberto. O contrato de abertura permanece em D02.

## 9. Pendências e substituição da decisão anterior

Esta revisão substitui a decisão de 24/10 que mantinha acesso duradouro apenas por confirmação, mesmo após cancelamento ou ausência sem atendimento.

Continuam pendentes:
- Tratamento de dados antigos e aplicação no banco existente — parte aberta de D01.
- Alteração dos participantes após confirmação e correção de confirmação indevida — D01.
- Abertura do prontuário — D02.
- Correção de realização indevida, estados de rascunho/finalização da evolução e atendimento avulso — parte ainda aberta de D03.
- Conteúdo mínimo — D04.
- CRO histórico e retificação — D05.
- Paciente inativo — D06.

Registros antigos não devem receber autorização automática apenas por autoria ou estado atual da consulta. O tratamento do histórico exige procedimento explícito.

A persistência inicial de 24/10 foi complementada pelas evidências de realização e pela integração da API. `8eeddd5` consolida a reconferência do vínculo após bloqueios e o versionamento. O [QA de 04/11](../relatorios/qa/2026-11-04-2f7dbfe-qa01-qa02/relatorio.md), publicado em `4c352b2`, aprovou os cenários descritos com ressalvas, em PostgreSQL 16.15 descartável. A implementação publicada corresponde aos oito hashes registrados pelo QA.

A segunda senha e a recuperação administrativa aprovadas em direção funcional em 02/11 são adicionais ao vínculo assistencial e estão na [especificação v0.4](../especificacoes/fluxo-atendimento-mvp-2026-11-02.md). Seus contratos ainda exigem detalhamento. A aplicação no banco existente e a integração pela interface continuam em etapa própria.
