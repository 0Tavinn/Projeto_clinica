import { toApiError } from "@/api/api";
import { loginFormSchema, type LoginFormData } from "@/services/Login/types";

export type LoginField = keyof LoginFormData;
export type LoginFieldErrors = Partial<Record<LoginField, string>>;

export const INITIAL_LOGIN_VALUES: LoginFormData = { username: "", password: "" };

const INVALID_CREDENTIALS_MESSAGE = "E-mail ou senha inválidos.";

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

// Traduz a falha da API para o que a tela exibe. A API responde 401 também para usuário inativo.
export function mapLoginError(error: unknown): LoginErrorState {
  const apiError = toApiError(error);

  if (apiError.status === 401) {
    return { formError: INVALID_CREDENTIALS_MESSAGE, fieldErrors: {} };
  }

  if (apiError.status === 422) {
    const { username, password } = apiError.fieldErrors;
    const fieldErrors: LoginFieldErrors = { username, password };
    const hasFieldError = Boolean(username || password);
    return {
      formError: hasFieldError ? null : apiError.message,
      fieldErrors,
    };
  }

  // 429, rede e demais erros já chegam com mensagem pronta do ApiError.
  return { formError: apiError.message, fieldErrors: {} };
}
