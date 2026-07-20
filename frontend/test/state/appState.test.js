import {beforeEach, describe, expect, it, vi} from 'vitest'
import {appState, clearError, setError, setToken} from '@/state/appState'

describe('appState', () => {
  beforeEach(() => {
    setToken(null)
    clearError()
  })

  it('stores authentication state', () => {
    setToken('token')
    expect(appState.token).toBe('token')
  })

  it('normalizes errors into a displayable message', () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    setError(new Error('Request failed'))
    expect(appState.error).toBe('Request failed')
  })
})
