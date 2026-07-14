import {beforeEach, describe, expect, it, vi} from 'vitest'
import {flushPromises, shallowMount} from '@vue/test-utils'

const {api} = vi.hoisted(() => ({api: {get: vi.fn()}}))
vi.mock('@/services/apiClient', () => ({api}))

import App from './App.vue'
import {appState, clearError, setToken, unselectValue} from '@/state/appState'

describe('App', () => {
  beforeEach(() => {
    setToken(null)
    unselectValue()
    clearError()
    sessionStorage.clear()
    vi.clearAllMocks()
  })

  it('loads values after a remembered token is restored', async () => {
    sessionStorage.setItem('token', 'remembered-token')
    api.get.mockResolvedValue([{id: 1, name: 'Health'}])
    const wrapper = shallowMount(App)
    await flushPromises()

    expect(appState.token).toBe('remembered-token')
    expect(api.get).toHaveBeenCalledWith('/values')
    expect(wrapper.text()).toContain('Health')
  })
})
