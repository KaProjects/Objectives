import {afterEach, beforeEach, describe, expect, it, vi} from 'vitest'
import {flushPromises, shallowMount} from '@vue/test-utils'

const {api} = vi.hoisted(() => ({
  api: {
    checkAuthentication: vi.fn(),
    login: vi.fn(),
    logout: vi.fn(),
  },
}))

vi.mock('@/services/apiClient', () => ({api}))

import App from '@/App.vue'
import router from '@/router'
import {appState, clearError, setAuthStatus} from '@/state/appState'

async function mountApp() {
  await router.push('/')
  return shallowMount(App, {
    global: {
      plugins: [router],
      stubs: {
        RouterView: {template: '<div>Values route</div>'},
      },
    },
  })
}

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setAuthStatus('checking')
    clearError()
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders neither login nor protected content while checking the cookie session', async () => {
    let finishSessionCheck
    api.checkAuthentication.mockImplementation(() => new Promise((resolve) => {
      finishSessionCheck = resolve
    }))
    const wrapper = await mountApp()

    expect(api.checkAuthentication).toHaveBeenCalledOnce()
    expect(wrapper.find('login-stub').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('Values route')

    finishSessionCheck()
    await flushPromises()

    expect(appState.authStatus).toBe('authenticated')
    expect(wrapper.text()).toContain('Values route')
  })

  it('renders login when the cookie session is missing or expired', async () => {
    api.checkAuthentication.mockRejectedValue({status: 401, message: 'Unauthorized'})
    const wrapper = await mountApp()
    await flushPromises()

    expect(appState.authStatus).toBe('anonymous')
    expect(appState.error).toBeNull()
    expect(wrapper.find('login-stub').exists()).toBe(true)
    expect(wrapper.text()).not.toContain('Values route')
  })

  it('shows non-authentication failures as blocking backend errors', async () => {
    api.checkAuthentication.mockRejectedValue(new Error('Backend unavailable'))
    const wrapper = await mountApp()
    await flushPromises()

    expect(appState.authStatus).toBe('anonymous')
    expect(wrapper.text()).toContain('Backend unavailable')
    expect(wrapper.find('login-stub').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('Values route')
  })
})
