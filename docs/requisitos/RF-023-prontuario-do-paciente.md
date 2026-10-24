# RF-023 — Consultar prontuários clínicos

**Revisão:** 23/10/2026. **Situação:** implementação parcial; diretrizes de Paulo e propostas operacionais abaixo. **Regra relacionada:** [RN-031](../regras-de-negocio/RN-031-acesso-e-responsabilidade-pelo-prontuario.md). **Decisões:** D01, D02, D03 e D06 no [índice](README.md).

## Objetivo e direção definida

Permitir que o dentista autorizado consulte o prontuário do paciente para preparar e acompanhar o atendimento. Um paciente conserva o mesmo prontuário na clínica ao longo de consultas com profissionais diferentes. A autoria é identificada em cada evolução; não se exige associação exclusiva permanente entre paciente e dentista.

**Ator:** dentista autenticado com cadastro profissional elegível. **Entradas:** paciente e consulta, quando o acesso vier da Agenda. **Saída:** dados do prontuário e histórico autorizado. Perfil, clínica e política de leitura são conferidos pela API em cada operação.

## Fluxo recomendado para aprovação

1. O dentista abre uma consulta sob sua responsabilidade ou pesquisa um paciente permitido pela política aprovada. O painel de atendimentos do dia é um refinamento de RF-012.
2. A API confere elegibilidade do usuário, clínica do paciente e autorização para leitura. A existência do paciente na lista não basta para autorizar conteúdo clínico.
3. A consulta do prontuário não cria dados. Se inexistente, a interface informa a situação e oferece a operação explícita de abertura somente a quem tiver permissão (D02).
4. A tela reúne últimas evoluções finalizadas e acesso ao histórico completo autorizado, ordenado e com identificação do autor. Rascunhos aparecem apenas ao autor como proposta de privacidade.
5. O dentista pode consultar o histórico e preparar o registro durante o atendimento; a matriz de estados da consulta ainda será fechada em D03. Não exigir consulta concluída para toda leitura preparatória.
6. A evolução atual segue RF-024. O resumo opcional segue RF-025 e não bloqueia o acesso aos registros originais.

## Critérios de aceite

Os critérios mantêm os IDs do detalhamento anterior; representam o comportamento pretendido após fechar as decisões, não testes já aprovados.

| ID | Resultado verificável |
|---|---|
| RF-023-CA01 | Dentista autorizado consulta o prontuário existente sem criar outro. |
| RF-023-CA02 | Consultar prontuário inexistente não escreve no banco; a abertura explícita aprovada gera no máximo um prontuário, inclusive em tentativas simultâneas. |
| RF-023-CA03 | Administrador, recepção e outra clínica não obtêm conteúdo por telas ou rotas alternativas, conforme a matriz clínica proposta. |
| RF-023-CA04 | A política de leitura aprovada é aplicada no backend; a ausência de vínculo exclusivo não amplia automaticamente a permissão. |
| RF-023-CA05 | Histórico respeita visibilidade de registros de outros autores e privacidade dos rascunhos conforme a política aprovada. |
| RF-023-CA06 | Dois dentistas autorizados acrescentam registros ao mesmo prontuário sem trocar autoria dos anteriores. |
| RF-023-CA07 | Acesso negado, ausência de prontuário e falha de conexão recebem mensagens distintas, sem exposição de dados de outra clínica. |

## Comportamento atual e dependências

`GET /api/v1/patients/{patient_id}/record` cria o prontuário ausente. A listagem de evoluções aceita qualquer dentista da clínica e inclui rascunhos de outros autores. A tela separa histórico e formulário. A API da Agenda restringe às próprias consultas, enquanto a lista cadastral de pacientes cobre toda a clínica.

Rever `backend/app/records/{router,service,repository}.py` e `frontend/src/{App.tsx,api.ts}`. A mudança do GET depende de migração coordenada da chamada atual `getOrOpen`; não declarar a interface integrada corrigida apenas porque o novo endpoint passou isoladamente.
