import type { UserRole } from "@/types/auth";

// Matriz real do backend (main em 23/09, PR #3). docs/api-integration.md está defasada:
// dentista também cadastra e edita paciente, e GET /users já existe (só ADMIN).
const PERMISSIONS = {
  manageTeam: ["ADMINISTRATOR"],
  viewPatients: ["ADMINISTRATOR", "RECEPTIONIST", "DENTIST"],
  createPatient: ["ADMINISTRATOR", "RECEPTIONIST", "DENTIST"],
  editPatient: ["ADMINISTRATOR", "RECEPTIONIST", "DENTIST"],
  deactivatePatient: ["ADMINISTRATOR", "RECEPTIONIST"],
} as const satisfies Record<string, readonly UserRole[]>;

export type Permission = keyof typeof PERMISSIONS;

export const ROLE_LABELS: Record<UserRole, string> = {
  ADMINISTRATOR: "Administrador",
  RECEPTIONIST: "Recepcionista",
  DENTIST: "Dentista",
};

export function hasPermission(role: UserRole, permission: Permission): boolean {
  return (PERMISSIONS[permission] as readonly UserRole[]).includes(role);
}

export const canManageTeam = (role: UserRole) => hasPermission(role, "manageTeam");
export const canCreatePatient = (role: UserRole) =>
  hasPermission(role, "createPatient");
export const canEditPatient = (role: UserRole) =>
  hasPermission(role, "editPatient");
export const canDeactivatePatient = (role: UserRole) =>
  hasPermission(role, "deactivatePatient");
