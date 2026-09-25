export type UserRole = "ADMINISTRATOR" | "RECEPTIONIST" | "DENTIST";

// Resposta de GET /api/v1/auth/me
export interface AuthUser {
  id: number;
  clinic_id: number;
  full_name: string;
  email: string;
  cpf: string;
  phone: string | null;
  role: UserRole;
  is_active: boolean;
}
