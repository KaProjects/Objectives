import {beforeEach, describe, expect, it, vi} from 'vitest'
import {flushPromises, mount} from '@vue/test-utils'

const {api} = vi.hoisted(() => ({
  api: {
    get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn(), login: vi.fn(),
  },
}))

vi.mock('@/services/apiClient', () => ({api}))

import Login from '@/components/Login.vue'

describe('Login', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('authenticates, stores the token, and notifies its parent', async () => {
    api.login.mockResolvedValue('token')
    const wrapper = mount(Login)
    const inputs = wrapper.findAll('input')
    await inputs[0].setValue('alice')
    await inputs[1].setValue('password')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(api.login).toHaveBeenCalledWith('alice', 'password')
    expect(wrapper.emitted('logged-in')).toEqual([['token']])
  })
})
