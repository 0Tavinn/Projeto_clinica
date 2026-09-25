const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1'

export async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('lumina_access_token')
  const headers = new Headers(options.headers)
  headers.set('Content-Type', 'application/json')
  if (token) headers.set('Authorization', `Bearer ${token}`)

  const response = await fetch(`${API_URL}${path}`, { ...options, headers })
  if (!response.ok) {
    const body = await response.json().catch(() => ({})) as { detail?: string }
    throw new Error(body.detail ?? 'Não foi possível concluir a operação.')
  }
  return response.status === 204 ? (undefined as T) : response.json() as Promise<T>
}

export async function login(email: string, password: string) {
  const body = new URLSearchParams({ username: email, password })
  const response = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  })
  if (!response.ok) throw new Error('E-mail ou senha inválidos.')
  const data = await response.json() as { access_token: string; refresh_token: string }
  localStorage.setItem('lumina_access_token', data.access_token)
  localStorage.setItem('lumina_refresh_token', data.refresh_token)
  return data
}
