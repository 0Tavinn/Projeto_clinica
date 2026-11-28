# Caio — contrato do painel administrativo de vínculos

[Índice de rotas dos dois painéis](README.md).
Fonte: `app/main.py`, `app/crud.py`, `app/clinical_patients_repository.py` e
OpenAPI da API `lumina_odonto/`, contrato publicado em `5c6ac86`.
Conferência documental em 26/11/2026. Exemplos abaixo são fictícios e ilustrativos.

## Sessão e seleção

O painel é exclusivo de ADMINISTRATOR. Faça login JSON em
`POST /api/v1/auth/login`, confira `GET /api/v1/auth/me` e use
`Authorization: Bearer <access_token>` nas chamadas deste documento.
O administrador não informa a senha clínica do dentista nem usa clinical_token.
Login, expiração e encerramento seguem o [contrato de sessão compartilhada](shared-session.md),
que Caio e Otávio devem utilizar na mesma aplicação.

1. `GET /api/v1/dentists?limit=50&offset=0`: retorna array de dentistas da clínica,
   incluindo inativos. Campos úteis: `id`, `user_id`, `full_name`, `is_active`,
   `cro_number`, `cro_state`, `specialty`. O ID a enviar é `id`, não `user_id`.
2. Selecionado o dentista: `GET /api/v1/access-links?dentist_id=4&limit=50&offset=0`.
   Retorna array de vínculos ACTIVE e REVOKED, inclusive os necessários à gestão
   de alvos inativos. A clínica vem da sessão; não há seletor de outra clínica.
3. Para o diálogo Vincular paciente: `GET /api/v1/patients?limit=50&offset=0`.
   Retorna array de pacientes ativos da clínica, com `id`, `full_name`,
   `medical_record_number`, `medical_record_id` e outros campos cadastrais.
   Não renderizar campos pessoais que a seleção não precisa mostrar.
4. `GET /api/v1/dentists/{dentist_id}` e `GET /api/v1/patients/{patient_id}`
   permitem consultar o cadastro selecionado. O detalhe comum de paciente
   exige perfil admin/recepção e paciente ativo; não serve para buscar inativos.

A gestão de vínculos não exige ler prontuário ou evolução clínica.
Recepcionista não administra vínculos, embora tenha acesso a cadastro de pacientes.

## O que a lista de vínculos retorna

GET `/api/v1/access-links` aceita somente os filtros documentados:
`dentist_id`, `patient_id`, `limit` (1–100, padrão 50) e `offset` (>=0).
O corpo de sucesso é **array**, não `{items,total}`.

Cada item contém `id`, `clinic_id`, `patient_id`, `dentist_id`, `status`,
`version`, `created_at`, `updated_at` e os dados adicionais:

| Campo | Uso no painel |
| --- | --- |
| patient_full_name | Nome do paciente; também disponível nos vínculos com inativos. |
| patient_medical_record_number | Identificação cadastral do prontuário. |
| patient_is_active | Situação atual do paciente. |
| dentist_full_name | Nome atual do profissional. |
| dentist_is_active | Situação atual da conta do profissional. |
| dentist_user_id | ID da conta, diferente do ID profissional. |
| dentist_cro_number / dentist_cro_state | Cadastro profissional atual, não snapshot histórico. |

