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
  objective_id: 7,
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

  it('reactively summarizes completed, failed, and active tasks', async () => {
    const tasks = [
      {id: 1, value: 'Completed one', state: 'finished'},
      {id: 2, value: 'Completed two', state: 'finished'},
      {id: 3, value: 'Failed one', state: 'failed'},
      {id: 4, value: 'Remaining one', state: 'active'},
    ]
    api.put.mockResolvedValue({state: 'failed'})
    api.get.mockResolvedValue({date_reviewed: '2026-01-02'})
    api.delete.mockResolvedValue(undefined)
    const wrapper = mount(KeyResultDialog, {
      props: {
        modelValue: true,
        kr: {...keyResult, tasks},
        kr_parent: {
          ...keyResult, obj_state: 'active', all_tasks_count: 4, resolved_tasks_count: 3,
        },
      },
    })

    expect(wrapper.vm.taskSummary).toEqual({
      completed: 2, failed: 1, active: 1, total: 4, completedPercentage: 50, failedPercentage: 25,
    })
    expect(wrapper.get('.taskSummary').attributes('aria-label'))
        .toBe('Tasks: 50% completed (2), 25% failed (1), 1 active out of 4 total')

    await wrapper.vm.updateTaskState(wrapper.vm.keyResult.tasks[3], 'failed')
    expect(wrapper.vm.taskSummary).toEqual({
      completed: 2, failed: 2, active: 0, total: 4, completedPercentage: 50, failedPercentage: 50,
    })

    await wrapper.vm.addCreatedTasks([
      {id: 5, value: 'Remaining two', state: 'active'},
      {id: 6, value: 'Remaining three', state: 'active'},
    ])
    expect(wrapper.vm.taskSummary).toEqual({
      completed: 2, failed: 2, active: 2, total: 6, completedPercentage: 33.3, failedPercentage: 33.3,
    })
    expect(wrapper.vm.formatTaskPercentage(wrapper.vm.taskSummary.completedPercentage)).toBe('33.3')

    await wrapper.vm.deleteTask(wrapper.vm.keyResult.tasks[0])
    expect(wrapper.vm.taskSummary).toEqual({
      completed: 1, failed: 2, active: 2, total: 5, completedPercentage: 20, failedPercentage: 40,
    })
  })

  it('uses zero percentages when no tasks have been resolved', () => {
    const wrapper = shallowMount(KeyResultDialog, {
      props: {
        modelValue: true,
        kr: {...keyResult, tasks: [{id: 1, value: 'Remaining', state: 'active'}]},
        kr_parent: {...keyResult, obj_state: 'active'},
      },
    })

    expect(wrapper.vm.taskSummary).toEqual({
      completed: 0, failed: 0, active: 1, total: 1, completedPercentage: 0, failedPercentage: 0,
    })
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
    expect(wrapper.find('.smartMarks').exists()).toBe(false)
    expect(wrapper.find('.smartRow').exists()).toBe(false)
    expect(wrapper.find('.smartDivider').exists()).toBe(false)
    expect(wrapper.find('.taskSummary').exists()).toBe(true)
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

  it.each(['failed', 'completed'])('requests its Objective after the Key Result is marked %s', async (state) => {
    api.put.mockResolvedValue(state)
    api.get.mockResolvedValue({date_reviewed: '2026-01-02'})
    const wrapper = shallowMount(KeyResultDialog, {
      props: {
        modelValue: true,
        kr: {...keyResult},
        kr_parent: {...keyResult, value_id: 3, obj_state: 'active'},
      },
    })

    await wrapper.vm.updateKeyResultState(state)

    expect(api.put).toHaveBeenCalledWith('/key_result/2/state', {state})
    expect(wrapper.emitted('updated')).toContainEqual([expect.objectContaining({id: 2, state})])
    expect(wrapper.emitted('locate-objective')).toEqual([[
      {objectiveId: 7, valueId: 3, objectiveState: 'active'},
    ]])
  })

  it('requests its parent Objective from the locate button', async () => {
    const wrapper = mount(KeyResultDialog, {
      props: {
        modelValue: true,
        kr: {...keyResult},
        kr_parent: {...keyResult, value_id: 3, obj_state: 'active'},
        showLocateObjective: true,
      },
    })

    await wrapper.get('.locateObjectiveButton').trigger('click')

    expect(wrapper.emitted('locate-objective')).toEqual([[
      {objectiveId: 7, valueId: 3, objectiveState: 'active'},
    ]])
  })

  it('hides the locate button unless its parent view enables it', () => {
    const wrapper = mount(KeyResultDialog, {
      props: {
        modelValue: true,
        kr: {...keyResult},
        kr_parent: {...keyResult, obj_state: 'active'},
      },
    })

    expect(wrapper.find('.locateObjectiveButton').exists()).toBe(false)
  })

  it('does not request its Objective when a terminal state update fails', async () => {
    api.put.mockRejectedValue(new Error('State update failed'))
    const wrapper = shallowMount(KeyResultDialog, {
      props: {
        modelValue: true,
        kr: {...keyResult},
        kr_parent: {...keyResult, value_id: 3, obj_state: 'active'},
      },
    })

    await wrapper.vm.updateKeyResultState('failed')

    expect(wrapper.emitted('locate-objective')).toBeUndefined()
    expect(wrapper.emitted('close')).toBeUndefined()
    expect(wrapper.vm.submissionError).toBe('State update failed')
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
