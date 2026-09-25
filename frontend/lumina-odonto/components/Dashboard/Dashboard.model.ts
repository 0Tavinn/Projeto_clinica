import { getNavItems, type NavItem } from "@/lib/auth/navigation";
import { ROUTES } from "@/lib/auth/routes";
import type { UserRole } from "@/types/auth";

// Atalhos = itens de menu do perfil, sem o próprio dashboard.
export function getShortcuts(role: UserRole): NavItem[] {
  return getNavItems(role).filter((item) => item.href !== ROUTES.dashboard);
}
