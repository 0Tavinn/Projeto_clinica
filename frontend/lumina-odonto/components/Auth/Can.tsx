"use client";

import { hasPermission, type Permission } from "@/lib/auth/permissions";
import { useSession } from "@/providers/session/session.context";

// Mostra o conteúdo só para perfis com a permissão. Ex.: <Can permission="deactivatePatient">.
export default function Can({
  permission,
  children,
  fallback = null,
}: {
  permission: Permission;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}) {
  const { user } = useSession();
  return user && hasPermission(user.role, permission) ? children : fallback;
}
