# Regras de Negócio — Lumina Odonto

## 1. Identificação e referência

- **Versão:** 1.0.
- **Data:** 27/09/2026.
- **Referência principal:** funcionalidades consolidadas na Sprint 04.
- **Referência complementar:** [Requisitos do sistema](./requirements.md).
- **Situação:** regras atuais documentadas e propostas para revisão da equipe.
- **Destino no repositório:** `docs/business-rules.md`.

Este documento descreve as condições que orientam as operações do Lumina Odonto. O relatório da Sprint 04 e os testes relatados pela equipe têm prioridade sobre propostas anteriores quando houver divergências.

As regras identificadas como atuais representam o comportamento documentado ou demonstrado na Sprint 04. Esta elaboração não inclui uma nova inspeção do código, das migrações ou das restrições completas de `appointments`.

As regras da Agenda são propostas para a Sprint 05. Devem ser revisadas por Tarcísio e João, alinhadas com Caio e Otávio e registradas como aprovadas antes de serem utilizadas como contrato definitivo de implementação.

### 1.1 Situações das regras

| Situação | Significado |
|---|---|
| Atual — Sprint 04 | Comportamento documentado ou confirmado pelos testes relatados da entrega atual. |
| Proposta — Sprint 05 | Regra recomendada para Agenda, sujeita à validação da equipe e do schema. |
| Melhoria proposta | Evolução sugerida, ainda sem implementação confirmada. |
| Planejada — etapa futura | Regra para módulos que ainda não estão funcionais. |

Os identificadores `RN-001` e seguintes pertencem a este catálogo. Alterações posteriores devem preservar os identificadores existentes para manter a relação com requisitos e testes.

## 2. Matriz de permissões

### 2.1 Permissões atuais

| Operação | Administrador | Recepcionista | Dentista |
|---|---|---|---|
| Autenticar e encerrar a própria sessão | Permitido | Permitido | Permitido |
| Cadastrar usuários da equipe | Permitido | Negado | Negado |
| Listar usuários da equipe | Permitido | Negado | Negado |
| Cadastrar pacientes | Permitido | Permitido | Permitido |
| Listar e consultar pacientes da clínica | Permitido | Permitido | Permitido |
| Editar pacientes | Permitido | Permitido | Permitido |
| Inativar pacientes | Permitido | Permitido | Negado |

O acesso do dentista aos pacientes da clínica não equivale, na versão atual, a uma regra de acesso apenas aos pacientes atendidos por ele. Essa restrição adicional dependeria de decisão e implementação próprias.

### 2.2 Permissões propostas para Agenda

| Operação | Administrador | Recepcionista | Dentista |
|---|---|---|---|
| Consultar agenda e detalhes | Agenda da clínica | Agenda da clínica | Próprios atendimentos |
| Criar consulta | Permitido | Permitido | Negado |
| Editar ou reagendar consulta | Permitido | Permitido | Negado |
| Cancelar consulta | Permitido | Permitido | Negado |
| Registrar conclusão ou ausência | A definir | A definir | Próprios atendimentos |

Esta segunda matriz é uma proposta. As permissões da Agenda não devem ser deduzidas das permissões do CRUD de pacientes. A equipe deve decidir expressamente quem poderá registrar conclusão e ausência além do dentista responsável.

## 3. Clínica, usuários e autenticação

### RN-001 — Vinculação à clínica

Todo usuário da equipe e todo paciente devem estar vinculados a uma clínica. Nos cadastros realizados por usuários autenticados, a clínica deve ser obtida da sessão validada pelo backend. O solicitante não pode escolher livremente outra clínica para acessar ou alterar seus registros.

**Situação:** atual — Sprint 04. O isolamento completo deve ser confirmado por testes com duas clínicas.
**Requisitos relacionados:** RF-005, RF-006 e RF-008.

### RN-002 — Perfis de acesso da equipe

Os perfis aceitos no módulo atual são `ADMINISTRATOR`, `RECEPTIONIST` e `DENTIST`. O backend deve rejeitar perfis que não pertençam a esse conjunto. Um paciente cadastrado não recebe automaticamente uma conta de acesso.

