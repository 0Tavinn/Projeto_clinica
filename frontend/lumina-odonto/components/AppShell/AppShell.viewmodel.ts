"use client";

import { usePathname } from "next/navigation";
import { getNavItems } from "@/lib/auth/navigation";
import { useSession } from "@/providers/session/session.context";
import { getInitials } from "@/lib/user";
import { isNavItemActive } from "./AppShell.model";

export function useAppShellViewModel() {
  const { user, logout } = useSession();
  const pathname = usePathname();

  const navItems = user
    ? getNavItems(user.role).map((item) => ({
        ...item,
        active: isNavItemActive(pathname, item.href),
      }))
    : [];

  return {
    user,
    initials: user ? getInitials(user.full_name) : "",
    navItems,
    // Ao limpar a sessão, o ProtectedRoute redireciona para o login.
    onLogout: logout,
  };
}

export type AppShellViewModel = ReturnType<typeof useAppShellViewModel>;
