import {afterEach, beforeEach, describe, expect, it, vi} from 'vitest'
import {appState, clearError, setToken} from '@/state/appState'
import {api} from './apiClient'

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
    setToken(null)
    clearError()
    vi.restoreAllMocks()
  })

  afterEach(() => vi.restoreAllMocks())

  it('adds a bearer token and parses JSON responses', async () => {
    setToken('user-token')
    global.fetch = vi.fn().mockResolvedValue(mockResponse({
      contentType: 'application/json',
      body: [{id: 1}],
    }))

    await expect(api.get('/values')).resolves.toEqual([{id: 1}])
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/values'), expect.objectContaining({
      method: 'GET',
      headers: expect.anything(),
    }))
    expect(fetch.mock.calls[0][1].headers.get('Authorization')).toBe('Bearer user-token')
  })

  it('sends JSON without authentication for login', async () => {
    global.fetch = vi.fn().mockResolvedValue(mockResponse({body: 'new-token'}))

    await expect(api.login('alice', 'password')).resolves.toBe('new-token')
    const options = fetch.mock.calls[0][1]
    expect(options.headers.get('Authorization')).toBeNull()
    expect(options.body).toBe(JSON.stringify({user: 'alice', password: 'password'}))
  })

  it('sets global error state and rejects failed requests', async () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    global.fetch = vi.fn().mockResolvedValue(mockResponse({ok: false, status: 404, body: 'Not found'}))

    await expect(api.get('/missing')).rejects.toThrow('[404] Not found')
    expect(appState.error).toBe('[404] Not found')
  })
})
