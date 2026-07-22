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
    await router.push('/value/1')
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
    await router.push('/value/1')
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
    await router.push('/value/1')
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

  it('reports and retries source-idea cleanup after creating an Objective', async () => {
    api.get.mockImplementation((path) => path.endsWith('/subvalue')
        ? Promise.resolve([{id: '0', name: 'Default', ideas: [{id: 'idea-1', name: 'Walk', description: ''}]}])
        : Promise.resolve({id: 1, name: 'Health', objectives: []}))
    api.delete.mockRejectedValueOnce(new Error('Firebase unavailable')).mockResolvedValueOnce(undefined)
    await router.push('/value/1')
    const wrapper = shallowMount(Value, {global: {plugins: [router]}})
    await flushPromises()
    wrapper.vm.createObjectiveFromIdea({
      subvalueId: '0',
      idea: {id: 'idea-1', name: 'Walk', description: ''},
    })

    await wrapper.vm.addObjective({id: 2, name: 'Walk', state: 'active'})

    expect(wrapper.vm.value.objectives).toContainEqual({id: 2, name: 'Walk', state: 'active'})
    expect(wrapper.vm.subvalues[0].ideas).toHaveLength(1)
    expect(wrapper.vm.conversionError).toContain('Objective was created')

    await wrapper.vm.retrySourceIdeaDeletion()

    expect(api.delete).toHaveBeenCalledTimes(2)
    expect(wrapper.vm.subvalues[0].ideas).toEqual([])
    expect(wrapper.vm.conversionError).toBeNull()
  })

  it('places done Objectives on a newest-first timeline using their finished date', async () => {
    api.get.mockImplementation((path) => path.endsWith('/subvalue')
        ? Promise.resolve([])
        : Promise.resolve({
          id: 1,
          name: 'Health',
          objectives: [
            {id: 1, state: 'achieved', date_finished: '2026-03-01'},
            {id: 2, state: 'failed', date_finished: '2026-07-10'},
            {id: 3, state: 'achieved', date_finished: 'not a date'},
            {id: 4, state: 'active', date_finished: ''},
            {id: 5, state: 'achieved', date_finished: '2026-07-10'},
          ],
        }))
    await router.push('/value/1')
    const wrapper = shallowMount(Value, {global: {plugins: [router]}})
    await flushPromises()

    expect(wrapper.vm.doneObjectiveTimeline.map((group) => group.finishedDate)).toEqual(['2026-07-10', '2026-03-01', null])
    expect(wrapper.vm.doneObjectiveTimeline[0].objectives.map((objective) => objective.id)).toEqual([2, 5])
    expect(wrapper.vm.doneObjectiveTimeline.map((group) => group.showYear)).toEqual([true, false, false])
  })

  it('keeps the selected tab in the URL and restores it from the URL', async () => {
    api.get.mockImplementation((path) => path.endsWith('/subvalue')
        ? Promise.resolve([])
        : Promise.resolve({id: 1, name: 'Health', objectives: []}))
    await router.push('/value/1/ideas')
    const wrapper = shallowMount(Value, {global: {plugins: [router]}})
    await flushPromises()

    expect(wrapper.vm.tab).toBe('ideas')
    wrapper.vm.tab = 'done'
    await flushPromises()
    expect(router.currentRoute.value.params.tab).toBe('done')

    await router.push('/value/1/active')
    await flushPromises()
    expect(wrapper.vm.tab).toBe('active')
  })
})
