import {afterEach, beforeEach, describe, expect, it, vi} from 'vitest'
import {appState, clearError, setToken} from '@/state/appState'
import {api} from './apiClient'

describe('api client', () => {
  beforeEach(() => {
    setToken(null)
    clearError()
    vi.restoreAllMocks()
  })

  afterEach(() => vi.restoreAllMocks())

  it('adds a bearer token and parses JSON responses', async () => {
    setToken('user-token')
    global.fetch = vi.fn().mockResolvedValue(new Response(JSON.stringify([{id: 1}]), {
      headers: {'content-type': 'application/json'},
    }))

    await expect(api.get('/values')).resolves.toEqual([{id: 1}])
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/values'), expect.objectContaining({
      method: 'GET',
      headers: expect.any(Headers),
    }))
    expect(fetch.mock.calls[0][1].headers.get('Authorization')).toBe('Bearer user-token')
  })

  it('sends JSON without authentication for login', async () => {
    global.fetch = vi.fn().mockResolvedValue(new Response('new-token'))

    await expect(api.login('alice', 'password')).resolves.toBe('new-token')
    const options = fetch.mock.calls[0][1]
    expect(options.headers.get('Authorization')).toBeNull()
    expect(options.body).toBe(JSON.stringify({user: 'alice', password: 'password'}))
  })

  it('sets global error state and rejects failed requests', async () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    global.fetch = vi.fn().mockResolvedValue(new Response('Not found', {status: 404}))

    await expect(api.get('/missing')).rejects.toThrow('[404] Not found')
    expect(appState.error).toBe('[404] Not found')
  })
})
