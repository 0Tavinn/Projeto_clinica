import axios, {
  AxiosError,
  type AxiosInstance,
  type InternalAxiosRequestConfig,
} from "axios";

// Contrato: Projeto_clinica/docs/api-integration.md. A doc está defasada em relação à main
// (GET /users e permissões de paciente do dentista); a matriz vigente está em lib/auth/permissions.ts.

// Precisa do prefixo NEXT_PUBLIC_ para ser exposta ao navegador (inlined no build).
export const API_URL = process.env.NEXT_PUBLIC_API_URL;

const LOGIN_PATH = "/";
const ACCESS_TOKEN_KEY = "lumina.access_token";
const REFRESH_TOKEN_KEY = "lumina.refresh_token";

// Rotas de autenticação não entram no fluxo de renovação automática.
const AUTH_ROUTES = ["/auth/login", "/auth/refresh"];

export type TokenPair = {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
};

/* ------------------------------------------------------------------ */
/* Sessão                                                              */
/* ------------------------------------------------------------------ */

const isBrowser = typeof window !== "undefined";

export const tokenStorage = {
  getAccessToken(): string | null {
    return isBrowser ? localStorage.getItem(ACCESS_TOKEN_KEY) : null;
  },
  getRefreshToken(): string | null {
    return isBrowser ? localStorage.getItem(REFRESH_TOKEN_KEY) : null;
  },
  setTokens({ access_token, refresh_token }: TokenPair) {
    if (!isBrowser) return;
    localStorage.setItem(ACCESS_TOKEN_KEY, access_token);
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token);
  },
  clear() {
    if (!isBrowser) return;
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  },
};

// Não existe endpoint de logout: encerrar a sessão é descartar os tokens.
export function endSession() {
  tokenStorage.clear();
  if (isBrowser && window.location.pathname !== LOGIN_PATH) {
    window.location.replace(LOGIN_PATH);
  }
}

/* ------------------------------------------------------------------ */
/* Erros                                                               */
/* ------------------------------------------------------------------ */

export type ValidationIssue = {
  loc: (string | number)[];
  msg: string;
  type: string;
};

type ErrorEnvelope = {
  error?: {
    code?: string;
    message?: string;
    details?: ValidationIssue[] | null;
  };
  detail?: ValidationIssue[] | string;
};

const DEFAULT_MESSAGES: Record<number, string> = {
  401: "Sessão expirada ou credenciais inválidas.",
  403: "Você não tem permissão para realizar esta ação.",
  404: "Registro não encontrado.",
  409: "CPF, e-mail ou prontuário já cadastrado.",
  422: "Campos inválidos ou incompletos.",
  429: "Muitas tentativas. Aguarde alguns instantes e tente novamente.",
  500: "Erro interno. Tente novamente mais tarde.",
};

const NETWORK_ERROR_MESSAGE =
  "Não foi possível conectar à API. Verifique sua conexão e tente novamente.";

export class ApiError extends Error {
  readonly status: number | null;
  readonly code: string | null;
  readonly details: ValidationIssue[];

  constructor(
    message: string,
    status: number | null,
    code: string | null = null,
    details: ValidationIssue[] = [],
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }

  // Falha de rede/CORS/timeout: a API não respondeu.
  get isNetworkError() {
    return this.status === null;
  }

  // Mapeia erros 422 para { campo: mensagem }, útil para destacar inputs.
  get fieldErrors(): Record<string, string> {
    return Object.fromEntries(
      this.details.map((issue) => [String(issue.loc.at(-1)), issue.msg]),
    );
  }
}

// O fluxo deve ser decidido pelo status HTTP; `code` pode vir genérico.
export function toApiError(error: unknown): ApiError {
  if (error instanceof ApiError) return error;

  if (!axios.isAxiosError<ErrorEnvelope>(error)) {
    return new ApiError(DEFAULT_MESSAGES[500], 500);
  }

  if (!error.response) {
    return new ApiError(NETWORK_ERROR_MESSAGE, null, "NETWORK_ERROR");
  }

  const { status, data } = error.response;
  const envelope = data?.error;
  const rawDetail = Array.isArray(data?.detail) ? data.detail : [];
  const message =
    status >= 500
      ? DEFAULT_MESSAGES[500]
      : (envelope?.message ??
        DEFAULT_MESSAGES[status] ??
        DEFAULT_MESSAGES[500]);

  return new ApiError(
    message,
    status,
    envelope?.code ?? null,
    envelope?.details ?? rawDetail,
  );
}

/* ------------------------------------------------------------------ */
/* Cliente HTTP                                                        */
/* ------------------------------------------------------------------ */

export const api: AxiosInstance = axios.create({
  baseURL: API_URL,
  timeout: 15_000,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = tokenStorage.getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Uma única renovação em andamento, compartilhada pelas requisições que falharem com 401.
let refreshPromise: Promise<string> | null = null;

async function refreshAccessToken(): Promise<string> {
  const refresh_token = tokenStorage.getRefreshToken();
  if (!refresh_token) throw new Error("Sem refresh token");

  // Cliente sem interceptors para não entrar em loop.
  const { data } = await axios.post<TokenPair>(`${API_URL}/auth/refresh`, {
    refresh_token,
  });
  tokenStorage.setTokens(data);
  return data.access_token;
}

type RetriableConfig = InternalAxiosRequestConfig & { _retry?: boolean };

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as RetriableConfig | undefined;
    const isAuthRoute = AUTH_ROUTES.some((route) =>
      original?.url?.includes(route),
    );

    if (
      error.response?.status !== 401 ||
      !original ||
      original._retry ||
      isAuthRoute
    ) {
      return Promise.reject(toApiError(error));
    }

    // 401: renovar somente se houver refresh token; se falhar, encerrar a sessão.
    if (!tokenStorage.getRefreshToken()) {
      endSession();
      return Promise.reject(toApiError(error));
    }

    original._retry = true;
    try {
      refreshPromise ??= refreshAccessToken().finally(() => {
        refreshPromise = null;
      });
      const newToken = await refreshPromise;
      original.headers.Authorization = `Bearer ${newToken}`;
      return api(original);
    } catch {
      endSession();
      return Promise.reject(toApiError(error));
    }
  },
);
