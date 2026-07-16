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

  it('loads its value and adds an objective', async () => {
    api.get.mockResolvedValue({id: 1, name: 'Health', objectives: []})
    api.post.mockResolvedValue({id: 2, name: 'Walk', state: 'active'})
    const wrapper = shallowMount(Value)
    await flushPromises()
    wrapper.vm.newObj = {name: 'Walk', description: 'Daily'}
    await wrapper.vm.addObjective()

    expect(api.post).toHaveBeenCalledWith('/objective', {name: 'Walk', description: 'Daily', value_id: 1})
    expect(wrapper.vm.value.objectives).toEqual([{id: 2, name: 'Walk', state: 'active'}])
    unselectValue()
  })
})
