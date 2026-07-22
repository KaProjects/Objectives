import {afterEach, beforeEach, describe, expect, it, vi} from 'vitest'
import {appState, clearError, setAuthStatus, setError} from '@/state/appState'
import {ApiError, api} from '@/services/apiClient'

function mockResponse({ok = true, status = 200, contentType = '', body = ''} = {}) {
  return {
    ok,
    status,
    headers: {
      get: (name) => name === 'content-type' ? contentType : null,
    },
    json: vi.fn().mockResolvedValue(body),
    text: vi.fn().mockResolvedValue(typeof body === 'string' ? body : JSON.stringify(body)),
  }
}

describe('api client', () => {
  beforeEach(() => {
    setAuthStatus('checking')
    clearError()
    vi.restoreAllMocks()
  })

  afterEach(() => vi.restoreAllMocks())

  it('includes browser credentials without an authorization header', async () => {
    global.fetch = vi.fn().mockResolvedValue(mockResponse({
      contentType: 'application/json',
      body: [{id: 1}],
    }))

    await expect(api.get('/values')).resolves.toEqual([{id: 1}])
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/values'), expect.objectContaining({
      method: 'GET',
      credentials: 'include',
      headers: expect.anything(),
    }))
    const headers = fetch.mock.calls[0][1].headers
    expect(headers.get('Authorization')).toBeNull()
    expect(headers.get('X-Objectives-Client')).toBeNull()
  })

  it('logs in with JSON and the mutation request header without returning a token', async () => {
    global.fetch = vi.fn().mockResolvedValue(mockResponse({status: 204}))

    await expect(api.login('alice', 'password')).resolves.toBeUndefined()
    const options = fetch.mock.calls[0][1]
    expect(options.method).toBe('POST')
    expect(options.credentials).toBe('include')
    expect(options.headers.get('Authorization')).toBeNull()
    expect(options.headers.get('Content-Type')).toBe('application/json')
    expect(options.headers.get('X-Objectives-Client')).toBe('web')
    expect(options.body).toBe(JSON.stringify({user: 'alice', password: 'password'}))
  })

  it('checks and clears the cookie session through the authentication endpoint', async () => {
    global.fetch = vi.fn().mockResolvedValue(mockResponse({status: 204}))

    await api.checkAuthentication()
    await api.logout()

    expect(fetch).toHaveBeenNthCalledWith(1, expect.stringContaining('/authenticate'), expect.objectContaining({
      method: 'GET',
      credentials: 'include',
    }))
    expect(fetch).toHaveBeenNthCalledWith(2, expect.stringContaining('/authenticate'), expect.objectContaining({
      method: 'DELETE',
      credentials: 'include',
    }))
    expect(fetch.mock.calls[0][1].headers.get('X-Objectives-Client')).toBeNull()
    expect(fetch.mock.calls[1][1].headers.get('X-Objectives-Client')).toBe('web')
  })

  it('transitions to anonymous without setting a global error on unauthorized requests', async () => {
    setAuthStatus('authenticated')
    global.fetch = vi.fn().mockResolvedValue(mockResponse({
      ok: false,
      status: 401,
      body: 'invalid session',
    }))

    let requestError
    try {
      await api.get('/values')
    } catch (error) {
      requestError = error
      setError(error)
    }

    expect(requestError).toBeInstanceOf(ApiError)
    expect(appState.authStatus).toBe('anonymous')
    expect(appState.error).toBeNull()
  })

  it('uses the backend error message for failed JSON requests', async () => {
    global.fetch = vi.fn().mockResolvedValue(mockResponse({
      ok: false,
      status: 404,
      contentType: 'application/json',
      body: {error: {message: 'Not found'}},
    }))

    await expect(api.get('/missing')).rejects.toMatchObject({
      name: 'ApiError',
      status: 404,
      message: 'Not found',
    })
  })
})