**Situação:** atual — Sprint 04.
**Requisitos relacionados:** RF-001 e RF-004.

### RN-003 — Condições para autenticação

O acesso exige uma conta existente, ativa e com senha válida. Conta inexistente e senha incorreta devem produzir uma mensagem genérica de credenciais inválidas. Contas inativas devem ter o acesso recusado.

**Situação:** atual — Sprint 04.
**Requisitos relacionados:** RF-001 e RF-002.

### RN-004 — Administração da equipe

Somente o administrador pode cadastrar e listar usuários da equipe da sua clínica. Essa autorização deve ser verificada na API mesmo quando o solicitante tenta acessar diretamente o endpoint, sem utilizar a interface.

**Situação:** atual — Sprint 04.
**Requisitos relacionados:** RF-004, RF-006 e RF-007.

### RN-005 — Campos do cadastro de usuário

O cadastro exige nome completo, e-mail, CPF, senha e perfil. O telefone é opcional. A clínica é definida pela regra RN-001. O perfil deve ser enviado com o identificador aceito pela API.

**Situação:** atual — Sprint 04. Os limites de tamanho e de senha devem seguir os schemas efetivamente utilizados pela API; este documento não cria limites novos.
**Requisitos relacionados:** RF-006 e RF-013.

### RN-006 — Unicidade de usuários

E-mail e CPF de usuários devem ser únicos em toda a tabela `users`, conforme as restrições apresentadas do PostgreSQL. A duplicidade deve ser recusada sem criar um segundo registro. Essa abrangência global é diferente da unicidade de pacientes por clínica.

**Situação:** atual — Sprint 04.
**Requisitos relacionados:** RF-006 e RF-013.

### RN-007 — Administrador inicial

O administrador inicial é criado pelo procedimento de seed em um banco previamente preparado. A execução repetida não deve criar uma segunda conta com o mesmo e-mail nem redefinir silenciosamente a senha de uma conta existente. Os demais usuários são cadastrados pelo administrador autenticado.

**Situação:** atual — Sprint 04, conforme o script informado.
**Requisito relacionado:** RF-006.

### RN-008 — Permissões sem herança automática

Cada operação deve possuir uma autorização explícita. Ter permissão para cadastrar ou editar pacientes não concede permissão para inativá-los ou administrar a equipe. A ação de inativação é exclusiva do administrador e da recepcionista.

**Situação:** atual — Sprint 04.
**Requisitos relacionados:** RF-004 e RF-011.

## 4. Cadastro e gestão de pacientes

### RN-009 — Campos obrigatórios de paciente

O cadastro de paciente exige nome completo, CPF, número de prontuário e data de nascimento. Telefone, e-mail e endereço são opcionais na estrutura atual. O paciente deve pertencer à clínica do usuário autenticado.

**Situação:** atual — Sprint 04.
**Requisitos relacionados:** RF-008 e RF-013.

### RN-010 — Identificação de paciente por clínica

Não pode existir mais de um paciente com o mesmo CPF na mesma clínica, nem mais de um paciente com o mesmo número de prontuário na mesma clínica. As restrições são aplicadas aos pares `(clinic_id, cpf)` e `(clinic_id, medical_record_number)`.

Uma atualização deve desconsiderar o próprio registro ao verificar duplicidade. Alterar o telefone de um paciente sem modificar seu CPF não pode gerar conflito com o CPF desse mesmo paciente.

**Situação:** atual — Sprint 04.
**Requisitos relacionados:** RF-008, RF-010 e RF-013.

### RN-011 — E-mail de paciente

O e-mail de paciente é opcional e deve ter formato válido quando informado. Na modelagem apresentada, esse campo não é exclusivo: dois pacientes podem compartilhar o mesmo endereço de e-mail, por exemplo, em um contato familiar.

**Situação:** atual — Sprint 04, conforme a modelagem informada.
**Requisito relacionado:** RF-013.

### RN-012 — Dados cadastrais válidos

Campos obrigatórios não podem ser vazios. A data de nascimento não pode estar no futuro. O CPF deve respeitar o formato numérico aceito pela API. A comprovação de validação dos dígitos verificadores depende da revisão do código e não é presumida neste documento.

