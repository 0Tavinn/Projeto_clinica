import type { UserRole } from "@/types/auth";
import { hasPermission, type Permission } from "./permissions";

export const ROUTES = {
  login: "/",
  dashboard: "/dashboard",
  patients: "/pacientes",
  team: "/equipe",
} as const;

// Hoje todos os perfis começam no dashboard; mudar aqui quando houver telas por perfil.
const HOME_ROUTE_BY_ROLE: Record<UserRole, string> = {
  ADMINISTRATOR: ROUTES.dashboard,
  RECEPTIONIST: ROUTES.dashboard,
  DENTIST: ROUTES.dashboard,
};

// Rotas protegidas que exigem permissão além de estar logado.
const ROUTE_PERMISSIONS: Record<string, Permission> = {
  [ROUTES.patients]: "viewPatients",
  [ROUTES.team]: "manageTeam",
};

export function getHomeRoute(role: UserRole): string {
  return HOME_ROUTE_BY_ROLE[role];
}

export function matchesRoute(pathname: string, route: string): boolean {
  return pathname === route || pathname.startsWith(`${route}/`);
}

export function canAccessRoute(role: UserRole, pathname: string): boolean {
  const entry = Object.entries(ROUTE_PERMISSIONS).find(([route]) =>
    matchesRoute(pathname, route),
  );
  return !entry || hasPermission(role, entry[1]);
}
