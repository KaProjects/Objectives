import {afterEach, beforeEach, describe, expect, it, vi} from 'vitest'
import {mount, shallowMount} from '@vue/test-utils'

const {api} = vi.hoisted(() => ({
  api: {
    get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn(), login: vi.fn(),
  },
}))

vi.mock('@/services/apiClient', () => ({api}))

import KeyResultDialog from '@/dialogs/KeyResultDialog.vue'
import Editable from '@/components/Editable.vue'

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

  it('provides a date picker when editing the deadline', () => {
    const wrapper = mount(KeyResultDialog, {
      props: {
        modelValue: true,
        kr: {...keyResult},
        kr_parent: {...keyResult, obj_state: 'active'},
      },
    })

    const deadlineEditor = wrapper.findAllComponents(Editable)
        .find((editable) => editable.props('label') === 'Deadline')

    expect(deadlineEditor.props('datePicker')).toBe(true)
  })

  it('keeps created and reviewed date pickers editable for an inactive Key Result and Objective', () => {
    const wrapper = mount(KeyResultDialog, {
      props: {
        modelValue: true,
        kr: {...keyResult, state: 'failed'},
        kr_parent: {...keyResult, state: 'failed', obj_state: 'failed'},
      },
    })
    const editors = wrapper.findAllComponents(Editable)
    const nameEditor = editors.find((editor) => editor.props('label') === 'Name')
    const createdEditor = editors.find((editor) => editor.props('label') === 'Created')
    const reviewedEditor = editors.find((editor) => editor.props('label') === 'Failed')

    expect(nameEditor.props('editable')).toBe(false)
    expect(createdEditor.props()).toMatchObject({editable: true, datePicker: true})
    expect(reviewedEditor.props()).toMatchObject({editable: true, datePicker: true})
  })

  it('updates Key Result dates without closing the dialog', async () => {
    const updatedDates = {date_created: '2025-12-20', date_reviewed: '2026-01-01'}
    api.put.mockResolvedValue(updatedDates)
    const wrapper = shallowMount(KeyResultDialog, {
      props: {
        modelValue: true,
        kr: {...keyResult, state: 'completed'},
        kr_parent: {...keyResult, state: 'completed', obj_state: 'achieved'},
      },
    })

    expect(await wrapper.vm.updateKeyResultDate('date_created', updatedDates.date_created)).toBe(true)

    expect(api.put).toHaveBeenCalledWith('/key_result/2/dates', updatedDates)
    expect(wrapper.vm.keyResult.date_created).toBe('2025-12-20')
    expect(wrapper.vm.keyResultParent.date_created).toBe('2025-12-20')
    expect(wrapper.emitted('updated')).toContainEqual([expect.objectContaining(updatedDates)])
    expect(wrapper.emitted('close')).toBeUndefined()
  })

  it('keeps the previous Key Result dates when correction fails', async () => {
    api.put.mockRejectedValue(new Error('Date update failed'))
    const wrapper = shallowMount(KeyResultDialog, {
      props: {
        modelValue: true,
        kr: {...keyResult},
        kr_parent: {...keyResult, obj_state: 'active'},
      },
    })

    expect(await wrapper.vm.updateKeyResultDate('date_reviewed', '2025-12-20')).toBe(false)

    expect(wrapper.vm.keyResult.date_reviewed).toBe('2026-01-01')
    expect(wrapper.vm.submissionError).toBe('Date update failed')
    expect(wrapper.emitted('updated')).toBeUndefined()
  })

  it.each(['failed', 'completed'])('closes after the Key Result is marked %s', async (state) => {
    api.put.mockResolvedValue(state)
    api.get.mockResolvedValue({date_reviewed: '2026-01-02'})
    const wrapper = shallowMount(KeyResultDialog, {
      props: {
        modelValue: true,
        kr: {...keyResult},
        kr_parent: {...keyResult, obj_state: 'active'},
      },
    })

    await wrapper.vm.updateKeyResultState(state)

    expect(api.put).toHaveBeenCalledWith('/key_result/2/state', {state})
    expect(wrapper.emitted('updated')).toContainEqual([expect.objectContaining({id: 2, state})])
    expect(wrapper.emitted('close')).toHaveLength(1)
    expect(wrapper.emitted('update:modelValue')).toContainEqual([false])
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
    await wrapper.vm.updateTaskValue(wrapper.vm.keyResult.tasks[0], 'Updated task')

    expect(wrapper.emitted('updated')).toBeUndefined()
  })

  it('deletes and closes only after the request succeeds', async () => {
    api.delete.mockResolvedValue(undefined)
    const wrapper = shallowMount(KeyResultDialog, {
      props: {
        modelValue: true,
        kr: {...keyResult},
        kr_parent: {...keyResult, obj_state: 'active'},
      },
    })

    await wrapper.vm.deleteKeyResult()

    expect(api.delete).toHaveBeenCalledWith('/key_result/2')
    expect(wrapper.emitted('deleted')).toEqual([[expect.objectContaining({id: 2})]])
    expect(wrapper.emitted('close')).toHaveLength(1)
    expect(wrapper.emitted('update:modelValue')).toContainEqual([false])
  })

  it('keeps the dialog open and displays a failed deletion', async () => {
    api.delete.mockRejectedValue(new Error('Delete failed'))
    const wrapper = shallowMount(KeyResultDialog, {
      props: {
        modelValue: true,
        kr: {...keyResult},
        kr_parent: {...keyResult, obj_state: 'active'},
      },
    })

    await wrapper.vm.deleteKeyResult()

    expect(wrapper.vm.submissionError).toBe('Delete failed')
    expect(wrapper.emitted('deleted')).toBeUndefined()
    expect(wrapper.emitted('close')).toBeUndefined()
    expect(wrapper.emitted('update:modelValue')).toBeUndefined()
  })
})
