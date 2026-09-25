---
assunto: Plano de implementação — login por perfil (Sprint 4)
"Data:": 2026-09-24
status: etapas 1–7 concluídas em 2026-09-25 (não commitado); etapa 7 validada contra a API real rodando com SQLite
tags: [login, mvvm, sessao, rotas, permissoes]
---
# Plano: login por perfil (MVVM)

Premissa MVVM (confirmar com o Caio): Model = `services/` + `api/`; ViewModel = hook
`useXViewModel` por tela; View = `components/` só renderiza. Pasta `features/` existe
vazia — se o padrão for `features/<modulo>/{model,viewmodel,view}`, ajustar caminhos.

## Estado atual (2026-09-24)
- Pronto: `api/api.ts` (token, refresh, ApiError), `authService.login/getMe/logout`, tipos, `loginFormSchema`.
- UI do login pronta visualmente, mas `LoginCard` sem estado, `form action=""`, sem `"use client"`.
- Falta: sessão global, ViewModel do login, proteção de rotas/perfil. Dashboard fica pra depois (só placeholder).

## Decisão: proteção de rotas no CLIENTE
Tokens estão em `localStorage` → `proxy.ts` (Next 16, ex-middleware) roda no servidor e
só vê cookies. Usar layout guard client-side num route group. Migrar pra cookie = refazer
tokenStorage/refresh; fora do prazo. A API continua sendo a autoridade (401/403).

## Etapas
1. **Model / permissões**: mover `AuthUser`/`UserRole` pra local compartilhado. Funções puras
   por perfil: `canManageTeam` (ADMIN), `canCreatePatient`/`canEditPatient` (todos),
   `canDeactivatePatient` (ADMIN, RECEP). Mapa perfil→rota inicial (hoje todos `/dashboard`)
   e perfil→itens de menu. Usar a matriz REAL (ver backend-main-2026-09-23.md), não a da doc.
2. **Sessão global**: SessionProvider + `useSession` no `app/layout.tsx`.
   Estado `status` (loading|authenticated|unauthenticated) + `user`. Bootstrap: tem token →
   getMe (interceptor faz refresh) → senão endSession. Ações `setUser`, `logout`.
3. **useLoginViewModel**: campos, erros por campo, erro geral, `isSubmitting`. Valida com
   `loginFormSchema`. Submit: login → getMe → setUser → redirect por perfil.
   Erros: 401 "E-mail ou senha inválidos" (inclui inativo); 422 `fieldErrors`; 429;
   `isNetworkError`. Se login ok e getMe falhar → limpar tokens. Bloquear duplo submit.
4. **View LoginCard**: `"use client"`, inputs controlados (`name`, `type="email"`,
   `autoComplete`), `onSubmit`, erros via `Field`/`Alert`, `Spinner` no botão. Não mexer no visual.
5. **Rotas**: `/` login; grupo `(protected)` com layout guard → `/dashboard`, `/equipe`
   (só ADMIN), `/pacientes`. Guard: loading → spinner; unauthenticated → `/`; perfil sem
   acesso → acesso negado/dashboard. Login com sessão ativa → redireciona pra home do perfil.
6. **Placeholder do dashboard**: nome, perfil, botão Sair, itens de menu do perfil.
7. **Validação ponta a ponta**: contas de teste dos 3 perfis (Paulo); `http://localhost:3000`
   em `CORS_ORIGINS` (Luiz); `.env` = `http://localhost:8000/api/v1`. Testar por perfil:
   login, F5, sair. Negativos: 401, 429, API off, token vencido (refresh), refresh vencido,
   rota protegida sem sessão, não-admin em `/equipe`. Tirar prints pro relatório.

Extras: `app/layout.tsx` `lang="pt-BR"` e título "Lumina Odonto"; atualizar comentário de
`api/api.ts:7` (doc defasada).

## Ordem
1 → 2 → 3+4 (login funcionando) → 5 → 6 (por perfil) → 7. Prazo oficial 26/09 23:59;
ainda restam tela de equipe e CRUD de pacientes, então priorizar 1–5.