**Situação:** atual — Sprint 04, conforme as validações relatadas; a equivalência das validações no frontend e no backend deve ser conferida.
**Requisito relacionado:** RF-013.

### RN-013 — Inativação lógica

A operação de exclusão disponível na interface deve alterar `is_active` para falso e manter o paciente no banco. A inativação não deve remover o histórico nem os vínculos existentes com consultas e prontuários.

**Situação:** atual — Sprint 04.
**Requisito relacionado:** RF-011.

### RN-014 — Duplicidade após inativação

A inativação não libera o CPF ou o número de prontuário para reutilização na mesma clínica. As restrições de unicidade continuam aplicadas ao registro preservado. Uma nova tentativa de cadastro com esses identificadores deve ser recusada.

**Situação:** atual, conforme as restrições de unicidade apresentadas. Um fluxo de reativação ainda não foi confirmado e depende de decisão da equipe.
**Requisitos relacionados:** RF-011 e RF-013.

### RN-015 — Número cadastral e prontuário clínico

O campo `medical_record_number` identifica o cadastro do paciente e, na versão atual, é preenchido manualmente. Sua presença não comprova a existência de histórico clínico, evoluções ou recursos de IA funcionais.

**Situação:** atual — Sprint 04.
**Requisitos relacionados:** RF-008, RF-023 e RF-033.

## 5. Agenda e consultas — proposta para Sprint 05

Antes da implementação, a equipe deve conferir campos, tipos, restrições, valores de status e relacionamentos da tabela `appointments`. As regras abaixo descrevem o comportamento recomendado e não declaram que a Agenda já esteja funcionando.

### RN-016 — Dentista elegível para agendamento

Uma consulta deve referenciar um registro profissional de `dentists`, vinculado a um usuário ativo com perfil `DENTIST`. Ter somente uma conta de usuário com esse perfil não é suficiente quando o relacionamento da consulta exige `dentists.id`.

O cadastro profissional deve possuir os dados obrigatórios da modelagem: usuário, número de CRO e UF do CRO. A especialidade é opcional na estrutura apresentada. O par CRO/UF e o vínculo com o usuário devem respeitar as restrições de unicidade existentes. O cadastro deve validar formato e preenchimento; não representa verificação automática do registro profissional junto ao conselho.

**Situação:** proposta — Sprint 05.
**Requisito relacionado:** RF-016.

### RN-017 — Participantes da mesma clínica

A consulta deve estar vinculada à clínica autenticada, a um paciente dessa clínica e a um dentista cujo usuário pertença à mesma clínica. O backend deve recusar identificadores de participantes de outra clínica, mesmo que enviados manualmente.

**Situação:** proposta — Sprint 05.
**Requisitos relacionados:** RF-005 e RF-018.

### RN-018 — Atividade dos participantes

Somente pacientes ativos e dentistas com conta ativa podem receber novos agendamentos ou reagendamentos. Consultas anteriores devem continuar preservadas quando um participante se tornar inativo.

O tratamento de consultas futuras já existentes após a inativação de um participante precisa de decisão da equipe. Não se deve presumir cancelamento automático sem regra aprovada.

**Situação:** proposta — Sprint 05.
**Requisitos relacionados:** RF-016, RF-018 e RF-020.

### RN-019 — Data, horário e duração

Uma nova consulta deve possuir data e horário futuros, duração em minutos maior que zero e horário de término calculado a partir do início e da duração. Reagendamentos devem respeitar as mesmas condições.

Os limites de duração, a duração sugerida, os dias de funcionamento e a faixa de horários devem ser definidos com a clínica. Nenhum valor de exemplo deve ser adotado automaticamente como regra aprovada.

**Situação:** proposta — Sprint 05.
**Requisitos relacionados:** RF-018 e RF-020.

### RN-020 — Ausência de sobreposição por dentista

Um dentista não pode possuir duas consultas que ocupem o mesmo intervalo de tempo. Há conflito quando o início da nova consulta ocorre antes do fim da consulta existente e seu término ocorre depois do início da consulta existente.

