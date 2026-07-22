import {beforeEach, describe, expect, it, vi} from 'vitest'
import {mount} from '@vue/test-utils'

const {api} = vi.hoisted(() => ({
  api: {
    get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn(), login: vi.fn(),
  },
}))

vi.mock('@/services/apiClient', () => ({api}))

import AddSubvalueDialog from '@/dialogs/AddSubvalueDialog.vue'

describe('AddSubvalueDialog', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('creates an empty subvalue and notifies its parent', async () => {
    const subvalue = {id: '3', name: 'Nutrition', ideas: []}
    api.post.mockResolvedValue(subvalue)
    const wrapper = mount(AddSubvalueDialog, {props: {modelValue: true, valueId: 7}})
    wrapper.vm.name = 'Nutrition'

    await wrapper.vm.addSubvalue()

    expect(api.post).toHaveBeenCalledWith('/value/7/subvalue', {name: 'Nutrition'})
    expect(wrapper.emitted('created')).toEqual([[subvalue]])
  })
})
