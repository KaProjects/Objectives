import {afterEach, beforeEach, describe, expect, it, vi} from 'vitest'
import {flushPromises, mount} from '@vue/test-utils'

const {api} = vi.hoisted(() => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    login: vi.fn(),
    checkAuthentication: vi.fn(),
    logout: vi.fn(),
  },
}))

vi.mock('@/services/apiClient', () => ({api}))

import Login from '@/components/Login.vue'
import {appState, clearError, setAuthStatus} from '@/state/appState'

async function submitLogin(wrapper) {
  const inputs = wrapper.findAll('input')
  await inputs[0].setValue('alice')
  await inputs[1].setValue('password')
  await wrapper.find('form').trigger('submit')
  await flushPromises()
}

describe('Login', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setAuthStatus('anonymous')
    clearError()
  })

  afterEach(() => vi.restoreAllMocks())

  it('authenticates through the cookie session and notifies its parent', async () => {
    api.login.mockResolvedValue(undefined)
    const storageSpy = vi.spyOn(Storage.prototype, 'setItem')
    const wrapper = mount(Login)

    await submitLogin(wrapper)

    expect(api.login).toHaveBeenCalledWith('alice', 'password')
    expect(appState.authStatus).toBe('authenticated')
    expect(storageSpy).not.toHaveBeenCalled()
    expect(wrapper.emitted('logged-in')).toEqual([[]])
  })

  it('shows invalid credentials locally and stays anonymous', async () => {
    api.login.mockRejectedValue({status: 401, message: 'Unauthorized'})
    const wrapper = mount(Login)

    await submitLogin(wrapper)

    expect(appState.authStatus).toBe('anonymous')
    expect(appState.error).toBeNull()
    expect(wrapper.text()).toContain('Invalid username or password')
  })
})
