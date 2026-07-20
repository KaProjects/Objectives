import {afterEach, beforeEach, describe, expect, it, vi} from 'vitest'
import {mount, shallowMount} from '@vue/test-utils'

const {api} = vi.hoisted(() => ({
  api: {
    get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn(), login: vi.fn(),
  },
}))

vi.mock('@/services/apiClient', () => ({api}))

import KeyResultDialog from '@/dialogs/KeyResultDialog.vue'

const keyResult = {
  id: 2,
  name: 'Walk',
  description: 'Walk daily',
  state: 'active',
  date_created: '2026-01-01',
  date_reviewed: '2026-01-01',
  tasks: [],
  s: 'Specific', m: 'Measurable', a: 'Attainable', r: 'Relevant', t: 'Timed',
}

describe('KeyResultDialog', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.spyOn(console, 'error').mockImplementation(() => {})
    api.get.mockResolvedValue([])
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('closes by emitting an event', () => {
    const wrapper = shallowMount(KeyResultDialog, {
      props: {
        modelValue: true,
        kr: {...keyResult},
        kr_parent: {...keyResult, obj_state: 'active'},
      },
    })
    wrapper.vm.closeDialog()
    expect(wrapper.emitted('close')).toHaveLength(1)
    expect(wrapper.emitted('update:modelValue')).toEqual([[false]])
  })

  it('opens the Add Task dialog', async () => {
    const wrapper = mount(KeyResultDialog, {
      props: {
        modelValue: true,
        kr: {...keyResult},
        kr_parent: {id: 1, obj_state: 'active', all_tasks_count: 0},
      },
    })
    const addTaskButton = wrapper.findAll('button').find((button) => button.text() === 'Add Task')

    await addTaskButton.trigger('click')

    expect(wrapper.vm.openAddTaskDialog).toBe(true)
  })

  it('sends named draft fields in its update payload', async () => {
    api.put.mockResolvedValue('02/01/2026')
    const wrapper = shallowMount(KeyResultDialog, {
      props: {
        modelValue: true,
        kr: {...keyResult},
        kr_parent: {...keyResult, obj_state: 'active'},
      },
    })
    wrapper.vm.draftKeyResult.attainable = 'Reachable daily walk'
    await wrapper.vm.updateKeyResult()

    expect(api.put).toHaveBeenCalledWith('/key_result/2', {
      name: 'Walk',
      description: 'Walk daily',
      s: 'Specific',
      m: 'Measurable',
      a: 'Reachable daily walk',
      r: 'Relevant',
      t: 'Timed',
    })
    expect(wrapper.emitted('updated')).toContainEqual([expect.objectContaining({
      id: 2,
      a: 'Reachable daily walk',
    })])
  })

  it('does not emit stale updates when refreshing its review date fails', async () => {
    api.put.mockResolvedValue({value: 'Updated task'})
    api.get.mockRejectedValueOnce(new Error('Refresh failed'))
    const wrapper = shallowMount(KeyResultDialog, {
      props: {
        modelValue: true,
        kr: {...keyResult, tasks: [{id: 4, value: 'Task', state: 'active'}]},
        kr_parent: {...keyResult, obj_state: 'active'},
      },
    })
    await wrapper.vm.updateTaskValue(wrapper.vm.kr.tasks[0], 'Updated task')

    expect(wrapper.emitted('updated')).toBeUndefined()
  })
})
