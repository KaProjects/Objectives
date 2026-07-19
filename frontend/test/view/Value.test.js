import {beforeEach, describe, expect, it, vi} from 'vitest'
import {flushPromises, shallowMount} from '@vue/test-utils'

const {api} = vi.hoisted(() => ({
  api: {get: vi.fn(), post: vi.fn(), delete: vi.fn()},
}))
vi.mock('@/services/apiClient', () => ({api}))

import Value from '@/view/Value.vue'
import router from '@/router'

describe('Value view', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('loads its value and adds a created objective to its list', async () => {
    api.get.mockImplementation((path) => path.endsWith('/subvalue')
        ? Promise.resolve([{id: '0', name: 'Default', ideas: []}])
        : Promise.resolve({id: 1, name: 'Health', objectives: []}))
    await router.push('/values/1')
    const wrapper = shallowMount(Value, {global: {plugins: [router]}})
    await flushPromises()
    wrapper.vm.addObjective({id: 2, name: 'Walk', state: 'active'})

    expect(wrapper.vm.value.objectives).toEqual([{id: 2, name: 'Walk', state: 'active'}])
    expect(wrapper.vm.tab).toBe('active')
    expect(api.get).toHaveBeenCalledWith('/value/1/subvalue')
  })

  it('opens a prefilled Objective dialog from an idea', async () => {
    api.get.mockImplementation((path) => path.endsWith('/subvalue')
        ? Promise.resolve([{id: '0', name: 'Default', ideas: []}])
        : Promise.resolve({id: 1, name: 'Health', objectives: []}))
    await router.push('/values/1')
    const wrapper = shallowMount(Value, {global: {plugins: [router]}})
    await flushPromises()

    wrapper.vm.tab = 'ideas'
    wrapper.vm.createObjectiveFromIdea({
      subvalueId: '0',
      idea: {id: 'idea-1', name: 'Walk', description: 'Short walk'},
    })

    expect(wrapper.vm.tab).toBe('ideas')
    expect(wrapper.vm.openAddObjDialog).toBe(true)
    expect(wrapper.vm.objectiveDraft).toEqual({name: 'Walk', description: 'Short walk'})
  })

  it('deletes the source idea after creating its Objective', async () => {
    api.get.mockImplementation((path) => path.endsWith('/subvalue')
        ? Promise.resolve([{id: '0', name: 'Default', ideas: [{id: 'idea-1', name: 'Walk', description: ''}]}])
        : Promise.resolve({id: 1, name: 'Health', objectives: []}))
    api.delete.mockResolvedValue(undefined)
    await router.push('/values/1')
    const wrapper = shallowMount(Value, {global: {plugins: [router]}})
    await flushPromises()
    wrapper.vm.createObjectiveFromIdea({
      subvalueId: '0',
      idea: {id: 'idea-1', name: 'Walk', description: ''},
    })

    await wrapper.vm.addObjective({id: 2, name: 'Walk', state: 'active'})

    expect(api.delete).toHaveBeenCalledWith('/value/1/subvalue/0/idea/idea-1')
    expect(wrapper.vm.subvalues[0].ideas).toEqual([])
  })
})
