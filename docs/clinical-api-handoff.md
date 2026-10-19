# Contrato clínico provisório para integração da Sprint 6

Este documento descreve o comportamento da branch de correção do backend.
As regras de vínculo assistencial, acesso ao histórico, atendimento sem
agendamento, abertura do prontuário, retificação e preservação do CRO ainda
precisam de aprovação da equipe e do professor. Até lá, a API limita o acesso
ao que pode comprovar pelos agendamentos existentes.

## Rotas e autorização

Todas as rotas abaixo usam o prefixo `/api/v1` e exigem access token Bearer.
Administrador e recepcionista recebem `403` para conteúdo clínico.

| Método e rota | Comportamento provisório |
| --- | --- |
| `GET /patients/{patient_id}/record` | Consulta um prontuário existente. Exige paciente ativo da clínica e uma consulta `SCHEDULED`, `CONFIRMED` ou `COMPLETED` atribuída ao dentista autenticado. Retorna `404` se não houver prontuário. Não cria registro e não devolve `general_notes`. |
| `GET /patients/{patient_id}/evolutions` | Exige o mesmo vínculo e lista somente evoluções do próprio dentista vinculadas a consultas `COMPLETED` coerentes com paciente e clínica. Não expõe o histórico de outros autores. |
| `POST /patients/evolutions` | Cria rascunho em prontuário existente. Exige `patient_id`, `description` e `appointment_id` de consulta `COMPLETED` atribuída ao dentista, mesmo que o campo seja anulável no banco. Aceita `procedure_performed` e `notes` opcionais. |
| `PATCH /patients/evolutions/{evolution_id}/draft` | Edita somente rascunho próprio ligado a consulta concluída coerente. |
| `POST /patients/evolutions/{evolution_id}/finalize` | Finaliza somente rascunho próprio com descrição não vazia; grava situação e horário na mesma transação. |

As respostas de evolução mantêm `dentist.id`, `dentist.full_name`,
`dentist.cro_number` e `dentist.cro_state`. Esses dados são lidos do cadastro
profissional atual: o armazenamento de um retrato do CRO no momento da
finalização ainda depende de decisão e modelagem.

Os erros seguem o envelope `{"error":{"code":"...","message":"...","details":...}}`.
Sem vínculo assistencial a API retorna `403`; recurso fora da clínica ou não
visível retorna `404`; agendamento já associado a uma evolução retorna
`409`; payload ou transição inválida retorna `422`.

## Repasse para frontend e banco

O frontend atual chama `GET /record` como “abrir ou consultar”. A abertura
automática por `GET` foi retirada: uma leitura não altera o banco e a política
de criação ainda precisa ser aprovada. Caio deve tratar o `404` como
prontuário ainda não aberto e aguardar o contrato de abertura. A listagem é
provisoriamente limitada ao próprio autor; a interface não deve chamar isso
de histórico clínico completo.

O PostgreSQL local consultado em 19/10/2026 já possui as tabelas clínicas,
suas restrições e gatilhos, mas não possui `alembic_version`. Nenhuma migração
foi executada. O DBA deve definir o baseline e a integridade antes de aplicar
qualquer alteração em banco existente. Os testes automatizados desta branch
usam SQLite e não comprovam as restrições específicas do PostgreSQL.
