import assert from 'node:assert/strict'
import test from 'node:test'

import { authApi, sessionStorageService } from '../src/api.ts'

function makeStorage() {
  const values = new Map()
  return {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, value),
    removeItem: (key) => values.delete(key),
  }
}

function jsonResponse(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

test('restaura a sessão renovando o access token expirado', async () => {
  globalThis.sessionStorage = makeStorage()
  sessionStorageService.setTokens({
    access_token: 'expired-access',
    refresh_token: 'valid-refresh',
    token_type: 'bearer',
  })
  const requests = []
  globalThis.fetch = async (url, options) => {
    const path = new URL(url).pathname
    requests.push(path)
    if (path === '/api/v1/auth/refresh') {
      assert.equal(JSON.parse(options.body).refresh_token, 'valid-refresh')
      return jsonResponse({ access_token: 'new-access', refresh_token: 'new-refresh', token_type: 'bearer' })
    }
    assert.equal(path, '/api/v1/auth/me')
    return options.headers.get('Authorization') === 'Bearer new-access'
      ? jsonResponse({ id: 1, role: 'DENTIST' })
      : jsonResponse({ error: { message: 'Token expirado.' } }, 401)
  }

  assert.deepEqual(await authApi.restoreSession(), { id: 1, role: 'DENTIST' })
  assert.deepEqual(requests, ['/api/v1/auth/me', '/api/v1/auth/refresh', '/api/v1/auth/me'])
  assert.equal(sessionStorageService.getAccessToken(), 'new-access')
  assert.equal(sessionStorageService.getRefreshToken(), 'new-refresh')
})

test('restaura a sessão quando resta apenas o refresh token', async () => {
  globalThis.sessionStorage = makeStorage()
  sessionStorageService.setTokens({ access_token: '', refresh_token: 'valid-refresh', token_type: 'bearer' })
  globalThis.fetch = async (url, options) => {
    const path = new URL(url).pathname
    if (path === '/api/v1/auth/refresh') {
      return jsonResponse({ access_token: 'new-access', refresh_token: 'new-refresh', token_type: 'bearer' })
    }
    assert.equal(path, '/api/v1/auth/me')
    return options.headers.get('Authorization') === 'Bearer new-access'
      ? jsonResponse({ id: 1 })
      : jsonResponse({ error: { message: 'Sem token.' } }, 401)
  }

  assert.deepEqual(await authApi.restoreSession(), { id: 1 })
})

test('descarta a sessão quando o refresh token é inválido', async () => {
  globalThis.sessionStorage = makeStorage()
  sessionStorageService.setTokens({
    access_token: 'expired-access',
    refresh_token: 'invalid-refresh',
    token_type: 'bearer',
  })
  globalThis.fetch = async (url) => {
    const path = new URL(url).pathname
    return jsonResponse({ error: { message: 'Sessão expirada.' } }, 401)
  }

  assert.equal(await authApi.restoreSession(), null)
  assert.equal(sessionStorageService.getAccessToken(), null)
  assert.equal(sessionStorageService.getRefreshToken(), null)
})
