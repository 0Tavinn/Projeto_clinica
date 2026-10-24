# RF-024 — Registrar evoluções clínicas

**Revisão:** 24/10/2026.
**Regras relacionadas:** RN-031 e RN-032.
**Situação:** implementação parcial; autoria e privacidade definidas, condições operacionais ainda pendentes.

## 1. Objetivo

Permitir ao dentista registrar sua atuação no prontuário do paciente, preservando autoria, conteúdo e horários.

Diferentes dentistas podem acrescentar suas próprias evoluções ao mesmo prontuário.

O autor deve ser identificado a partir da sessão autenticada. O cliente não pode escolher livremente outro profissional como autor.

## 2. Leitura e escrita são permissões distintas

A concessão definida em RN-031 permite consultar o prontuário e as evoluções finalizadas.

Ela não autoriza:

- Ler rascunhos de terceiros.
- Editar ou finalizar registros de outros autores.
- Criar evolução em qualquer estado de consulta.
- Registrar atendimento sem comprovação das condições aprovadas.

A manutenção da leitura após cancelamento ou ausência não significa que houve atendimento.

## 3. Dados do registro

Os campos atuais incluem:

- Paciente.
- Descrição.
- Procedimento realizado, quando informado.
- Observações adicionais.
- Consulta vinculada, quando informada pelo contrato atual.

Os dados de controle incluem:

- Autor.
- Data e hora do registro.
- Estado da evolução.
- Data e hora da finalização.

Os estados existentes são `DRAFT` e `FINALIZED`.

Campos obrigatórios na finalização, momento real do atendimento e preservação histórica de nome/CRO ainda dependem das decisões correspondentes.

## 4. Fluxo esperado

1. A API verifica autenticação, perfil, clínica, autorização de acesso e condições específicas para registrar.
2. Quando houver consulta vinculada, valida conjuntamente paciente, clínica, dentista e situação permitida.
3. O profissional cria ou recupera seu rascunho, respeitando a unicidade existente por consulta.
4. Somente o autor consulta, edita e finaliza seu rascunho.
5. A finalização valida as condições aprovadas, registra seu instante e impede edição ou exclusão comum posterior.
6. Correções de registro finalizado devem seguir o mecanismo de retificação a definir, preservando o original.

Se a operação envolver abertura do prontuário e criação da evolução, ambas devem ser confirmadas na mesma transação ou integralmente revertidas.

A troca do GET que atualmente abre prontuário depende de D02 e de integração com o frontend.

## 5. Critérios de aceite

Os IDs existentes foram preservados. Critérios dependentes de D03–D06 continuam condicionados às decisões de Paulo; não representam funcionalidades já validadas.

| ID | Resultado esperado |
|---|---|
| RF-024-CA01 | A autoria vem da sessão; enviar outro identificador não permite registrar em nome de outro profissional. |
| RF-024-CA02 | Consulta incompatível com paciente, dentista ou clínica é recusada; estados e atendimento avulso seguem a política aprovada. |
| RF-024-CA03 | Somente o autor consulta, edita e finaliza seu rascunho; outro dentista não obtém seu conteúdo nem executa essas ações. |
| RF-024-CA04 | A finalização recusa ausência dos campos mínimos aprovados e registra autoria e horários no caso válido. A proposta mínima é rejeitar descrição vazia ou somente com espaços. |
| RF-024-CA05 | Evolução finalizada não aceita edição ou exclusão comum; o mecanismo de retificação aprovado preserva o original. |
| RF-024-CA06 | Rascunho e finalização são recuperáveis após reinício; falha parcial não confirma apenas parte de uma operação composta. |
| RF-024-CA07 | Perfis administrador, recepção, outro dentista e outra clínica são verificados por HTTP com dados fictícios. |
| RF-024-CA08 | Após definição e implementação de D05, mudanças cadastrais de nome/CRO não reescrevem a identificação histórica preservada na evolução. |
| RF-024-CA09 | Reabrir a consulta permite recuperar o registro existente; duplicidade recebe resposta controlada. |
| RF-024-CA10 | Concorrência não permite editar conteúdo já finalizado; conflitos entre edições de rascunho recebem tratamento explícito para evitar sobrescrita silenciosa. |

## 6. Decisões ainda necessárias

- **D03:** estados que permitem criar rascunho e finalizar, atendimento sem agendamento e identificação do momento do atendimento.
- **D04:** conteúdo mínimo e possibilidade de registrar em nome de outro profissional.
- **D05:** momento da preservação de nome/CRO, tratamento dos registros antigos, autoria e estrutura da retificação.
- **D06:** leitura e escrita quando o paciente estiver inativo.

A proposta de rascunho em `CONFIRMED`/`COMPLETED` e finalização somente em `COMPLETED` ainda não foi aprovada por extensão da regra de leitura.

A finalização é uma operação da aplicação e não equivale a assinatura certificada.

## 7. Implementação encontrada

Na referência `9b26c81`, existem criação, edição e finalização, autoria pela sessão e bloqueio comum após finalizar.

Ainda há lacunas de validação dos vínculos, conteúdo mínimo, privacidade, transações, concorrência, identificação histórica e retificação.

Correções e testes realizados em outro checkout devem ser revisados antes de serem considerados incorporados nesta pasta.

A implementação deve respeitar a regra atual de uma evolução por consulta vinculada. Retificação requer desenho compatível ou revisão explícita dessa restrição.