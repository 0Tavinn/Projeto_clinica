const API_URL = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1').replace(/\/$/, '')

const ACCESS_TOKEN_KEY = 'lumina.access_token'
const REFRESH_TOKEN_KEY = 'lumina.refresh_token'

export type UserRole = 'ADMINISTRATOR' | 'RECEPTIONIST' | 'DENTIST'

export type AuthUser = {
  id: number
  clinic_id: number
  full_name: string
  email: string
  cpf: string
  phone: string | null
  role: UserRole
  is_active: boolean
}

export type UserRead = AuthUser

export type UserCreatePayload = {
  full_name: string
  email: string
  password: string
  cpf: string
  phone: string | null
  role: UserRole
}

export type Patient = {
  id: number
  clinic_id: number
  full_name: string
  cpf: string
  medical_record_number: string
  birth_date: string
  phone: string | null
  email: string | null
  address: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export type PatientPayload = {
  full_name: string
  cpf: string
  medical_record_number: string
  birth_date: string
  phone: string | null
  email: string | null
  address: string | null
}

type TokenPair = {
  access_token: string
  refresh_token: string
  token_type: 'bearer'
}

type ValidationIssue = {
  loc?: Array<string | number>
  msg?: string
  type?: string
}

type ErrorEnvelope = {
  error?: {
    code?: string
    message?: string
    details?: ValidationIssue[] | null
  }
  detail?: string | ValidationIssue[]
}

const STATUS_MESSAGES: Record<number, string> = {
  401: 'Sessão expirada ou credenciais inválidas.',
  403: 'Você não tem permissão para realizar esta ação.',
  404: 'Registro não encontrado.',
  409: 'Já existe um registro com estes dados.',
  422: 'Revise os campos obrigatórios e tente novamente.',
  429: 'Muitas tentativas. Aguarde alguns instantes e tente novamente.',
  500: 'Erro interno. Tente novamente mais tarde.',
}

export class ApiError extends Error {
  readonly status: number | null
  readonly code: string | null
  readonly details: ValidationIssue[]

  constructor(
    message: string,
    status: number | null,
    code: string | null = null,
    details: ValidationIssue[] = [],
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.details = details
  }
}

export function getErrorMessage(error: unknown): string {
  return error instanceof Error
    ? error.message
    : 'Não foi possível concluir a operação.'
}

export const sessionStorageService = {
  getAccessToken: () => sessionStorage.getItem(ACCESS_TOKEN_KEY),
  getRefreshToken: () => sessionStorage.getItem(REFRESH_TOKEN_KEY),
  setTokens(tokens: TokenPair) {
    sessionStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token)
    sessionStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token)
  },
  clear() {
    sessionStorage.removeItem(ACCESS_TOKEN_KEY)
    sessionStorage.removeItem(REFRESH_TOKEN_KEY)
  },
}

async function toApiError(response: Response): Promise<ApiError> {
  const body = await response.json().catch(() => ({})) as ErrorEnvelope
  const details = body.error?.details ?? (Array.isArray(body.detail) ? body.detail : [])
  const detailMessage = typeof body.detail === 'string' ? body.detail : null
  const message = body.error?.message ?? detailMessage ?? STATUS_MESSAGES[response.status]
    ?? 'Não foi possível concluir a operação.'

  return new ApiError(message, response.status, body.error?.code ?? null, details)
}

async function fetchApi(path: string, options: RequestInit): Promise<Response> {
  try {
    return await fetch(`${API_URL}${path}`, options)
  } catch {
    throw new ApiError(
      'Não foi possível conectar à API. Verifique se o serviço está disponível.',
      null,
      'NETWORK_ERROR',
    )
  }
}

function requestHeaders(options: RequestInit): Headers {
  const headers = new Headers(options.headers)
  const token = sessionStorageService.getAccessToken()

  if (options.body && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  return headers
}

async function refreshSession(): Promise<void> {
  const refreshToken = sessionStorageService.getRefreshToken()
  if (!refreshToken) {
    sessionStorageService.clear()
    throw new ApiError('Sua sessão expirou. Entre novamente.', 401)
  }

  const response = await fetchApi('/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  })

  if (!response.ok) {
    sessionStorageService.clear()
    throw await toApiError(response)
  }

  sessionStorageService.setTokens(await response.json() as TokenPair)
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
  retryAfterRefresh = true,
): Promise<T> {
  let response = await fetchApi(path, { ...options, headers: requestHeaders(options) })

  if (response.status === 401 && retryAfterRefresh && !path.startsWith('/auth/')) {
    try {
      await refreshSession()
      response = await fetchApi(path, { ...options, headers: requestHeaders(options) })
    } catch (error) {
      sessionStorageService.clear()
      throw error
    }
  }

  if (!response.ok) {
    if (response.status === 401) sessionStorageService.clear()
    throw await toApiError(response)
  }

  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

async function login(email: string, password: string): Promise<TokenPair> {
  const body = new URLSearchParams({ username: email, password })
  const response = await fetchApi('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  })

  if (!response.ok) throw await toApiError(response)

  const tokens = await response.json() as TokenPair
  sessionStorageService.setTokens(tokens)
  return tokens
}

export const authApi = {
  async signIn(email: string, password: string): Promise<AuthUser> {
    await login(email, password)
    try {
      return await apiRequest<AuthUser>('/auth/me')
    } catch (error) {
      sessionStorageService.clear()
      throw error
    }
  },
  getMe: () => apiRequest<AuthUser>('/auth/me'),
  async restoreSession(): Promise<AuthUser | null> {
    if (!sessionStorageService.getAccessToken() && !sessionStorageService.getRefreshToken()) {
      return null
    }
    try {
      return await apiRequest<AuthUser>('/auth/me')
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) return null
      throw error
    }
  },
  logout() {
    sessionStorageService.clear()
  },
}

export const usersApi = {
  list: () => apiRequest<UserRead[]>('/users'),
  create: (payload: UserCreatePayload) => apiRequest<UserRead>('/users', {
    method: 'POST',
    body: JSON.stringify(payload),
  }),
}

export const patientsApi = {
  list: () => apiRequest<Patient[]>('/patients'),
  get: (id: number) => apiRequest<Patient>(`/patients/${id}`),
  create: (payload: PatientPayload) => apiRequest<Patient>('/patients', {
    method: 'POST',
    body: JSON.stringify(payload),
  }),
  update: (id: number, payload: PatientPayload) => apiRequest<Patient>(`/patients/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  }),
  deactivate: (id: number) => apiRequest<void>(`/patients/${id}`, {
    method: 'DELETE',
  }),
}
