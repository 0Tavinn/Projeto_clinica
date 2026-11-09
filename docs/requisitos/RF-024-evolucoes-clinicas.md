# RF-024 — Registrar evoluções clínicas

**Revisão documental:** 09/11/2026. **Decisões clínicas:** consultar RN-031 e a especificação de 02/11.
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

A manutenção da leitura após cancelamento ou ausência não significa que houve atendimento. A ação **Concluir atendimento** pertence à Agenda: somente o dentista responsável pode executá-la sobre consulta `CONFIRMED` com confirmação confiável. Ela grava `COMPLETED` e a evidência da realização atomicamente; não equivale a finalizar uma evolução clínica.

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
- Versão inteira do registro, retornada pela API e exigida na edição.
- Data e hora da finalização.

Os estados existentes são `DRAFT` e `FINALIZED`.

Campos obrigatórios na finalização da evolução e preservação histórica de nome/CRO ainda dependem das decisões correspondentes. O horário informado da realização é registrado na conclusão da consulta; não deve ser deduzido do horário agendado nem do instante de digitação da evolução.

## 4. Fluxo esperado

1. A API verifica autenticação, perfil, clínica, autorização de acesso e condições específicas para registrar.
2. Quando houver consulta vinculada, valida conjuntamente paciente, clínica, dentista e situação permitida.
3. O profissional cria ou recupera seu rascunho, respeitando a unicidade existente por consulta.
4. Somente o autor consulta, edita e finaliza seu rascunho. A edição envia a versão lida e recebe conflito se ela estiver desatualizada. A API reconfere a autorização após esperar pelos bloqueios.
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

- **D03 parcialmente fechada:** a conclusão da consulta e a autoria do registro de realização seguem a ação aprovada em RN-031. Permanecem pendentes os estados para criar/finalizar evolução, o atendimento sem agendamento e a correção de realização indevida.
- **D04:** conteúdo mínimo e possibilidade de registrar em nome de outro profissional.
- **D05:** momento da preservação de nome/CRO, tratamento dos registros antigos, autoria e estrutura da retificação.
- **D06:** leitura e escrita quando o paciente estiver inativo.

A proposta de rascunho em `CONFIRMED`/`COMPLETED` e finalização somente em `COMPLETED` ainda não foi aprovada por extensão da regra de leitura.

A finalização é uma operação da aplicação e não equivale a assinatura certificada.

## 7. Implementação encontrada e evidências

A API possui criação, edição e finalização, autoria pela sessão, filtro de finalizadas e rascunhos próprios e bloqueio de edição comum após finalizar. O commit `8eeddd5` consolida a reconferência de autorização sob bloqueios e o controle otimista de versão.

O PATCH de rascunho exige `version` inteira positiva. Edição aceita incrementa a versão. Edição desatualizada retorna 409 e entrada sem versão ou inválida retorna 422. A finalização permanece sem corpo e incrementa a versão.

O [QA de 04/11](../relatorios/qa/2026-11-04-2f7dbfe-qa01-qa02/relatorio.md) aprovou QA-01 e QA-02 no recorte exercitado em PostgreSQL 16.15 descartável. A execução final teve 10 testes aprovados. O commit `4c352b2` registra a evidência e suas ressalvas. A conferência de hashes em 09/11 corresponde aos arquivos testados. O ensaio cobre os cenários descritos no relatório e usa a API por TestClient.

A descrição vazia ainda é aceita pelo contrato atual, e permanecem abertos conteúdo mínimo para finalizar, nome/CRO históricos, retificação e política de paciente inativo. A regra atual permite uma evolução por consulta vinculada. Retificação exige desenho compatível ou revisão explícita dessa restrição.

Em 02/11, Paulo aprovou exigir evolução salva com descrição antes de concluir consulta, podendo permanecer DRAFT. Essa mudança do fluxo é uma implementação futura e não equivale a aprovar todos os estados de escrita ou o conteúdo mínimo para FINALIZED. Consulte a [especificação v0.4](../especificacoes/fluxo-atendimento-mvp-2026-11-02.md).

O frontend precisa enviar `version`, e a migração de versionamento ainda exige preparação para o banco de destino. Imagem implantada, interface e banco existente continuam sujeitos a validação própria.
