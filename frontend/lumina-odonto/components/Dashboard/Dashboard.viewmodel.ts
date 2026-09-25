"use client";

import { getFirstName } from "@/lib/user";
import { ROLE_LABELS } from "@/lib/auth/permissions";
import { useSession } from "@/providers/session/session.context";
import { getShortcuts } from "./Dashboard.model";

export function useDashboardViewModel() {
  const { user } = useSession();

  // O ProtectedRoute só renderiza o dashboard com sessão autenticada.
  if (!user) return null;

  return {
    firstName: getFirstName(user.full_name),
    roleLabel: ROLE_LABELS[user.role],
    shortcuts: getShortcuts(user.role),
  };
}

export type DashboardViewModel = NonNullable<ReturnType<typeof useDashboardViewModel>>;
