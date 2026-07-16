import {afterEach, beforeEach, describe, expect, it, vi} from 'vitest'
import {flushPromises, shallowMount} from '@vue/test-utils'

const {api} = vi.hoisted(() => ({api: {get: vi.fn()}}))
vi.mock('@/services/apiClient', () => ({api}))

import App from '@/App.vue'
import router from '@/router'
import {appState, clearError, setError, setToken} from '@/state/appState'

describe('App', () => {
  beforeEach(() => {
    setToken(null)
    clearError()
    sessionStorage.clear()
    vi.clearAllMocks()
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('loads values after a remembered token is restored', async () => {
    sessionStorage.setItem('token', 'remembered-token')
    api.get.mockResolvedValue([{id: 1, name: 'Health'}])
    await router.push('/')
    const wrapper = shallowMount(App, {global: {plugins: [router]}})
    await flushPromises()

    expect(appState.token).toBe('remembered-token')
    expect(api.get).toHaveBeenCalledWith('/values')
    expect(wrapper.text()).toContain('Health')
  })

  it('hides application content while a blocking error is set', async () => {
    setError('Backend unavailable')
    await router.push('/')
    const wrapper = shallowMount(App, {
      global: {
        plugins: [router],
        stubs: {
          'v-alert': {template: '<div><slot /></div>'},
        },
      },
    })

    expect(wrapper.text()).toContain('Backend unavailable')
    expect(wrapper.find('login-stub').exists()).toBe(false)
  })
})
