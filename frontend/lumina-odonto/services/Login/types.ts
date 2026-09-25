import * as z from "zod";

export type { AuthUser, UserRole } from "@/types/auth";

export interface LoginCredentialsProps {
  username: string;
  password: string;
}

export const loginFormSchema = z.object({
  username: z.string().trim().pipe(z.email("E-mail inválido")),
  password: z.string().min(1, "Senha é obrigatória"),
});
export type LoginFormData = z.infer<typeof loginFormSchema>;
