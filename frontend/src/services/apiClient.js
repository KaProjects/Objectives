import {appState} from '@/state/appState'

export class ApiError extends Error {
  constructor(status, message) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

const backend = import.meta.env.VITE_BACKEND_URL

async function request(path, {method = 'GET', data, authenticated = true} = {}) {
  const headers = new Headers()

  if (data !== undefined) {
    headers.set('Content-Type', 'application/json')
  }

  if (authenticated && appState.token) {
    headers.set('Authorization', `Bearer ${appState.token}`)
  }

  const response = await fetch(`${backend}${path}`, {
    method,
    headers,
    body: data === undefined ? undefined : JSON.stringify(data),
  })
  const contentType = response.headers.get('content-type') ?? ''
  const body = contentType.includes('application/json')
      ? await response.json()
      : await response.text()

  if (!response.ok) {
    if (response.status === 401) {
      sessionStorage.removeItem('token')
    }
    const message = typeof body === 'string'
      ? body
      : body?.error?.message ?? body?.message ?? JSON.stringify(body)
    throw new ApiError(response.status, message)
  }

  return body
}

export const api = {
  get: (path) => request(path),
  delete: (path) => request(path, {method: 'DELETE'}),
  post: (path, data) => request(path, {method: 'POST', data}),
  put: (path, data) => request(path, {method: 'PUT', data}),
  login: (username, password) => request('/authenticate', {
    method: 'POST',
    data: {user: username, password},
    authenticated: false,
  }),
}
