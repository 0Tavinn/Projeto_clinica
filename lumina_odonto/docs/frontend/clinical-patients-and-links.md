# Pacientes clínicos e vínculos — novas leituras

Fonte ativa lumina_odonto/. Implementação local sobre
67068ac969cb7b34396b5d94e4ee09a7001ef8b4, em26/11/2026.
Exemplos fictícios; conferir a revisão entregue e a imagem executada.

## Lista do próprio dentista

GET /api/v1/clinical/patients com Authorization: Bearer <clinical_token>.

| Parâmetro | Regra |
|---|---|
| limit | Inteiro1–100, padrão50. |
| after_id | Inteiro>=0, padrão0; usar o cursor recebido. |
| q | Opcional,1–128 caracteres e conteúdo após trim; pesquisa literal por parte do nome ou número do prontuário. |

A pesquisa usa ILIKE: não distingue caixa, mas não promete ignorar acentos.
% e _ são literais, não curingas. O dentista é derivado da sessão. Não há
parâmetro para selecionar outro dentista. O token de acesso comum não basta.

Resposta200, exemplo completo:

```json
{
  "items": [
    {
      "patient_id": 7,
      "full_name": "Paciente Fictício",
      "medical_record_number": "PRONT-007",
      "medical_record_id": 3,
      "access_link_id": 11
    }
  ],
  "limit": 50,
  "next_after_id": null
}
```

São pacientes ativos, da clínica e vinculados de forma ACTIVE ao próprio
dentista. Vínculo administrativo sem consulta/evolução participa normalmente.
Prontuário vazio aparece. Se um registro legado não tiver prontuário,
medical_record_id pode ser null; a leitura não cria nem regulariza registros.

Não retorna CPF, contatos, general_notes, descrição, rascunhos ou credenciais.
Não há total global. Ordem crescente de patient_id. next_after_id é o último
ID candidato examinado quando existe outro candidato. Repassar esse cursor
com os mesmos filtros. Uma revogação concorrente pode deixar a página
menor ou vazia com cursor; continuar enquanto next_after_id não for null.
As páginas são leituras independentes, sem snapshot estável entre chamadas.

## Cabeçalho clínico

GET /api/v1/clinical/patients/{patient_id}, também com token clínico.
Retorna200 com um objeto no mesmo formato de cada item. O ID deve ser positivo.
Paciente sem vínculo ativo, revogado ou fora do contexto autorizado não
libera identificação. A verificação é do servidor, independentemente da lista
mantida na tela.

## Erros e concorrência das novas rotas

401: token ausente, inválido, expirado, tipo/perfil clínico incorreto ou
sessão inválida. 403: falta de cadastro profissional, vínculo ou elegibilidade.
404 pode ocorrer no detalhe quando o paciente está inativo/não encontrado
na verificação do contexto permitido. 422: parâmetros inválidos. O formato
de erro continua o detail já documentado em authentication-and-search.md.
As mensagens não ecoam a busca ou identificação enviada.

Leituras bloqueiam pacientes e depois seus vínculos, em ordem crescente,
com FOR SHARE, seguindo patient -> link de change_link. Após esperas,
reconferem sessão, clínica, profissional e o vínculo com um novo snapshot
READ COMMITTED. Revogação confirmada durante a espera exclui o item da lista
ou recusa o detalhe. Os bloqueios duram somente a requisição, encerrados ao
fechar a sessão da dependency; não persistem enquanto o usuário navega na tela.
Não se promete recolher bytes já enviados nem estabilidade entre páginas.

## Administração dos vínculos existentes

GET /api/v1/access-links continua **array**, exclusivo do admin com
access_token. Mantém campos existentes e filtros patient_id, dentist_id,
limit1–100 e offset>=0. Agora acrescenta a cada vínculo:

| Campo adicional | Uso |
|---|---|
| patient_full_name | Nome para gestão, inclusive paciente inativo. |
| patient_medical_record_number | Número do prontuário cadastral. |
| patient_is_active | Situação atual do paciente. |
| dentist_full_name | Nome atual do profissional. |
| dentist_is_active | Situação atual do usuário profissional. |
| dentist_user_id | Relaciona ao usuário de autenticação. |
| dentist_cro_number, dentist_cro_state | Cadastro profissional atual. |

Exemplo ilustrativo de um item (campos completos do vínculo e acréscimos):

```json
{
  "id": 11,
  "clinic_id": 1,
  "patient_id": 7,
  "dentist_id": 4,
  "status": "REVOKED",
  "version": 2,
  "created_at": "2026-11-26T10:00:00+00:00",
  "updated_at": "2026-11-26T11:00:00+00:00",
  "patient_full_name": "Paciente Fictício",
  "patient_medical_record_number": "PRONT-007",
  "patient_is_active": false,
  "dentist_full_name": "Profissional Fictício",
  "dentist_is_active": true,
  "dentist_user_id": 9,
  "dentist_cro_number": "12345",
  "dentist_cro_state": "PE"
}
```

Os nomes/CRO são atuais, sem fotografia histórica. Flags permitem exibir
o vínculo para gerir/revogar; não autorizam concessão ou reativação de inativos.
GET /dentists continua incluindo inativos com is_active. A seleção para nova
concessão deve considerar os ativos, e o servidor continua validando a escrita.

A mutação permanece POST /api/v1/admin/access com patient_id,dentist_id,
action GRANTED/REVOKED/REACTIVATED. Sem nova rota duplicada.
Recepção não administra vínculos. Revogar inativos no escopo permitido
preserva prontuário/evoluções e mantém evento/auditoria existentes.
Cancelamento ou alteração de consulta antiga não reabre vínculo revogado;
novo agendamento mantém a regra de concessão/reativação já implementada.

## Integração

Após desbloqueio clínico, carregar a nova lista e escolher um item. Usar o
detalhe mínimo para cabeçalho e as rotas atuais para prontuário/evoluções.
Em401/403 remover da tela os dados cujo acesso foi perdido. Não usar token
administrativo como atalho para o painel clínico.
