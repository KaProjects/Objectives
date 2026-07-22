import {beforeEach, describe, expect, it, vi} from 'vitest'
import {appState, clearError, setAuthStatus, setError} from '@/state/appState'

describe('appState', () => {
  beforeEach(() => {
    setAuthStatus('checking')
    clearError()
  })

  it('stores authentication status without a token', () => {
    setAuthStatus('authenticated')

    expect(appState.authStatus).toBe('authenticated')
    expect(appState).not.toHaveProperty('token')
  })

  it('normalizes errors into a displayable message', () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    setError(new Error('Request failed'))
    expect(appState.error).toBe('Request failed')
  })

  it('does not turn an unauthorized response into a global backend error', () => {
    setError({status: 401, message: 'Session expired'})

    expect(appState.error).toBeNull()
  })
})
