import {beforeEach, describe, expect, it, vi} from 'vitest'
import {flushPromises, shallowMount} from '@vue/test-utils'

const {api} = vi.hoisted(() => ({
  api: {get: vi.fn(), post: vi.fn(), delete: vi.fn()},
}))
vi.mock('@/services/apiClient', () => ({api}))

import Value from '@/view/Value.vue'
import {selectValue, unselectValue} from '@/state/appState'

describe('Value view', () => {
  beforeEach(() => {
    selectValue({id: 1})
    vi.clearAllMocks()
  })

  it('loads its value and adds a created objective to its list', async () => {
    api.get.mockResolvedValue({id: 1, name: 'Health', objectives: []})
    const wrapper = shallowMount(Value)
    await flushPromises()
    wrapper.vm.addObjective({id: 2, name: 'Walk', state: 'active'})

    expect(wrapper.vm.value.objectives).toEqual([{id: 2, name: 'Walk', state: 'active'}])
    expect(wrapper.vm.tab).toBe('active')
    unselectValue()
  })
})
