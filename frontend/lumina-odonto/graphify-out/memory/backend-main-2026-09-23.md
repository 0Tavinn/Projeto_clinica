---
assunto: Mudanças do backend na main (23/09) que tornam docs/api-integration.md desatualizado
"Data:": 2026-09-24
fonte: git origin/main (commits 47c3cb1, 5a46cb1, c4169b6, 2a35651, merge 74eb022 / PR #3)
---
# Backend na main em 2026-09-23 — o que mudou além da documentação

Nenhum arquivo de `docs/` foi alterado. As mudanças são de código e **implementam
dois itens que `docs/api-integration.md` ainda lista como "previstos, fora do
contrato atual"**. A doc está atrasada em relação à API.

## 1. GET /api/v1/users (Tarcísio — 47c3cb1, 5a46cb1, direto na main)

- `backend/app/users/management_router.py`: `GET /api/v1/users`, `response_model=List[UserRead]`, 200.
- Permissão: `require_administrator` (só ADMINISTRATOR; demais → 403).
- `service.list_users_by_clinic`: retorna **todos** os usuários da clínica do admin
  (`User.clinic_id == current_user.clinic_id`), inclusive inativos; sem paginação, sem filtro, sem ordenação explícita.
- Formato de cada item = `UserRead` (id, clinic_id, full_name, email, cpf, phone, role, is_active).
- Testes em `backend/tests/test_permissions.py`.
- Obs.: o commit 5a46cb1 também versionou uma pasta `venv/` inteira no repo (lixo).

## 2. Dentista cadastra e edita paciente (Tarcísio c4169b6 + Paulo/eiSerjao 2a35651, PR #3)

- Nova permissão `require_patient_editor` = ADMINISTRATOR, RECEPTIONIST, DENTIST.
- `POST /api/v1/patients` e `PATCH /api/v1/patients/{id}` → `require_patient_editor`.
- `DELETE /api/v1/patients/{id}` (inativar) continua `require_patient_manager` = ADMIN e RECEP. Dentista → 403.
- PR #3 existiu porque c4169b6 usava `require_patient_editor` sem declará-lo (API não subia).
  Após o fix: 26 testes passando; validado no Swagger (dentista cria/edita, 403 ao inativar;
  recepcionista inativa → 204) e no PostgreSQL (is_active true → false, registro preservado).

## Matriz de permissões REAL (substitui a de docs/api-integration.md)

| Operação | Admin | Recep | Dentista |
|---|:-:|:-:|:-:|
| Login / refresh / me | Sim | Sim | Sim |
| Cadastrar usuário (POST /users) | Sim | Não | Não |
| Listar equipe (GET /users) | Sim | Não | Não |
| Listar/consultar pacientes | Sim | Sim | Sim |
| Cadastrar paciente | Sim | Sim | **Sim** |
| Editar paciente | Sim | Sim | **Sim** |
| Inativar paciente | Sim | Sim | Não |

## Impacto no front
- Tela de equipe pode listar via `GET /users` (mostrar status ativo/inativo, já que vem tudo).
- Dentista: mostrar botões de cadastrar/editar paciente; esconder "inativar".
- Esperar a doc (Cassiano) ser atualizada ou avisar o time que ela está defasada.
