# Guia de integração do prontuário — Otávio

Conferido em **26/11/2026**, branch `fix/prontuario-correcoes-qa`.
Base documental 67068ac; novas leituras de vínculo implementadas localmente
em 26/11/2026. Os pareceres históricos continuam vinculados às versões originais.
Este guia descreve a API de lumina_odonto/app/main.py, app/crud.py e
app/clinical_patients*.py.
O serviço de `backend/` tem contratos diferentes; não misturar suas rotas.

## Onde começar

- [Pacientes clínicos e vínculos](docs/frontend/clinical-patients-and-links.md).
- [Autenticação, pesquisa e erros](docs/frontend/authentication-and-search.md).
- [Prontuário e evoluções: requisições e retornos](docs/frontend/records-and-evolutions.md).
- [README geral da API](README.md).
- [Relatórios e manifesto do pacote aprovado](../docs/relatorios/prontuario-correcoes-qa-2026-11-26/README.md).

Os exemplos são ilustrativos, com dados fictícios. Obter IDs reais do ambiente
isolado utilizado; paciente, prontuário, usuário e dentista têm IDs diferentes.
Enviar JSON com `Content-Type: application/json` nas escritas.
Todas as rotas abaixo já incluem `/api/v1`.
`/docs` e `/openapi.json` ficam fora desse prefixo.

A base HTTP deve apontar para a **imagem desta API** no ambiente de integração.
Uma API saudável numa porta antiga não comprova que esta candidata está executando.
Não configurar o frontend com segredo JWT ou acesso direto ao PostgreSQL.

## Sequência para a interface do dentista

1. Login: receber `access_token`.
2. Consultar `/api/v1/auth/me` com esse token para identificar o perfil.
3. Desbloquear o módulo com a senha clínica: receber `clinical_token`.
4. Carregar GET /api/v1/clinical/patients com token clínico e selecionar um item.
   Usar GET /api/v1/clinical/patients/{patient_id} para identificação mínima.
5. Consultar prontuário e suas evoluções com o token clínico.
6. Criar rascunho, editar enviando `version` e finalizar com `version` atual.
7. Pesquisar o histórico do paciente selecionado; seguir `next_offset`.

O prontuário nasce vazio no cadastro do paciente; não existe uma ação clínica
POST de abertura nesta API. O GET consulta o registro e não deve ser tratado
como uma chamada de criação. Evolução manual não exige consulta vinculada.
Concluir uma consulta não é pré-condição das rotas de evolução deste pacote.

## Rotas para Otávio

| Método e rota | Token | Envio/consulta | Retorno principal |
|---|---|---|---|
| POST `/api/v1/auth/login` | Nenhum | `email`, `password` | 200: `access_token`, `token_type` |
| GET `/api/v1/auth/me` | Acesso | Sem corpo | 200: usuário, clínica e perfil |
| POST `/api/v1/auth/clinical-unlock` | Acesso | `password` clínica | 200: `clinical_token`, `token_type` |
| GET /api/v1/clinical/patients | Clínico | limit, after_id, q | 200: items e next_after_id |
| GET /api/v1/clinical/patients/{patient_id} | Clínico | ID do paciente | 200: identificação mínima |
| GET `/api/v1/patients/{patient_id}/record` | Clínico | ID do paciente | 200: `id`, `patient_id` |
| GET `/api/v1/patients/{patient_id}/record/summary` | Clínico | ID do paciente | 200: registro completo de `medical_records` |
| PATCH `/api/v1/patients/{patient_id}/record` | Clínico | `general_notes` | 200: registro atualizado |
| GET `/api/v1/patients/{patient_id}/evolutions` | Clínico | ID do paciente | 200: array de evoluções visíveis |
| GET `/api/v1/evolutions/{evolution_id}` | Clínico | ID da evolução | 200: evolução e `patient_id` |
| POST `/api/v1/evolutions` | Clínico | `patient_id`, `description`; opcionais no guia | 201: evolução criada |
| PATCH `/api/v1/evolutions/{evolution_id}` | Clínico | `version` e campos alterados | 200: evolução e nova versão |
| POST `/api/v1/evolutions/{evolution_id}/finalize` | Clínico | `version` | 200: finalizada e nova versão |
| GET `/api/v1/clinical/search` | Clínico | `patient_id`, `q`, `engine_name`, `offset` | 200: resultados e `next_offset` |

