import { toApiError } from "@/api/api";
import { loginFormSchema, type LoginFormData } from "@/services/Login/types";

export type LoginField = keyof LoginFormData;
export type LoginFieldErrors = Partial<Record<LoginField, string>>;

export const INITIAL_LOGIN_VALUES: LoginFormData = { username: "", password: "" };

type ValidationResult =
  | { success: true; data: LoginFormData }
  | { success: false; fieldErrors: LoginFieldErrors };

export function validateLoginForm(values: LoginFormData): ValidationResult {
  const result = loginFormSchema.safeParse(values);
  if (result.success) return { success: true, data: result.data };

  const fieldErrors: LoginFieldErrors = {};
  for (const issue of result.error.issues) {
    const field = issue.path[0] as LoginField;
    fieldErrors[field] ??= issue.message;
  }
  return { success: false, fieldErrors };
}

export type LoginErrorState = {
  formError: string | null;
  fieldErrors: LoginFieldErrors;
};

// Traduz a falha da API para o que a tela exibe. As mensagens vêm prontas da API
// (401 "Email ou senha inválidos." vale também para usuário inativo; 429; etc.).
export function mapLoginError(error: unknown): LoginErrorState {
  const apiError = toApiError(error);

  if (apiError.status === 422) {
    const { username, password } = apiError.fieldErrors;
    const fieldErrors: LoginFieldErrors = { username, password };
    const hasFieldError = Boolean(username || password);
    return {
      formError: hasFieldError ? null : apiError.message,
      fieldErrors,
    };
  }

  return { formError: apiError.message, fieldErrors: {} };
}
