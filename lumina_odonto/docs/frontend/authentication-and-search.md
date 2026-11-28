# Autenticação, pesquisa e erros — contrato atual

[Voltar ao guia de Otávio](../../FRONTEND.md).
[Sessão compartilhada com Caio, logout e bloqueio clínico](shared-session.md).
Fonte: `app/main.py`, `app/crud.py` e `app/config.py`; conferir a imagem que
estiver efetivamente executando, não apenas o nome da porta HTTP.
Exemplos ilustrativos com dados fictícios, não capturas de execução.

## Login e identificação

POST `/api/v1/auth/login`, JSON (não formulário OAuth):

```json
{"email": "dentista.demo@example.com", "password": "DemoLumina2026!"}
```

Resposta 200:

```json
{"access_token": "<token-de-acesso>", "token_type": "bearer", "expires_in": 1800}
```

GET `/api/v1/auth/me` com `Authorization: Bearer <access_token>` retorna
`id`, `clinic_id`, `full_name`, `email`, `role`, `is_active`. Não retorna
`dentist_id`. O token de entrada é emitido por 30 minutos no código atual; `expires_in` informa esse prazo em segundos.
Os valores de minutos expostos em configuração não são lidos nessa chamada:
não prometer prazo configurável sem revisar a implementação.

As credenciais deste exemplo são as contas de demonstração de
`sql/seed_demo.sql`. Só existem em ambientes preparados com esse seed.
Não executar seed sobre banco existente para tentar fazer o login funcionar.

## Desbloquear o prontuário

POST `/api/v1/auth/clinical-unlock` com o token de acesso, JSON:

```json
{"password": "ClinicaDemo2026!"}
```

Resposta 200:

```json
{"clinical_token": "<token-clinico>", "token_type": "bearer", "expires_in": 900}
```

Usar `Authorization: Bearer <clinical_token>` nas rotas clínicas. Não enviar
as duas senhas em cada requisição nem trocar a chave esperada de resposta
por `access_token`. O token clínico é emitido por 15 minutos no código atual; `expires_in` vale 900 segundos.

É necessário perfil DENTIST e cadastro profissional. O token clínico não
substitui o de acesso em `/auth/me` ou nas rotas administrativas; o inverso
também é recusado. Em expiração clínica, oferecer novo desbloqueio usando
uma sessão de entrada ainda válida. Sessão inválida exige novo login.

As duas senhas são credenciais do profissional, não do paciente. Não são
dois fatores independentes. Redefinições/inativação podem invalidar tokens
antes do horário de expiração. Evitar logs de tokens, senha, conteúdo de
rascunho e URL completa de busca em ferramentas do frontend.

## Selecionar paciente após desbloquear

GET /api/v1/clinical/patients usa o mesmo clinical_token, derivando o dentista
da sessão. Para identificar o paciente selecionado, GET
/api/v1/clinical/patients/{patient_id}. Vínculo manual sem consulta também
aparece. Ver [DTOs, paginação e administração](clinical-patients-and-links.md).
O admin continua usando access_token em /access-links e /admin/access.

## Pesquisa no histórico do paciente

GET `/api/v1/clinical/search?patient_id=7&q=limpeza&engine_name=auto&offset=0`
com o token clínico.

| Parâmetro | Contrato atual |
|---|---|
| `patient_id` | Obrigatório, inteiro positivo; paciente selecionado e autorizado. |
| `q` | Obrigatório; 1–128 caracteres após trim e conteúdo não vazio após normalização. |
| `engine_name` | `auto` (padrão), `cpu` ou `opencl`. |
| `offset` | Inteiro >= 0, padrão 0; deslocamento de candidatos, não de resultados. |

Não existe parâmetro de tamanho de página nesta rota. Os candidatos são
até 1.000 evoluções visíveis por página, ordenados por `e.id`. A busca
considera **description**, não os campos notes ou procedure_performed.
A comparação é literal, sem distinguir caixa/acentos, sem regex/fuzzy search.
Codificar `q` com URLSearchParams, sem concatenar texto cru na URL.

Resposta 200, exemplo:

```json
{
  "engine": "opencl",
  "total": 1,
  "results": [
    {
      "id": 10,
      "description": "Limpeza fictícia registrada.",
      "status": "FINALIZED",
      "dentist_id": 4,
      "patient_id": 7
    }
  ],
  "candidate_limit": 1000,
  "offset": 0,
  "next_offset": null
}
```

`results` não é o DTO completo da evolução: para exibir o detalhe ou editar,
fazer GET `/api/v1/evolutions/{id}`. A busca não devolve `version`, notes ou
horários nessa resposta. Ela mantém rascunhos de terceiros fora da consulta.

### Paginação e motores

`total` conta as correspondências **desta página**, não do histórico todo.
Enquanto `next_offset` não for `null`, usar esse valor na próxima chamada,
com o mesmo paciente/termo/motor. Uma página com `results: []` pode ainda
ter `next_offset`; não declarar “nenhum resultado no histórico” antes de
percorrer as páginas desejadas. `limit` não é parâmetro aceito desta busca.

`auto` tenta OpenCL e usa CPU em falha prevista do runtime. `cpu` força a
comparação sequencial. `opencl` exige runtime e devolve 503 se indisponível.
O campo `engine` informa o motor usado. Não anunciar OpenCL quando vier cpu.
Isso é diferente da configuração do OpenCL da Agenda, em outra branch.

O orçamento padrão é 2.000.000 bytes dos textos normalizados da página.
Excesso retorna 413; não há controle de `limit` para reduzi-la nesta API.
Registrar o caso e alinhar tratamento com Backend; não descartar registros
ou ignorar a falha para parecer que a busca foi completa.

A autorização é revalidada após o processamento. 403 durante a busca exige
remover o conteúdo clínico da tela e rever o contexto de acesso; uma busca
anterior aprovada não garante que o vínculo continua válido.

## Erros para a interface

HTTPException usa `detail` textual, exemplo:

```json
{"detail": "Acesso clínico não autorizado"}
```

Erro de validação de entrada usa `detail` como array sanitizado, exemplo:

```json
{
  "detail": [
    {
      "loc": ["body", "version"],
      "msg": "Campo ausente ou inválido",
      "type": "validation_error"
    }
  ]
}
```

O código também pode devolver 422 com `detail` textual em validações de
negócio. Não assumir que todo 422 tem array ou que toda falha possui `code`
como no backend anterior. O OpenAPI pode mostrar o schema padrão de erro,
mas o handler real é sanitizado; os exemplos acima seguem sua implementação.

| Status | Tratamento esperado |
|---|---|
| 401 | Rever o tipo/validade do token; desbloquear novamente ou fazer login conforme a sessão. |
| 403 | Recusa de perfil/vínculo/autoria/estado; não manter conteúdo clínico negado na tela. |
| 404 | Contexto/recurso não localizado; não criar outro prontuário por reação automática. |
| 409 | Ler o conflito; em versão antiga, preservar texto e comparar com o registro autorizado atual. |
| 413 | Página de busca excede orçamento; não interpretar como ausência de resultados. |
| 422 | Exibir validação útil sem reproduzir corpo clínico ou senha. |
| 503 | Runtime OpenCL obrigatório indisponível ou configuração inválida de autenticação, conforme a operação. |
| 500/rede | Exibir erro genérico; não renderizar traceback ou repetir escrita cegamente. |

Nem todo erro500 é JSON. Tratar Content-Type e falha de parse com mensagem
genérica, sem mostrar corpo bruto. Não persistir respostas clínicas de erro
em telemetria. Sem promessa de rate limiting validado: seus critérios seguem
pendentes nos relatórios desta candidata.
