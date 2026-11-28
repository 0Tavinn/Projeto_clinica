# Rotas para integrar as interfaces — Otávio e Caio

Conferência documental: **26/11/2026**, branch `fix/prontuario-correcoes-qa`,
contratos da API publicada em `5c6ac86204d8d76cae0240088a93f2f511e721b0`.
Este índice organiza as rotas. A manutenção de sessão de 28/11/2026 acrescenta
logout, bloqueio clínico e validade explícita, conforme o [guia compartilhado](shared-session.md).

## Qual API utilizar

- Código: `lumina_odonto/app/`. O serviço legado de `backend/` tem outros contratos.
- Swagger local desta preparação: http://localhost:18100/docs.
- Origem HTTP: `http://localhost:18100`. As rotas abaixo **já incluem** `/api/v1`.
- Se o cliente usa base `http://localhost:18100/api/v1`, acrescente somente o caminho restante.
- Preparação, portas, CORS e contas fictícias: [INTEGRATION.md](../../INTEGRATION.md).
- Guia geral já publicado: [FRONTEND.md](../../FRONTEND.md).

Localhost é o computador que executa a API. O colega precisa preparar seu ambiente;
a interface da Agenda em 18088 não foi convertida em interface desta API.

## Autenticação compartilhada

| Método e rota | Envio | Retorno/uso |
| --- | --- | --- |
| POST `/api/v1/auth/login` | JSON com `email` e `password` | 200: `access_token`, `token_type`, `expires_in`. Não é formulário OAuth. |
| POST `/api/v1/auth/logout` | Bearer de acesso; sem corpo | 204: encerra todas as sessões desta conta na API nova. |
| POST `/api/v1/auth/clinical-lock` | Bearer de acesso do dentista; sem corpo | 204: bloqueia liberações clínicas, preservando o login. |
| GET `/api/v1/auth/me` | Bearer `access_token` | 200: usuário, clínica e perfil; `id` é do usuário, não do dentista. |
| POST `/api/v1/auth/clinical-unlock` | Bearer de acesso e JSON `password` clínica | 200: `clinical_token`, `token_type`, `expires_in`; exclusivo do dentista. |

Enviar `Authorization: Bearer <token>` e, nas escritas, `Content-Type: application/json`.
O administrador usa seu **access_token** no painel de vínculos. O dentista usa
**clinical_token** no prontuário. Não utilizar token administrativo para acessar
conteúdo clínico. Contrato de tokens e erros: [authentication-and-search.md](authentication-and-search.md).

## Otávio — prontuários do dentista

Todas as rotas desta tabela usam **clinical_token** do dentista autenticado.

| Método e rota | Finalidade | Envio e retorno principal |
| --- | --- | --- |
| GET `/api/v1/clinical/patients` | Meus pacientes autorizados | `limit`, `after_id`, `q` opcional; objeto com `items`, `limit`, `next_after_id`. |
| GET `/api/v1/clinical/patients/{patient_id}` | Cabeçalho mínimo do paciente | 200: identificação mínima e IDs de prontuário/vínculo. |
| GET `/api/v1/patients/{patient_id}/record` | Identificar prontuário | 200: `id`, `patient_id`; não cria o registro. |
| GET `/api/v1/patients/{patient_id}/record/summary` | Ler resumo geral | 200: registro com `general_notes` e horários. |
| PATCH `/api/v1/patients/{patient_id}/record` | Atualizar observação geral | JSON `general_notes`, inclusive null; retorna registro atualizado. |
| GET `/api/v1/patients/{patient_id}/evolutions` | Histórico visível | Array; finalizadas permitidas e rascunhos do próprio autor; vazio é `[]`. |
| GET `/api/v1/evolutions/{evolution_id}` | Detalhe de evolução | 200: evolução, versão e `patient_id`. |
| POST `/api/v1/evolutions` | Novo rascunho | `patient_id`, `description`; opcionais `appointment_id`, `procedure_performed`, `notes`; 201 com evolução. |
| PATCH `/api/v1/evolutions/{evolution_id}` | Editar próprio rascunho | `version` obrigatória e pelo menos um campo editável; 200 com nova versão. |
| POST `/api/v1/evolutions/{evolution_id}/finalize` | Finalizar próprio rascunho | JSON `version`; 200 com FINALIZED, nova versão e data de finalização. |
| GET `/api/v1/clinical/search` | Buscar descrições no histórico | `patient_id`, `q`, `engine_name`, `offset`; resultados e `next_offset`. |

