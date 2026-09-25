# Integração entre Front-end e API — Lumina Odonto

## Objetivo

Este documento descreve o contrato **atualmente implementado** pela API do
Lumina Odonto para orientar a integração do front-end na Sprint 4. Ele não
antecipa endpoints ou permissões que ainda não existem no código.

## Endereços locais

Com a API executada localmente a partir da pasta `backend/`:

| Recurso | Endereço |
|---|---|
| API | `http://localhost:8000` |
| Swagger / OpenAPI | `http://localhost:8000/docs` |
| Health check | `GET http://localhost:8000/health` |
| Prefixo da API | `/api/v1` |

Exemplo de URL base no front-end:

```text
http://localhost:8000/api/v1
```

Não inclua a URL base diretamente em diversos componentes. Centralize-a na
configuração do front-end para que possa variar entre ambientes.

## Autenticação JWT

A API usa access token e refresh token JWT. Depois de um login válido, envie o
access token em todas as rotas protegidas:

```http
Authorization: Bearer <access_token>
```

O token de acesso é usado para as requisições protegidas. Quando ele expirar, o
front-end pode enviar o refresh token para `POST /api/v1/auth/refresh` e
substituir os dois tokens retornados. Não há endpoint de logout no momento; o
logout no front-end deve descartar a sessão armazenada e redirecionar para a
tela de login.

### Login usa formulário OAuth2

`POST /api/v1/auth/login` **não** recebe JSON. Envie
`application/x-www-form-urlencoded` com os campos abaixo:

| Campo | Tipo | Regra |
|---|---|---|
| `username` | texto | E-mail do usuário |
| `password` | texto | Senha do usuário |

Exemplo com `fetch`:

```js
const body = new URLSearchParams({
  username: email,
  password,
});

const response = await fetch(`${API_URL}/auth/login`, {
  method: "POST",
  headers: { "Content-Type": "application/x-www-form-urlencoded" },
  body,
});
```

Resposta de sucesso (`200`):

```json
{
  "access_token": "<jwt-de-acesso>",
  "refresh_token": "<jwt-de-renovacao>",
  "token_type": "bearer"
}
```

Após o login, consulte `GET /api/v1/auth/me` com o access token. Essa rota
retorna o perfil que deve orientar a navegação e os controles da interface.

## Perfis de acesso vigentes

| Operação | Administrador | Recepcionista | Dentista |
|---|:---:|:---:|:---:|
| Login, refresh e consulta do próprio usuário | Sim | Sim | Sim |
| Cadastrar usuário da equipe | Sim | Não | Não |
| Listar ou consultar pacientes | Sim | Sim | Sim |
| Cadastrar paciente | Sim | Sim | Não |
| Editar paciente | Sim | Sim | Não |
| Inativar paciente | Sim | Sim | Não |

As permissões acima refletem a API atual. O front-end deve esconder ações não
autorizadas por perfil, mas a API continua sendo a autoridade final e pode
retornar `403`.

## Endpoints existentes

### Saúde da API

| Método | Rota | Finalidade | Perfil | Campos principais | Respostas esperadas |
|---|---|---|---|---|---|
| `GET` | `/health` | Verifica se o processo da API está ativo | Público | Nenhum | `200` |

O health check é de disponibilidade do processo; ele não confirma a conexão
com PostgreSQL.

Exemplo de resposta (`200`):

```json
{
  "status": "ok",
  "app": "Dental Clinic API",
  "environment": "development"
}
```

### Autenticação

| Método | Rota | Finalidade | Perfil | Campos principais | Respostas esperadas |
|---|---|---|---|---|---|
| `POST` | `/api/v1/auth/login` | Autentica e emite tokens | Público | Formulário: `username`, `password` | `200`, `401`, `422`, `429`, `500` |
| `POST` | `/api/v1/auth/refresh` | Emite novo par de tokens | Refresh token válido | JSON: `refresh_token` | `200`, `401`, `422`, `500` |
| `GET` | `/api/v1/auth/me` | Retorna o usuário autenticado | Usuário ativo | Header `Authorization` | `200`, `401`, `500` |

Exemplo de renovação:

```json
{
  "refresh_token": "<jwt-de-renovacao>"
}
```

Resposta de `GET /api/v1/auth/me` (`200`):

```json
{
  "id": 1,
  "clinic_id": 1,
  "full_name": "Nome do usuário",
  "email": "usuario@exemplo.com",
  "cpf": "00000000000",
  "phone": "81999999999",
  "role": "RECEPTIONIST",
  "is_active": true
}
```

### Usuários da equipe

