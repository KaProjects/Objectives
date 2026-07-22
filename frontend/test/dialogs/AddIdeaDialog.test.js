import {beforeEach, describe, expect, it, vi} from 'vitest'
import {mount} from '@vue/test-utils'

const {api} = vi.hoisted(() => ({
  api: {
    get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn(), login: vi.fn(),
  },
}))

vi.mock('@/services/apiClient', () => ({api}))

import AddIdeaDialog from '@/dialogs/AddIdeaDialog.vue'

describe('AddIdeaDialog', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('creates an idea and notifies its parent', async () => {
    const idea = {id: 'idea-2', name: 'Second', description: 'Details'}
    api.post.mockResolvedValue(idea)
    const wrapper = mount(AddIdeaDialog, {props: {modelValue: true, valueId: 7, subvalueId: '1'}})

    wrapper.vm.newIdea = {name: 'Second', description: 'Details'}
    await wrapper.vm.addIdea()

    expect(api.post).toHaveBeenCalledWith('/value/7/subvalue/1/idea', {
      name: 'Second', description: 'Details',
    })
    expect(wrapper.emitted('created')).toEqual([[idea]])
  })
})
