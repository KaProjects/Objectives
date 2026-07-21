import {afterEach, beforeEach, describe, expect, it, vi} from 'vitest'
import {flushPromises, shallowMount} from '@vue/test-utils'

import App from '@/App.vue'
import router from '@/router'
import {appState, clearError, setError, setToken} from '@/state/appState'

describe('App', () => {
  beforeEach(() => {
    setToken(null)
    clearError()
    sessionStorage.clear()
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('restores a remembered token and renders the authenticated route', async () => {
    sessionStorage.setItem('token', 'remembered-token')
    await router.push('/')
    const wrapper = shallowMount(App, {
      global: {
        plugins: [router],
        stubs: {
          RouterView: {template: '<div>Values route</div>'},
        },
      },
    })
    await flushPromises()

    expect(appState.token).toBe('remembered-token')
    expect(wrapper.text()).toContain('Values route')
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
