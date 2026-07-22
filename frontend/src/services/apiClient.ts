import {setAuthStatus} from '@/state/appState'

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

interface RequestOptions<TData> {
  method?: string
  data?: TData
}

const backend = import.meta.env.VITE_BACKEND_URL
const mutationMethods = new Set(['POST', 'PUT', 'PATCH', 'DELETE'])

async function request<TResponse, TData = never>(
    path: string,
    {method = 'GET', data}: RequestOptions<TData> = {},
): Promise<TResponse> {
  const headers = new Headers()
  const normalizedMethod = method.toUpperCase()

  if (data !== undefined) {
    headers.set('Content-Type', 'application/json')
  }

  if (mutationMethods.has(normalizedMethod)) {
    headers.set('X-Objectives-Client', 'web')
  }

  const response = await fetch(`${backend}${path}`, {
    method: normalizedMethod,
    headers,
    credentials: 'include',
    body: data === undefined ? undefined : JSON.stringify(data),
  })
  const contentType = response.headers.get('content-type') ?? ''
  const body: unknown = response.status === 204
    ? undefined
    : contentType.includes('application/json')
      ? await response.json()
      : await response.text()

  if (!response.ok) {
    if (response.status === 401) {
      setAuthStatus('anonymous')
    }
    const message = errorMessage(body)
    throw new ApiError(response.status, message)
  }

  return body as TResponse
}

function errorMessage(body: unknown): string {
  if (typeof body === 'string') return body
  if (body && typeof body === 'object') {
    const responseBody = body as {error?: {message?: unknown}; message?: unknown}
    if (typeof responseBody.error?.message === 'string') return responseBody.error.message
    if (typeof responseBody.message === 'string') return responseBody.message
  }
  return JSON.stringify(body)
}

export const api = {
  get: <TResponse>(path: string) => request<TResponse>(path),
  delete: <TResponse = void>(path: string) => request<TResponse>(path, {method: 'DELETE'}),
  post: <TResponse, TData = unknown>(path: string, data: TData) =>
    request<TResponse, TData>(path, {method: 'POST', data}),
  put: <TResponse, TData = unknown>(path: string, data: TData) =>
    request<TResponse, TData>(path, {method: 'PUT', data}),
  login: (username: string, password: string) => request<void, {user: string; password: string}>(
      '/authenticate',
      {method: 'POST', data: {user: username, password}},
  ),
  checkAuthentication: () => request<void>('/authenticate'),
  logout: () => request<void>('/authenticate', {method: 'DELETE'}),
}