| Método | Rota | Finalidade | Perfil | Campos principais | Respostas esperadas |
|---|---|---|---|---|---|
| `POST` | `/api/v1/users` | Cadastra usuário na clínica do administrador | Administrador | `full_name`, `email`, `password`, `cpf`, `phone`, `role` | `201`, `401`, `403`, `409`, `422`, `500` |

Campos obrigatórios para cadastro de usuário:

| Campo | Regra atual |
|---|---|
| `full_name` | Texto de 1 a 150 caracteres |
| `email` | E-mail válido |
| `password` | Texto de 8 a 128 caracteres |
| `cpf` | Exatamente 11 dígitos, sem pontuação |
| `role` | `ADMINISTRATOR`, `RECEPTIONIST` ou `DENTIST` |
| `phone` | Opcional, até 20 caracteres |

Exemplo de requisição:

```json
{
  "full_name": "Nome da profissional",
  "email": "profissional@exemplo.com",
  "password": "<senha-definida-pelo-usuario>",
  "cpf": "00000000000",
  "phone": "81999999999",
  "role": "RECEPTIONIST"
}
```

A resposta não inclui a senha nem o hash da senha. O usuário sempre é criado
na clínica do administrador autenticado; o front-end não envia `clinic_id`.

Exemplo de resposta de criação (`201`):

```json
{
  "id": 2,
  "clinic_id": 1,
  "full_name": "Nome da profissional",
  "email": "profissional@exemplo.com",
  "cpf": "00000000000",
  "phone": "81999999999",
  "role": "RECEPTIONIST",
  "is_active": true
}
```

Não existe `GET /api/v1/users` na versão atual. Portanto, a tela de equipe
não consegue obter uma lista de usuários pela API e não deve supor que essa
rota esteja disponível.

### Pacientes

| Método | Rota | Finalidade | Perfil | Campos principais | Respostas esperadas |
|---|---|---|---|---|---|
| `POST` | `/api/v1/patients` | Cadastra paciente | Administrador ou recepcionista | Dados do paciente | `201`, `401`, `403`, `409`, `422`, `500` |
| `GET` | `/api/v1/patients` | Lista pacientes ativos da clínica | Qualquer perfil ativo | Header `Authorization` | `200`, `401`, `403`, `500` |
| `GET` | `/api/v1/patients/{patient_id}` | Consulta paciente ativo | Qualquer perfil ativo | `patient_id` | `200`, `401`, `403`, `404`, `422`, `500` |
| `PATCH` | `/api/v1/patients/{patient_id}` | Atualiza paciente ativo | Administrador ou recepcionista | `patient_id` e campos alterados | `200`, `400`, `401`, `403`, `404`, `409`, `422`, `500` |
| `DELETE` | `/api/v1/patients/{patient_id}` | Inativa paciente sem apagá-lo | Administrador ou recepcionista | `patient_id` | `204`, `401`, `403`, `404`, `422`, `500` |

Campos obrigatórios no cadastro de paciente:

| Campo | Regra atual |
|---|---|
| `full_name` | Texto de 1 a 150 caracteres |
| `cpf` | Exatamente 11 dígitos, sem pontuação |
| `medical_record_number` | Texto de 1 a 30 caracteres; a API armazena em maiúsculas |
| `birth_date` | Data no formato `YYYY-MM-DD` |
| `phone` | Opcional, até 20 caracteres |
| `email` | Opcional; se informado, deve ser e-mail válido |
| `address` | Opcional |

Exemplo de cadastro:

```json
{
  "full_name": "Nome do paciente",
  "cpf": "00000000000",
  "medical_record_number": "PRT-0001",
  "birth_date": "1995-04-12",
  "phone": "81999999999",
  "email": "paciente@exemplo.com",
  "address": "Endereço de exemplo"
}
```

Exemplo de resposta de criação (`201`):

```json
{
  "id": 1,
  "clinic_id": 1,
  "full_name": "Nome do paciente",
  "cpf": "00000000000",
  "medical_record_number": "PRT-0001",
  "birth_date": "1995-04-12",
  "phone": "81999999999",
  "email": "paciente@exemplo.com",
  "address": "Endereço de exemplo",
  "is_active": true,
  "created_at": "2026-09-22T12:00:00Z",
  "updated_at": "2026-09-22T12:00:00Z"
}
```

No `PATCH`, envie somente os campos que devem mudar. É necessário enviar ao
menos um campo útil. Atualmente, campos com valor `null` são ignorados pela
API; portanto, o front-end não consegue limpar um campo opcional enviando
`null`.

O `DELETE` é uma inativação lógica e responde sem corpo (`204`). Em seguida,
atualize a listagem local ou faça nova chamada para `GET /patients`.

## Regras de persistência e isolamento de clínica

