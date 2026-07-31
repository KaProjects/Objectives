import {beforeEach, describe, expect, it, vi} from 'vitest'
import {flushPromises, shallowMount} from '@vue/test-utils'

const {api} = vi.hoisted(() => ({api: {get: vi.fn()}}))
vi.mock('@/services/apiClient', () => ({api}))

import KeyResults from '@/view/KeyResults.vue'
import KeyResultDialog from '@/dialogs/KeyResultDialog.vue'
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
    expect(wrapper.findAll('.deadlineAlert')).toHaveLength(2)
    expect(wrapper.find('.missingDeadline').text()).toBe('Deadline: Not set')
  })

  it('opens the existing Key Result dialog with full Key Result data', async () => {
    api.get.mockImplementation((path) => path === '/key_result/overview'
        ? Promise.resolve([{
          id: 3, name: 'Sooner', value_id: 7, value_name: 'Health', objective_id: 11,
          objective_name: 'Energy', objective_state: 'active', t: '2000-08-01',
        }])
        : Promise.resolve({id: 3, objective_id: 11, name: 'Sooner', state: 'active', tasks: []}))
    await router.push('/key-results')
    const wrapper = shallowMount(KeyResults, {global: {plugins: [router]}})
    await flushPromises()

    const keyResultCard = wrapper.get('.keyResultCard')
    expect(keyResultCard.attributes()).toMatchObject({
      role: 'button',
      tabindex: '0',
      'aria-label': 'Open Key Result Sooner',
    })

    await keyResultCard.trigger('keydown.space')
    await flushPromises()

    expect(api.get).toHaveBeenCalledWith('/key_result/3')
    expect(wrapper.vm.openKeyResultDialog).toBe(true)
    expect(wrapper.vm.selectedKeyResultParent.state).toBe('active')
    expect(wrapper.vm.selectedKeyResultParent.obj_state).toBe('active')
    expect(wrapper.vm.selectedKeyResultParent.value_id).toBe(7)
    expect(wrapper.getComponent(KeyResultDialog).props('showLocateObjective')).toBe(true)
  })

  it('opens the parent Value and Objective requested by the dialog', async () => {
    api.get.mockImplementation((path) => path === '/key_result/overview'
        ? Promise.resolve([{
          id: 3, name: 'Sooner', value_id: 7, value_name: 'Health', objective_id: 11,
          objective_name: 'Energy', objective_state: 'active', t: '2026-08-01',
        }])
        : Promise.resolve({id: 3, objective_id: 11, name: 'Sooner', state: 'active', tasks: []}))
    await router.push('/key-results')
    const wrapper = shallowMount(KeyResults, {global: {plugins: [router]}})
    await flushPromises()
    await wrapper.get('.keyResultCard').trigger('click')
    await flushPromises()

    wrapper.getComponent(KeyResultDialog).vm.$emit('locate-objective', {
      valueId: 7,
      objectiveId: 11,
    })
    await flushPromises()

    expect(router.currentRoute.value.name).toBe('value')
    expect(router.currentRoute.value.params).toMatchObject({valueId: '7', tab: 'active'})
    expect(router.currentRoute.value.query.objective).toBe('11')
  })

  it('keeps an edited active Key Result open and reorders it after a deadline change', async () => {
    api.get.mockResolvedValue([
      {id: 1, name: 'August', value_name: 'Health', objective_name: 'Energy', objective_state: 'active', t: '2026-08-01'},
      {id: 2, name: 'December', value_name: 'Work', objective_name: 'Launch', objective_state: 'active', t: '2026-12-01'},
    ])
    await router.push('/key-results')
    const wrapper = shallowMount(KeyResults, {global: {plugins: [router]}})
    await flushPromises()
    wrapper.vm.openKeyResultDialog = true

    wrapper.vm.updateKeyResult({id: 2, name: 'July', t: '2026-07-01'})

    expect(wrapper.vm.openKeyResultDialog).toBe(true)
    expect(wrapper.vm.keyResults.map((keyResult) => keyResult.id)).toEqual([2, 1])
    expect(wrapper.vm.keyResults[0]).toEqual(expect.objectContaining({name: 'July', t: '2026-07-01'}))
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