Consultas consecutivas são permitidas: uma consulta pode começar exatamente quando a anterior termina. Na edição, o próprio agendamento deve ser desconsiderado na comparação. Consultas canceladas não devem ocupar disponibilidade.

Essa garantia deve resistir a duas solicitações simultâneas. Apenas consultar horários e depois inserir, sem proteção transacional ou restrição equivalente, pode permitir conflitos concorrentes.

**Situação:** proposta — Sprint 05. Os demais status que ocupam disponibilidade precisam ser definidos pela equipe.
**Requisitos relacionados:** RF-018 e RF-020.

### RN-021 — Visibilidade da agenda

O administrador e a recepcionista podem consultar a agenda da clínica. O dentista pode consultar os agendamentos em que seja o profissional responsável. Filtros enviados pelo frontend não devem permitir ampliar essa autorização.

**Situação:** proposta — Sprint 05.
**Requisitos relacionados:** RF-017 e RF-019.

### RN-022 — Alteração e reagendamento

Somente administrador e recepcionista podem alterar os dados administrativos ou reagendar uma consulta, conforme a matriz proposta. Toda alteração de paciente, dentista, data, horário ou duração exige nova validação de vínculo, atividade e disponibilidade.

A consulta deve manter sua identificação ao ser reagendada. Alterações em consultas concluídas, canceladas ou com ausência registrada dependem das transições aprovadas na RN-024.

**Situação:** proposta — Sprint 05.
**Requisito relacionado:** RF-020.

### RN-023 — Cancelamento sem exclusão física

O cancelamento deve preservar o registro da consulta e alterar sua situação para cancelada. Somente administrador e recepcionista podem executar essa ação, conforme a matriz proposta. O horário cancelado deve voltar a ficar disponível.

A obrigatoriedade de motivo e eventual prazo mínimo de cancelamento dependem de aprovação da equipe e de compatibilidade com o schema.

**Situação:** proposta — Sprint 05.
**Requisito relacionado:** RF-021.

### RN-024 — Estados e transições da consulta

A equipe deve aprovar os estados aceitos e as mudanças possíveis antes da implementação. Como proposta mínima, a consulta inicia como agendada e pode passar para concluída, cancelada ou ausência.

| Origem proposta | Destino proposto | Condição |
|---|---|---|
| Agendada | Concluída | Atendimento realizado e ação de um perfil autorizado. |
| Agendada | Cancelada | Cancelamento realizado pelo administrador ou pela recepcionista. |
| Agendada | Ausência | Horário já iniciado e ausência registrada por perfil autorizado. |
| Concluída, cancelada ou ausência | Outro estado | Bloqueado no fluxo comum; eventual correção precisa de regra própria. |

Os nomes acima são conceitos de negócio. Os identificadores enviados pela API devem ser definidos após conferir a restrição de status do PostgreSQL. Um estado de confirmação, se necessário, deve ser acrescentado com suas transições e permissões.

**Situação:** proposta — Sprint 05.
**Requisitos relacionados:** RF-018 a RF-022.

### RN-025 — Atuação do dentista no próprio atendimento

O dentista pode registrar conclusão ou ausência somente nas consultas sob sua responsabilidade, conforme os estados aprovados. Não pode utilizar a atualização de status para trocar paciente, dentista, data ou duração, nem para cancelar consultas.

As permissões do administrador e da recepcionista para conclusão e ausência permanecem pendentes de decisão.

**Situação:** proposta — Sprint 05.
**Requisito relacionado:** RF-022.

### RN-026 — Referência de tempo consistente

A Agenda deve utilizar uma referência de tempo única da clínica para comparar horários, impedir agendamentos no passado e apresentar as consultas. O frontend e a API devem trocar horários sem ambiguidades de fuso. A equipe deve confirmar o tipo de `scheduled_at` e definir como os horários serão armazenados e exibidos.

**Situação:** proposta — Sprint 05.
**Requisitos relacionados:** RF-017, RF-018 e RF-020.

## 6. Melhorias propostas nos cadastros

### RN-027 — CPF com máscara visual

O formulário pode apresentar CPF com pontos e traço enquanto o usuário digita números. Antes do envio, o valor deve ser convertido para o formato numérico esperado pela API. A máscara não substitui a validação do CPF.