Os dados de usuários e pacientes são persistidos no PostgreSQL. O vínculo com
`clinic_id` não é definido pelo front-end: a API o obtém do usuário autenticado
e limita consultas e alterações àquela clínica.

- usuários: `email` e `cpf` são únicos em todo o banco; a senha é persistida
  somente como hash;
- pacientes: a combinação `clinic_id` + `cpf` é única, assim como
  `clinic_id` + `medical_record_number`;
- listagem e consulta retornam somente pacientes ativos da clínica do usuário;
- `DELETE /patients/{patient_id}` não apaga uma linha: define `is_active` como
  `false`. Pacientes inativos deixam de aparecer nas rotas atuais de listagem,
  consulta e atualização;
- na criação e atualização, o número de prontuário é convertido para
  maiúsculas; e-mail é convertido para minúsculas e campos textuais enviados
  são removidos de espaços nas extremidades.

## Respostas e tratamento de erros

| Código | Significado para o front-end |
|---|---|
| `200` | Operação concluída; leia o corpo da resposta |
| `201` | Registro criado; atualize a lista com o recurso retornado |
| `204` | Operação concluída sem corpo; remova ou atualize o item da interface |
| `401` | Credenciais, access token ou refresh token inválido/expirado; encerre ou renove a sessão conforme o fluxo |
| `403` | Usuário autenticado sem permissão; mantenha a sessão e mostre acesso negado |
| `404` | Recurso inexistente, inativo ou fora da clínica do usuário |
| `409` | Conflito, normalmente e-mail, CPF ou prontuário já cadastrado |
| `422` | Payload inválido; destaque os campos apontados em `error.details` quando disponível |
| `500` | Falha interna; mostre uma mensagem genérica e não exponha detalhes técnicos |

Os erros tratados pela API usam este envelope:

```json
{
  "error": {
    "code": "CODIGO_DO_ERRO",
    "message": "Mensagem adequada para exibição",
    "details": null
  }
}
```

Para erros de validação (`422`), `details` pode conter a lista de campos e
motivos retornados pelo FastAPI. Para conflitos e alguns erros HTTP, o campo
`code` atual pode ser genérico. Por isso, o front-end deve decidir o fluxo
principal pelo status HTTP e exibir `error.message` quando ela existir.

Exemplos representativos:

`401` — token ausente, inválido ou expirado:

```json
{
  "error": {
    "code": "UNAUTHORIZEDERROR",
    "message": "Token de autenticação não informado.",
    "details": null
  }
}
```

`403` — perfil sem a permissão exigida:

```json
{
  "error": {
    "code": "FORBIDDENERROR",
    "message": "Usuário não tem permissão para acessar este recurso.",
    "details": null
  }
}
```

`409` — e-mail, CPF ou número de prontuário duplicado:

```json
{
  "error": {
    "code": "HTTP_ERROR",
    "message": "Já existe um paciente com este CPF ou número de prontuário nesta clínica.",
    "details": null
  }
}
```

`422` — corpo ou parâmetro da rota inválido:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Dados de entrada inválidos.",
    "details": [
      {
        "loc": ["body", "cpf"],
        "msg": "String should have at least 11 characters",
        "type": "string_too_short"
      }
    ]
  }
}
```

Recomendações de interface:

- não exiba tokens, senhas ou detalhes internos em mensagens;
- trate falhas de rede separadamente de respostas HTTP da API;
- mantenha ações restritas ocultas por perfil, mas sempre trate `403`;
- depois de `401`, tente renovar a sessão somente quando houver refresh token;
- se a renovação falhar, descarte a sessão e redirecione para o login.

## CORS e URL base

As origens permitidas são configuradas pela variável `CORS_ORIGINS` no ambiente
da API. O endereço exato do front-end, incluindo protocolo e porta, deve estar
nessa lista. Em desenvolvimento, o exemplo de ambiente contempla endereços
locais usuais para aplicações web.

Se o navegador bloquear uma requisição por CORS, confirme primeiro:

1. a URL base usada pelo front-end;
2. a origem completa em que o front-end está rodando;
3. se essa origem está configurada em `CORS_ORIGINS` no ambiente da API;
4. se o token foi enviado no cabeçalho `Authorization` correto.

Não altere CORS pelo front-end e não use `*` quando a aplicação precisar enviar
credenciais.

## Funcionalidades previstas para a Sprint 4

As funcionalidades a seguir estão no planejamento da Sprint, mas **não fazem
parte do contrato atual**:

- `GET /api/v1/users` para a tela de gestão da equipe;
- autorização para dentistas cadastrarem e editarem pacientes;
- testes automatizados para as novas permissões e para a listagem de equipe.

Até que essas mudanças sejam implementadas e testadas, o front-end não deve
apresentá-las como disponíveis.