Não usar a antiga rota `/patients/evolutions/{id}/draft` nem finalizar com
corpo vazio. `care_occurred_at` pertence ao contrato anterior da Agenda e não
é campo de criação/finalização de evolução nesta API.

## Rotas administrativas de apoio — sem liberar acesso ao dentista

| Método e rota | Quem usa | Observação atual |
|---|---|---|
| GET `/api/v1/dentists` | Usuário autenticado, token de acesso | `limit` 1–100, padrão 50; `offset` >= 0. Inclui `user_id`, nome e `is_active`, sem filtro só de ativos. |
| GET `/api/v1/patients` | Admin/recepção, token de acesso | Somente pacientes ativos; retorna `medical_record_id`. `limit` e `offset`. |
| POST `/api/v1/patients` | Admin/recepção, token de acesso | Cria paciente e prontuário na mesma transação; retorna `patient_id` e `medical_record_id`. |
| GET `/api/v1/access-links` | Só admin, token de acesso | Filtros `dentist_id`, `patient_id`, `limit`, `offset`; inclui vínculos ativos/revogados, nomes e flags atuais dos envolvidos. |
| POST `/api/v1/admin/access` | Só admin, token de acesso | `patient_id`, `dentist_id`, `action`: `GRANTED`, `REVOKED` ou `REACTIVATED`. |
| GET `/api/v1/access-events` | Só admin, token de acesso | Filtro `link_id`, `limit`, `offset`. |
| POST `/api/v1/admin/users/{user_id}/reset-login-password` | Só admin, token de acesso | `new_password` com pelo menos 12 caracteres; invalida sessões anteriores. |
| POST `/api/v1/auth/reset-clinical-password` | Próprio dentista, token de acesso | `new_password` distinta da senha de entrada; invalida liberações clínicas anteriores. |

`user_id` de `/auth/me` não é `dentist_id`. A listagem de dentistas permite
localizar o cadastro cujo `user_id` coincide com o usuário; não presumir IDs iguais.
Listagens comuns retornam arrays, não objetos com `items` e `total`.

## Lacunas a resolver antes de concluir as telas

| Necessidade da interface | Situação comprovada no código | Encaminhamento |
|---|---|---|
| “Meus pacientes/prontuários” do dentista | Implementado GET /clinical/patients com token clínico, paginação e busca restritos ao próprio profissional. | Usar o novo contrato, sem credencial administrativa. |
| Cabeçalho do painel clínico | Implementado GET /clinical/patients/{patient_id} com identificação mínima autorizada. | Obter dados cadastrais mínimos por essa rota. |
| Nome/flags de alvos inativos na gestão do vínculo | GET /access-links acrescenta identificação e flags, mantendo array e acesso exclusivo do admin. | Exibir para gestão sem tratar inativos como elegíveis para concessão. |
| Admin recuperar senha clínica de outro dentista | Há reset administrativo da senha de entrada e reset clínico pelo próprio dentista. Não há reset clínico administrativo nesta candidata. | Backend/Paulo fechar contrato desse fluxo antes de implementar o botão do protótipo. |
| Impressão individual e identificação histórica do autor | GET da evolução traz `dentist_id`; não há rota de impressão/PDF nem nome/CRO histórico nesse DTO. | Alinhar dados e política de impressão/retificação. Não anunciar impressão integrada ou histórico profissional como comprovados. |

As três leituras indicadas como implementadas têm contrato no novo guia.
As lacunas de senha e impressão continuam abertas, e a interface precisa
validar os novos fluxos na versão integrada.

## Evidências e roteiro de integração

A evidência histórica do QA encerrou N05 na candidata consolidada em21cefa6,
com 26 testes aprovados e 25
objetivos HTTP aprovados em PostgreSQL 16.16 e OpenCL real em CPU.
As provas anteriores dos outros defeitos estão nos relatórios, com suas versões.
Não houve aceite da interface, implantação diária ou upgrade do banco.

Usar dados fictícios e ambiente isolado. Conferir token, paciente e vínculo;
consultar registro vazio; criar/editar rascunho; disputar a mesma versão em
duas abas (200/409); finalizar; pesquisar por paciente e percorrer páginas;
revogar pelo admin e verificar a recusa e a remoção do conteúdo clínico da tela.
Os comportamentos da API já testados precisam ser exercitados na interface
integrada, com branch/commit e evidências identificados.

Esta revisão documenta novas leituras locais. Não houve migração nem implantação;
o parecer histórico não constitui reteste independente dessas novas rotas.
