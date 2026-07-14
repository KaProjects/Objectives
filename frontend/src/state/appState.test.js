import {beforeEach, describe, expect, it, vi} from 'vitest'
import {appState, clearError, selectValue, setError, setToken, unselectValue} from './appState'

describe('appState', () => {
  beforeEach(() => {
    setToken(null)
    unselectValue()
    clearError()
  })

  it('stores authentication and selected-value state', () => {
    const value = {id: 1, name: 'Health'}
    setToken('token')
    selectValue(value)
    expect(appState.token).toBe('token')
    expect(appState.selectedValue).toEqual(value)
  })

  it('normalizes errors into a displayable message', () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    setError(new Error('Request failed'))
    expect(appState.error).toBe('Request failed')
  })
})
