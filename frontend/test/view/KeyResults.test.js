import {beforeEach, describe, expect, it, vi} from 'vitest'
import {flushPromises, shallowMount} from '@vue/test-utils'

const {api} = vi.hoisted(() => ({api: {get: vi.fn()}}))
vi.mock('@/services/apiClient', () => ({api}))

import KeyResults from '@/view/KeyResults.vue'
import router from '@/router'

describe('Key Results overview', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows all Key Results ordered by a valid SMART deadline', async () => {
    api.get.mockResolvedValue([
      {id: 1, name: 'No deadline', value_name: 'Health', objective_name: 'Energy', objective_state: 'active', t: 'later'},
      {id: 2, name: 'Later', value_name: 'Work', objective_name: 'Launch', objective_state: 'active', t: '2099-12-01'},
      {id: 3, name: 'Sooner', value_name: 'Health', objective_name: 'Energy', objective_state: 'active', t: '2000-08-01'},
    ])
    await router.push('/key-results')
    const wrapper = shallowMount(KeyResults, {global: {plugins: [router]}})
    await flushPromises()

    expect(api.get).toHaveBeenCalledWith('/key_result/overview')
    expect(wrapper.vm.keyResults.map((keyResult) => keyResult.id)).toEqual([3, 2, 1])
    expect(wrapper.text()).toContain('Health / Energy')
    expect(wrapper.text()).toContain('Deadline: Not set')
    expect(wrapper.findAll('.deadlineAlert')).toHaveLength(1)
  })

  it('opens the existing Key Result dialog with full Key Result data', async () => {
    api.get.mockImplementation((path) => path === '/key_result/overview'
        ? Promise.resolve([{id: 3, name: 'Sooner', value_name: 'Health', objective_name: 'Energy', objective_state: 'active', t: '2000-08-01'}])
        : Promise.resolve({id: 3, name: 'Sooner', tasks: []}))
    await router.push('/key-results')
    const wrapper = shallowMount(KeyResults, {global: {plugins: [router]}})
    await flushPromises()

    await wrapper.find('.keyResultCard').trigger('click')
    await flushPromises()

    expect(api.get).toHaveBeenCalledWith('/key_result/3')
    expect(wrapper.vm.openKeyResultDialog).toBe(true)
    expect(wrapper.vm.selectedKeyResultParent.obj_state).toBe('active')
  })

  it('removes a Key Result after it is completed or failed', async () => {
    api.get.mockResolvedValue([
      {id: 3, name: 'Sooner', value_name: 'Health', objective_name: 'Energy', objective_state: 'active', t: '2026-08-01'},
    ])
    await router.push('/key-results')
    const wrapper = shallowMount(KeyResults, {global: {plugins: [router]}})
    await flushPromises()
    wrapper.vm.openKeyResultDialog = true

    wrapper.vm.updateKeyResult({id: 3, state: 'completed'})

    expect(wrapper.vm.keyResults).toEqual([])
    expect(wrapper.vm.openKeyResultDialog).toBe(false)
  })
})