**Situação:** melhoria proposta.
**Requisito relacionado:** RF-031.

### RN-028 — Telefone com DDD

O formulário deve aceitar e apresentar os formatos de telefone fixo e celular com DDD definidos para o projeto. Não deve acrescentar automaticamente um nono dígito a um telefone fixo nem transformar um número incompleto em um número aparentemente válido. O formato enviado deve respeitar o contrato da API.

**Situação:** melhoria proposta.
**Requisito relacionado:** RF-031.

### RN-029 — Endereço organizado e consulta de CEP

A interface pode separar CEP, logradouro, número, complemento, bairro, cidade e UF. Enquanto o banco mantiver apenas `address`, esses valores devem ser reunidos em um texto para envio à API. A edição deve preservar endereços existentes; não se deve presumir que todo texto antigo possa ser separado automaticamente sem perda.

A consulta de CEP deve preencher somente os dados disponíveis e permitir correção manual. Falha no serviço de CEP não deve impedir o preenchimento manual. Número e complemento continuam sob responsabilidade do usuário.

**Situação:** melhoria proposta.
**Requisito relacionado:** RF-032.

### RN-030 — Geração automática de número de prontuário

O backend pode gerar o número de prontuário no cadastro, garantindo unicidade por clínica e evitando conflito entre solicitações simultâneas. O identificador não deve depender de CPF, nome ou outros dados pessoais, nem ser reutilizado após inativação.

Como exemplo sujeito à aprovação, pode ser utilizado `LO-001-2026-000001`. A geração automática ainda não faz parte do comportamento confirmado na Sprint 04.

**Situação:** melhoria proposta.
**Requisito relacionado:** RF-033.

## 7. Prontuário, auditoria e IA — etapas futuras

### RN-031 — Acesso e responsabilidade pelos registros clínicos

O acesso ao conteúdo clínico e o registro de evoluções devem ser autorizados de forma específica. Como proposta inicial, evoluções são registradas por dentistas autorizados e vinculadas ao paciente, à clínica, ao profissional e à data do atendimento. A permissão para editar dados cadastrais de pacientes não concede automaticamente acesso irrestrito ao prontuário clínico.

**Situação:** planejada — etapa futura. A matriz clínica precisa ser aprovada.
**Requisitos relacionados:** RF-023 e RF-024.

### RN-032 — Preservação do histórico clínico

Evoluções finalizadas não devem ser sobrescritas silenciosamente. A equipe deve definir um fluxo de correção ou complementação que preserve autor, data e conteúdo original. As regras de rascunho, finalização e correção devem ser aprovadas antes da implementação.

**Situação:** planejada — etapa futura.
**Requisito relacionado:** RF-024.

### RN-033 — IA como apoio ao profissional

Conteúdo gerado por IA deve ser identificado como tal e disponibilizado para revisão do dentista. Uma sugestão não deve se tornar automaticamente diagnóstico, prescrição ou evolução clínica assinada pelo profissional.

A equipe deve definir quais dados serão utilizados, como restringir o acesso, quando gerar os resumos e como registrar sua origem. As propostas anteriores de GPU, processamento noturno e lote não constituem decisões finais de implementação.

**Situação:** planejada — etapa futura.
**Requisito relacionado:** RF-025.

### RN-034 — Operações com rastreabilidade

A equipe deve definir quais ações exigem auditoria, por exemplo, alterações de perfil, inativações, cancelamentos e alterações clínicas. O registro deve identificar responsável, ação, recurso e momento. Senhas e tokens não devem compor o conteúdo de auditoria.

**Situação:** planejada — etapa futura; o fluxo de auditoria ainda não foi confirmado.
**Requisito relacionado:** RF-026.

Portal do paciente, serviços e relatórios financeiros permanecem no escopo congelado. Novas regras desses módulos devem ser definidas quando sua implementação for retomada.

## 8. Decisões necessárias antes da implementação da Agenda

