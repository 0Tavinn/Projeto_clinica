---
assunto: 
"Data:": 2026-09-22
status: 
tags:
---
# GUIA DE INTEGRAÇÃO ENTRE FRONT-END E API

## 1. Configuração principal

URL local da API:

```
http://localhost:8000
```

Prefixo dos endpoints:

```
/api/v1
```

Exemplo de variável do front-end:

```
VITE_API_URL=http://localhost:8000/api/v1
```

Documentação interativa:

```
http://localhost:8000/docs
```

## 2. Autenticação

### Login

```
POST /api/v1/auth/login
```

O login não recebe JSON. Ele utiliza o formato:

```
application/x-www-form-urlencoded
```

Campos:

```
username = e-mail do usuário
password = senha do usuário
```

Resposta esperada:

```
{
  "access_token": "TOKEN_JWT",
  "refresh_token": "TOKEN_DE_RENOVACAO",
  "token_type": "bearer"
}
```

Depois do login, as requisições protegidas devem enviar:

```
Authorization: Bearer TOKEN_JWT
```

### Consultar usuário autenticado

```
GET /api/v1/auth/me
```

Esse endpoint permite descobrir:

- ID do usuário;
    
- nome;
    
- e-mail;
    
- perfil;
    
- clínica;
    
- situação do cadastro.
    

## 3. Cadastro da equipe

### Cadastrar usuário

```
POST /api/v1/users
```

Permissão:

```
Somente ADMINISTRATOR
```

Exemplo de JSON:

```
{
  "full_name": "Ana Souza",
  "email": "ana@lumina.com",
  "password": "Senha@123",
  "cpf": "12345678901",
  "phone": "81999990000",
  "role": "RECEPTIONIST"
}
```

Perfis aceitos:

```
ADMINISTRATOR
RECEPTIONIST
DENTIST
```

O front-end não deve enviar:

```
clinic_id
password_hash
is_active
created_at
updated_at
```

A API identifica a clínica pelo administrador autenticado e transforma a senha em hash.

## 4. Pacientes

### Listar pacientes

```
GET /api/v1/patients
```

### Cadastrar paciente

```
POST /api/v1/patients
```

Exemplo de JSON:

```
{
  "full_name": "Maria da Silva",
  "cpf": "12345678901",
  "medical_record_number": "PAC-0001",
  "birth_date": "1990-05-20",
  "phone": "81999990001",
  "email": "maria@email.com",
  "address": "Rua Exemplo, 123"
}
```

Observações:

- CPF deve ser enviado somente com números;
    
- data deve utilizar `AAAA-MM-DD`;
    
- número do prontuário é obrigatório no contrato atual;
    
- `clinic_id` é definido pela API;
    
- CPF e número do prontuário não podem estar repetidos na mesma clínica.
    

### Consultar paciente

```
GET /api/v1/patients/{patient_id}
```

### Atualizar paciente

```
PATCH /api/v1/patients/{patient_id}
```

O `PATCH` recebe somente os campos alterados:

```
{
  "phone": "81988880000",
  "address": "Novo endereço"
}
```

### Inativar paciente

```
DELETE /api/v1/patients/{patient_id}
```

Resposta esperada:

```
204 No Content
```

A exclusão é lógica. O registro permanece no banco com `is_active = false`.

## 5. Tratamento de erros

O front-end deve tratar:

```
401 — E-mail ou senha inválidos
403 — Usuário sem permissão
404 — Registro não encontrado
409 — CPF, e-mail ou prontuário já cadastrado
422 — Campos inválidos ou incompletos
500 — Erro interno
Falha de rede — API indisponível
```

Quando existir, usar a mensagem:

```
{
  "error": {
    "code": "CONFLICTERROR",
    "message": "Mensagem explicando o problema"
  }
}
```

Para erros de validação do FastAPI, o front também deve conseguir interpretar o campo:

```
{
  "detail": []
}
```

## 6. Regras de navegação

- Usuário sem token deve voltar para o Login;
    
- Administrador pode acessar a gestão da equipe;
    
- Recepcionista não pode acessar a gestão da equipe;
    
- Dentista não pode acessar a gestão da equipe;
    
- Menus sem permissão não devem ser exibidos;
    
- Erro `401` durante uma requisição deve encerrar a sessão;
    
- Após logout, remover os tokens e retornar ao Login.
    

## 7. Campos que não devem aparecer no front-end

Nunca exibir ou solicitar:

```
password_hash
SECRET_KEY
DATABASE_URL
clinic_id digitado manualmente
tokens completos em mensagens ou prints
```
