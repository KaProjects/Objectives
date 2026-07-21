import {beforeEach, describe, expect, it, vi} from 'vitest'
import {flushPromises, shallowMount} from '@vue/test-utils'

const {api} = vi.hoisted(() => ({api: {get: vi.fn()}}))
vi.mock('@/services/apiClient', () => ({api}))

import Values from '@/view/Values.vue'
import router from '@/router'

describe('Values view', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    await router.push('/')
  })

  it('loads and renders values when the route is mounted', async () => {
    api.get.mockResolvedValue([{
      id: 1,
      name: 'Health',
      description: 'Build sustainable health habits.',
      active_count: 2,
      achievements_count: 1,
    }])

    const wrapper = shallowMount(Values, {global: {plugins: [router]}})
    await flushPromises()

    expect(api.get).toHaveBeenCalledWith('/values')
    expect(wrapper.text()).toContain('Health')
    expect(wrapper.text()).toContain('Active: 2')
    expect(wrapper.text()).toContain('Achievements: 1')
  })

  it('opens the selected value on its active tab', async () => {
    api.get.mockResolvedValue([{
      id: 7,
      name: 'Relationships',
      description: '',
      active_count: 0,
      achievements_count: 0,
    }])

    const wrapper = shallowMount(Values, {global: {plugins: [router]}})
    await flushPromises()
    await wrapper.get('.value').trigger('click')
    await flushPromises()

    expect(router.currentRoute.value.name).toBe('value')
    expect(router.currentRoute.value.params).toMatchObject({valueId: '7', tab: 'active'})
  })
})