| Decisão | Encaminhamento proposto | Responsáveis pela definição |
|---|---|---|
| Cadastro profissional do dentista | Definir campos, endpoint e vínculo `users` → `dentists` → `appointments`. | Tarcísio e João, com alinhamento do frontend. |
| Estados das consultas | Conferir restrições do banco e aprovar transições e nomes da API. | Tarcísio e João, com revisão da equipe. |
| Conclusão e ausência | Confirmar se administrador e recepcionista também poderão registrar essas situações. | Equipe, com implementação por Tarcísio e João. |
| Horários e duração | Definir funcionamento, duração sugerida e limites por consulta. | Paulo com a clínica; equipe valida a proposta. |
| Tempo e fuso | Conferir `scheduled_at` e padronizar armazenamento e exibição. | Paulo, Tarcísio e João, com alinhamento de Caio. |
| Conflito do paciente | Decidir se um paciente poderá ter consultas simultâneas com dentistas diferentes. | Equipe. |
| Cancelamento | Definir necessidade de motivo e eventual prazo mínimo. | Equipe com a clínica. |
| Inativação com consultas futuras | Definir bloqueio, aviso ou necessidade de cancelamento/reagendamento prévio. | Equipe. |
| Disponibilidade e concorrência | Definir proteção que impeça dois agendamentos simultâneos para o mesmo intervalo do dentista. | Tarcísio e João, com revisão do banco por Paulo. |

Essas pendências devem ser registradas no quadro da Sprint. Uma proposta neste documento não deve ser apresentada no relatório como implementada sem confirmação por teste.

## 9. Cenários mínimos para validar as regras

| Cenário | Resultado esperado | Referência |
|---|---|---|
| Recepcionista tenta cadastrar ou listar a equipe | Operação negada. | RN-004 |
| Dentista cadastra e edita paciente da clínica | Operações permitidas. | Matriz atual e RN-008 |
| Dentista tenta inativar paciente | Operação negada e registro preservado. | RN-008 e RN-013 |
| Novo paciente usa CPF de outro paciente da mesma clínica | Cadastro recusado por duplicidade. | RN-010 |
| Paciente mantém o próprio CPF ao editar telefone | Edição permitida, sem falso conflito. | RN-010 |
| Novo paciente usa identificador de paciente inativo da mesma clínica | Cadastro recusado por duplicidade. | RN-014 |
| Usuário tenta consultar ou alterar registro de outra clínica | Acesso recusado, sem exposição do registro. | RN-001 e RN-017 |
| Consulta utiliza paciente inativo ou dentista inelegível | Agendamento recusado. | RN-016 e RN-018 |
| Consulta é criada no passado ou com duração inválida | Agendamento recusado. | RN-019 |
| Duas consultas se sobrepõem para o mesmo dentista | Segundo agendamento recusado. | RN-020 |
| Consulta começa exatamente no término da anterior | Agendamento permitido, se as demais regras forem atendidas. | RN-020 |
| Duas requisições simultâneas tentam reservar o mesmo horário | No máximo uma reserva conflitante é persistida. | RN-020 |
| Consulta é cancelada | Registro preservado e horário liberado. | RN-023 |
| Dentista tenta alterar consulta de outro dentista | Operação negada. | RN-021 e RN-025 |
| Atualização utiliza transição de status proibida | Alteração recusada e estado anterior preservado. | RN-024 |
| Serviços são reiniciados após uma operação salva | Dados continuam recuperáveis. | RF-015 e requisitos de persistência |

Os cenários atuais devem compor os testes de regressão. Os cenários da Agenda só podem ser considerados concluídos após aprovação das regras correspondentes e execução dos testes.

## 10. Manutenção do documento

Quando uma regra for modificada, a equipe deve registrar a justificativa, atualizar os requisitos relacionados, ajustar os testes e informar o frontend quando houver mudança no contrato da API. Regras descontinuadas devem manter seu identificador e indicar a substituição.

| Versão | Data | Alteração |
|---|---|---|
| 1.0 | 27/09/2026 | Regras atuais da Sprint 04, propostas de Agenda para Sprint 05 e evoluções futuras. |

As evidências de implementação devem referenciar o commit ou Pull Request e os testes correspondentes. A aprovação das regras da Agenda deve ser registrada antes de alterar sua situação neste documento.