O exemplo completo de item está no [contrato compartilhado](clinical-patients-and-links.md#administração-dos-vínculos-existentes).
Para mostrar apenas pacientes atualmente vinculados, filtre `status === 'ACTIVE'`
nos dados carregados. Os REVOKED continuam existindo no servidor/histórico.
Não excluir a informação do banco para fazer o paciente desaparecer da lista ativa.

## Três operações, uma rota

Todas usam POST `/api/v1/admin/access`, token de acesso administrativo e JSON.
IDs são dos cadastros retornados pelas listas, sempre da clínica autenticada.
Os exemplos 7 e 4 não são IDs garantidos do seed local.

### Vincular pela primeira vez

```json
{"patient_id":7,"dentist_id":4,"action":"GRANTED"}
```

Usar quando o par ainda não possui vínculo. Se o vínculo já existir, retorna 409;
não substituir por reativação automática sem confirmar o estado e a intenção.

### Desvincular

```json
{"patient_id":7,"dentist_id":4,"action":"REVOKED"}
```

Usar em vínculo ACTIVE. Se não existir ou já estiver revogado, retorna 409.
O servidor permite revogação de alvos inativos no contexto compatível da clínica;
não esconda o botão somente porque a flag is_active está falsa.
A ausência de senha clínica não deve impedir a apresentação da revogação de
um vínculo existente. A lista não revela hashes nem informa uma senha clínica.

### Reativar um vínculo existente

```json
{"patient_id":7,"dentist_id":4,"action":"REACTIVATED"}
```

Usar em vínculo REVOKED. Se não existir ou estiver ativo, retorna 409.
Nova concessão e reativação exigem participantes ativos e compatíveis;
flags na interface não substituem a validação no servidor.

### Sucesso e histórico

Resposta HTTP **200**, no exemplo de desvinculação:

```json
{"link_id":11,"action":"REVOKED"}
```

O retorno não contém a lista atualizada, total, nova versão ou nomes.
Após sucesso, consulte novamente `/access-links` para o dentista selecionado.
Não use DELETE de paciente/dentista nem DELETE de vínculo: não há essa rota.
O servidor grava estado, versão, evento e auditoria na mesma transação.
Não enviar `version` de evolução para essa operação administrativa.

GET `/api/v1/access-events?link_id=11&limit=50&offset=0` retorna um array
com os eventos do vínculo, ordenados por ID decrescente. Inclui ação, fonte,
ator e versão do vínculo, entre os campos de histórico. Não oferece edição
ou exclusão de eventos. Revogar não apaga evoluções ou autoria.

## Comportamento esperado da interface

- Ao clicar Desvincular, confirmar paciente e dentista pelo nome em um diálogo.
- Cancelar o diálogo não envia mutação e preserva seleção, lista e pesquisa.
- Durante a requisição, evitar duplo envio; não remover nem incrementar contagem antecipadamente.
- Somente após sucesso, atualizar lista/contagem e mostrar confirmação visível,
  inclusive quando a pesquisa atual continua sem resultados.
- Em falha, preservar contexto e oferecer nova tentativa sem repetir a escrita cegamente.
- Ao vincular um REVOKED, apresentar reativação de forma clara, sem criar outro par.
- Preservar outros vínculos do mesmo paciente; não existe dentista exclusivo por paciente.
- Exibir alvos inativos para gerir/revogar o vínculo, sem oferecê-los como nova concessão elegível.

O corpo não possui `reason`/motivo. Se a tela solicitar esse texto, não afirmar
que ele será persistido: exige contrato adicional de backend. Não inventar
esse campo ou outros parâmetros como parte do contrato atual.

## Pesquisa, paginação e contagens

`GET /dentists`, `GET /patients` e `GET /access-links` não implementam `q` nem
filtro textual de nome neste contrato. O `q` de `/clinical/patients` pertence
à lista do dentista, com token clínico, e não é uma busca administrativa.

As listas administrativas usam `limit`/`offset` e não retornam total global.
Para uma pesquisa local completa ou contagem total por profissional, percorra
todas as páginas necessárias e então filtre os dados. Se filtrar apenas a
página carregada, informe essa limitação; não anunciar resultado global.
Uma página com menos itens que limit indica o fim na leitura atual, sem
prometer snapshot estável entre páginas ou após operações concorrentes.
Se o volume exigir busca no servidor, alinhar esse incremento com Backend.

O paciente de um vínculo revogado pode ser encontrado pela lista administrativa
de vínculos, enquanto o seletor de nova concessão usa apenas pacientes ativos.
A listagem enriquecida evita tentar abrir o prontuário para obter nomes.

## Erros e limites

| HTTP | Tratamento |
| --- | --- |
| 401 | Token ausente, inválido, expirado ou sessão inválida; solicitar login adequado. |
| 403 | Perfil/clinica sem permissão; não oferecer o painel a outros perfis. |
| 404 | Paciente não localizado no contexto permitido; conferir cadastro/atividade. |
| 409 | Estado mudou ou ação incompatível; recarregar vínculo e pedir decisão do administrador. |
| 422 | Corpo/ação inválida ou dentista incompatível; orientar correção sem inventar sucesso. |
| 500 ou rede | Mensagem genérica; não mostrar traceback ou repetir mutação automaticamente. |

O envelope é `detail`, textual ou array sanitizado, conforme o erro;
ver [authentication-and-search.md](authentication-and-search.md#erros-para-a-interface).
Não supor envelope `code/message` do backend anterior nem prioridade fixa
quando houver mais de uma condição inválida.

Um novo agendamento pela API corrigida pode conceder/reativar o vínculo.
Cancelar, concluir ou alterar uma consulta antiga não desfaz a revogação.
O painel administrativo consegue operar sem criar consulta. Essa regra não
significa que as duas APIs de Agenda/prontuário já foram integradas.

Esta revisão documenta comportamento existente. Não altera API/banco nem
substitui os testes de integração da interface de Caio com o backend.