Fluxo: login → desbloqueio clínico → lista de pacientes → cabeçalho/prontuário →
evoluções. Prontuário vazio é válido. O cadastro de paciente cria o prontuário;
não existe POST clínico de abertura nesta API. Nova evolução manual não exige
concluir consulta e não substitui o histórico existente.

`version` é inteiro JSON estrito e positivo na edição/finalização. Em 409,
preserve o texto e ofereça recarga/comparação; não repita a gravação automaticamente.
Finalizada não tem edição comum. Em 401/403, retire da tela os dados cujo acesso
foi perdido. A lista clínica é do próprio profissional, derivado da sessão.

- [DTOs, filtros e cursor de pacientes](clinical-patients-and-links.md).
- [Corpos JSON, retornos e regras das evoluções](records-and-evolutions.md).
- [Busca, motores, paginação e erros](authentication-and-search.md).

## Caio — vínculos no administrador

O painel usa **access_token de ADMINISTRATOR**, sem desbloqueio clínico.

| Método e rota | Finalidade | Envio e retorno principal |
| --- | --- | --- |
| GET `/api/v1/dentists` | Listar dentistas da clínica | `limit`, `offset`; array, incluindo inativos, com nome e `is_active`. |
| GET `/api/v1/dentists/{dentist_id}` | Identificar dentista selecionado | Objeto cadastral; `id` é dentist_id e `user_id` identifica a conta. |
| GET `/api/v1/patients` | Selecionar paciente para vincular | `limit`, `offset`; array de pacientes ativos da clínica. |
| GET `/api/v1/patients/{patient_id}` | Conferir cadastro do paciente ativo | Objeto cadastral; não é conteúdo de evolução. |
| GET `/api/v1/access-links` | Ler vínculos do profissional | `dentist_id`, `patient_id`, `limit`, `offset`; array enriquecido com nomes, flags, status e versão. |
| POST `/api/v1/admin/access` | Vincular, desvincular ou reativar | `patient_id`, `dentist_id`, `action`; 200 com `link_id` e `action`. |
| GET `/api/v1/access-events` | Consultar histórico do vínculo | `link_id`, `limit`, `offset`; array de eventos. |

Fluxo: login admin → dentistas → selecionar `dentist_id` → vínculos →
selecionar paciente → confirmação → POST → recarregar vínculos após sucesso.
Não criar consulta para executar uma vinculação manual.

O contrato completo do painel, com os três corpos JSON, resposta, estados,
erros, pesquisa/paginação e limites, está em [administrative-links.md](administrative-links.md).

## Limites e critérios de integração

- Não confundir `user_id`, `dentist_id`, `patient_id`, ID do prontuário e ID do vínculo.
- Revogação retira acesso, mas não apaga prontuário, evolução ou eventos.
- `q` da lista clínica não existe automaticamente nas listas administrativas.
- A API não fornece total global/contagem pronta por dentista no painel administrativo.
- Não inventar rotas DELETE de vínculo, endpoints de PDF ou motivo de revogação persistido.
- Recuperação clínica administrativa, impressão e identificação histórica do autor
  permanecem lacunas documentadas; estes guias não as declaram implementadas.
- A entrega da Agenda/OpenCL está em outra branch. Seus contratos de login,
  conclusão, cancelamento, filtros e respostas exigem harmonização futura.
- Os exemplos são ilustrativos; os resultados da manutenção de sessão são registrados
  em relatório próprio, sem substituir o aceite integrado da interface.
