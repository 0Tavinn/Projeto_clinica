import { canAccessRoute, getHomeRoute, ROUTES } from "@/lib/auth/routes";
import type { SessionStatus } from "@/providers/session/session.context";
import type { AuthUser } from "@/types/auth";

export type GuardDecision =
  | { kind: "loading" }
  | { kind: "redirect"; to: string }
  | { kind: "denied"; homeRoute: string }
  | { kind: "allowed" };

// Área logada: sem sessão → login; perfil sem acesso à rota → acesso negado.
export function resolveProtectedRoute(
  status: SessionStatus,
  user: AuthUser | null,
  pathname: string,
): GuardDecision {
  if (status === "loading") return { kind: "loading" };
  if (!user) return { kind: "redirect", to: ROUTES.login };
  if (!canAccessRoute(user.role, pathname)) {
    return { kind: "denied", homeRoute: getHomeRoute(user.role) };
  }
  return { kind: "allowed" };
}

// Telas de visitante (login): com sessão ativa → home do perfil.
export function resolveGuestRoute(
  status: SessionStatus,
  user: AuthUser | null,
): GuardDecision {
  if (status === "loading") return { kind: "loading" };
  if (user) return { kind: "redirect", to: getHomeRoute(user.role) };
  return { kind: "allowed" };
}
