import {afterEach, beforeEach, describe, expect, it, vi} from 'vitest'
import {flushPromises, shallowMount} from '@vue/test-utils'

const {api} = vi.hoisted(() => ({api: {get: vi.fn()}}))
vi.mock('@/services/apiClient', () => ({api}))

import App from './App.vue'
import {appState, clearError, setError, setToken, unselectValue} from '@/state/appState'

describe('App', () => {
  beforeEach(() => {
    setToken(null)
    unselectValue()
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
    const wrapper = shallowMount(App)
    await flushPromises()

    expect(appState.token).toBe('remembered-token')
    expect(api.get).toHaveBeenCalledWith('/values')
    expect(wrapper.text()).toContain('Health')
  })

  it('keeps the app usable and clears the error when the alert is dismissed', async () => {
    setError('Backend unavailable')
    const wrapper = shallowMount(App, {
      global: {
        stubs: {
          'v-alert': {
            emits: ['click:close'],
            template: '<button @click="$emit(\'click:close\')"><slot /></button>',
          },
        },
      },
    })

    expect(wrapper.find('login-stub').exists()).toBe(true)
    await wrapper.find('button').trigger('click')
    expect(appState.error).toBeNull()
  })
})
