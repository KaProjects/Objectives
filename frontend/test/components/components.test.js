import {afterEach, beforeEach, describe, expect, it, vi} from 'vitest'
import {flushPromises, mount, shallowMount} from '@vue/test-utils'

const {api} = vi.hoisted(() => ({
  api: {
    get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn(), login: vi.fn(),
  },
}))

vi.mock('@/services/apiClient', () => ({api}))

import Editable from '@/components/Editable.vue'
import Ideas from '@/components/Ideas.vue'
import AddIdeaDialog from '@/dialogs/AddIdeaDialog.vue'
import AddObjectiveDialog from '@/dialogs/AddObjectiveDialog.vue'
import AddKeyResultDialog from '@/dialogs/AddKeyResultDialog.vue'
import AddSubvalueDialog from '@/dialogs/AddSubvalueDialog.vue'
import AddTaskDialog from '@/dialogs/AddTaskDialog.vue'
import KeyResultDialog from '@/dialogs/KeyResultDialog.vue'
import Login from '@/components/Login.vue'
import Objective from '@/components/Objective.vue'
import ObjectiveDialog from '@/dialogs/ObjectiveDialog.vue'

const objective = {
  id: 1,
  name: 'Exercise',
  description: 'Move more',
  state: 'active',
  date_created: '2026-01-01',
  ideas_count: 0,
  key_results: [],
}

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

describe('frontend components', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.spyOn(console, 'error').mockImplementation(() => {})
    api.get.mockResolvedValue([])
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('Editable renders the supplied editor content', () => {
    const wrapper = mount(Editable, {
      props: {value: 'Name', label: 'Name', submit: vi.fn()},
      slots: {display: '<input aria-label="Name">'},
    })

    expect(wrapper.find('input[aria-label="Name"]').exists()).toBe(true)
  })

  it('Editable delays closing after an unfocus save', async () => {
    const submit = vi.fn().mockResolvedValue(true)
    const wrapper = mount(Editable, {
      props: {value: 'Name', label: 'Name', submit},
      slots: {display: '<span>Name</span>'},
    })

    await wrapper.vm.startEditing()
    wrapper.vm.setValue('Updated name')
    window.dispatchEvent(new Event('pointerdown'))
    await wrapper.find('input').trigger('focusout')
    await flushPromises()

    expect(submit).toHaveBeenCalledWith('Updated name')
    expect(wrapper.vm.isEditing).toBe(true)
    window.dispatchEvent(new MouseEvent('click', {bubbles: true}))
    expect(wrapper.vm.isEditing).toBe(false)
    wrapper.unmount()
  })

  it('Editable closes without saving when its value is unchanged', async () => {
    const submit = vi.fn()
    const wrapper = mount(Editable, {
      props: {value: 'Name', label: 'Name', submit},
      slots: {display: '<span>Name</span>'},
    })

    await wrapper.vm.startEditing()
    await wrapper.vm.save()

    expect(submit).not.toHaveBeenCalled()
    expect(wrapper.vm.isEditing).toBe(false)
    wrapper.unmount()
  })

  it('Login authenticates, stores the token, and notifies its parent', async () => {
    api.login.mockResolvedValue('token')
    const wrapper = mount(Login)
    const inputs = wrapper.findAll('input')
    await inputs[0].setValue('alice')
    await inputs[1].setValue('password')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(api.login).toHaveBeenCalledWith('alice', 'password')
    expect(wrapper.emitted('logged-in')).toEqual([['token']])
  })

  it('Ideas renders supplied subvalue lists without loading them itself', async () => {
    const subvalues = [
      {id: '0', name: 'Default', ideas: [{id: 'first', name: 'First', description: 'First description'}]},
      {id: '1', name: 'Fitness', ideas: [{id: 'run', name: 'Run', description: ''}]},
    ]
    const wrapper = mount(Ideas, {props: {valueId: 7, subvalues}})

    expect(wrapper.text()).toContain('First')
    expect(wrapper.text()).toContain('First description')
    expect(wrapper.text()).toContain('Fitness')
    expect(wrapper.text()).not.toContain('Default')
    expect(wrapper.findAll('.addIdeaButton')).toHaveLength(2)
    expect(api.get).not.toHaveBeenCalled()
  })

  it('Ideas controls the add dialog for the list whose plus button was clicked', async () => {
    const wrapper = mount(Ideas, {
      props: {valueId: 7, subvalues: [{id: '1', name: 'Fitness', ideas: []}]},
    })

    await wrapper.find('.addIdeaButton').trigger('click')

    expect(wrapper.findComponent(AddIdeaDialog).props('modelValue')).toBe(true)
  })

  it('Ideas saves inline edits and notifies its parent', async () => {
    const idea = {id: 'idea-1', name: 'Walk', description: 'Short walk'}
    const subvalue = {id: '1', name: 'Fitness', ideas: [idea]}
    const updatedIdea = {...idea, name: 'Run', description: 'Twenty minutes'}
    api.put.mockResolvedValue(updatedIdea)
    const wrapper = mount(Ideas, {props: {valueId: 7, subvalues: [subvalue]}})

    await wrapper.vm.startEditing(subvalue, idea)
    wrapper.vm.draftIdea = {name: 'Run', description: 'Twenty minutes'}
    await wrapper.vm.saveIdea(subvalue, idea)

    expect(api.put).toHaveBeenCalledWith('/value/7/subvalue/1/idea/idea-1', {
      name: 'Run', description: 'Twenty minutes',
    })
    expect(wrapper.emitted('updated')).toEqual([[{subvalueId: '1', idea: updatedIdea}]])
  })

  it('Ideas offers objective creation from a hovered idea', async () => {
    const idea = {id: 'idea-1', name: 'Walk', description: 'Short walk'}
    const subvalue = {id: '1', name: 'Fitness', ideas: [idea]}
    const wrapper = mount(Ideas, {props: {valueId: 7, subvalues: [subvalue]}})
    wrapper.vm.selectedIdeaId = '1:idea-1'
    await wrapper.vm.$nextTick()

    await wrapper.find('.createObjectiveFromIdea').trigger('click')

    expect(wrapper.emitted('create-objective')).toEqual([[{
      subvalueId: '1', idea,
    }]])
  })

  it('Ideas saves an edited subvalue name and notifies its parent', async () => {
    const subvalue = {id: '1', name: 'Fitness', ideas: []}
    api.put.mockResolvedValue({id: '1', name: 'Training'})
    const wrapper = mount(Ideas, {props: {valueId: 7, subvalues: [subvalue]}})

    await wrapper.vm.updateSubvalue(subvalue, 'Training')

    expect(api.put).toHaveBeenCalledWith('/value/7/subvalue/1', {name: 'Training'})
    expect(wrapper.emitted('subvalue-updated')).toEqual([[{id: '1', name: 'Training'}]])
  })

  it('Ideas moves a dragged idea to another subvalue', async () => {
    const idea = {id: 'idea-1', name: 'Walk', description: ''}
    const sourceSubvalue = {id: '0', name: 'default', ideas: [idea]}
    const targetSubvalue = {id: '1', name: 'Fitness', ideas: []}
    api.put.mockResolvedValue(idea)
    const wrapper = mount(Ideas, {props: {valueId: 7, subvalues: [sourceSubvalue, targetSubvalue]}})
    wrapper.vm.draggedIdea = {sourceSubvalueId: '0', idea}

    await wrapper.vm.moveDraggedIdea(targetSubvalue)

    expect(api.put).toHaveBeenCalledWith('/value/7/subvalue/0/idea/idea-1/move', {
      target_subvalue_id: '1',
    })
    expect(wrapper.emitted('moved')).toEqual([[{
      sourceSubvalueId: '0', targetSubvalueId: '1', idea,
    }]])
  })

  it('Ideas does not move a dragged idea dropped in its source subvalue', async () => {
    const idea = {id: 'idea-1', name: 'Walk', description: ''}
    const subvalue = {id: '0', name: 'default', ideas: [idea]}
    const wrapper = mount(Ideas, {props: {valueId: 7, subvalues: [subvalue]}})
    wrapper.vm.draggedIdea = {sourceSubvalueId: '0', idea}

    await wrapper.vm.moveDraggedIdea(subvalue)

    expect(api.put).not.toHaveBeenCalled()
    expect(wrapper.emitted('moved')).toBeUndefined()
  })

  it('Ideas moves a selected touch idea after choosing a destination list', async () => {
    const idea = {id: 'idea-1', name: 'Walk', description: ''}
    const sourceSubvalue = {id: '0', name: 'default', ideas: [idea]}
    const targetSubvalue = {id: '1', name: 'Fitness', ideas: []}
    api.put.mockResolvedValue(idea)
    const wrapper = mount(Ideas, {props: {valueId: 7, subvalues: [sourceSubvalue, targetSubvalue]}})

    wrapper.vm.startMove(sourceSubvalue, idea)
    await wrapper.vm.movePendingIdea(targetSubvalue)

    expect(api.put).toHaveBeenCalledWith('/value/7/subvalue/0/idea/idea-1/move', {
      target_subvalue_id: '1',
    })
    expect(wrapper.vm.pendingMove).toBeNull()
    expect(wrapper.emitted('moved')).toEqual([[{
      sourceSubvalueId: '0', targetSubvalueId: '1', idea,
    }]])
  })

  it('Ideas deletes a subvalue and notifies its parent', async () => {
    const subvalue = {id: '1', name: 'Fitness', ideas: []}
    api.delete.mockResolvedValue(undefined)
    const wrapper = mount(Ideas, {props: {valueId: 7, subvalues: [subvalue]}})

    await wrapper.vm.deleteSubvalue(subvalue)

    expect(api.delete).toHaveBeenCalledWith('/value/7/subvalue/1')
    expect(wrapper.emitted('subvalue-deleted')).toEqual([['1']])
  })

  it('AddIdeaDialog creates an idea and notifies its parent', async () => {
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

  it('AddSubvalueDialog creates an empty subvalue and notifies its parent', async () => {
    const subvalue = {id: '3', name: 'Nutrition', ideas: []}
    api.post.mockResolvedValue(subvalue)
    const wrapper = mount(AddSubvalueDialog, {props: {modelValue: true, valueId: 7}})
    wrapper.vm.name = 'Nutrition'

    await wrapper.vm.addSubvalue()

    expect(api.post).toHaveBeenCalledWith('/value/7/subvalue', {name: 'Nutrition'})
    expect(wrapper.emitted('created')).toEqual([[subvalue]])
  })

  it('AddObjectiveDialog uses the supplied objective draft', async () => {
    const wrapper = mount(AddObjectiveDialog, {
      props: {
        modelValue: true,
        valueId: 7,
        initialObjective: {name: 'Walk', description: 'Short walk'},
      },
    })

    expect(wrapper.vm.newObjective).toEqual({name: 'Walk', description: 'Short walk'})
  })

  it('AddKeyResultDialog submits SMART setup values', async () => {
    const keyResult = {id: 3, name: 'Walk', description: 'Daily walk', s: 'true', m: '10 km', a: '5 km', r: 'true', t: '2026-12-31'}
    api.post.mockResolvedValue(keyResult)
    const wrapper = mount(AddKeyResultDialog, {props: {modelValue: true, objectiveId: 7}})
    wrapper.vm.newKeyResult = {
      name: 'Walk', description: 'Daily walk', s: true, m: '10 km', a: '5 km', r: true, t: '2026-12-31',
    }

    await wrapper.vm.addKeyResult()

    expect(api.post).toHaveBeenCalledWith('/key_result', {
      name: 'Walk', description: 'Daily walk', s: 'true', m: '10 km', a: '5 km', r: 'true', t: '2026-12-31', objective_id: 7,
    })
    expect(wrapper.emitted('created')).toEqual([[keyResult]])
  })

  it('AddKeyResultDialog uses an initial key result draft', async () => {
    const wrapper = mount(AddKeyResultDialog, {
      props: {
        modelValue: true,
        objectiveId: 7,
        initialKeyResult: {name: 'Turn idea into a result'},
        showActivator: false,
      },
    })

    expect(wrapper.vm.newKeyResult.name).toBe('Turn idea into a result')
  })

  it('AddKeyResultDialog validates required fields and unlocks Add after a correction', async () => {
    const wrapper = mount(AddKeyResultDialog, {props: {modelValue: true, objectiveId: 7}})

    await wrapper.vm.addKeyResult()

    expect(api.post).not.toHaveBeenCalled()
    expect(wrapper.vm.validationErrors).toEqual({
      name: 'Name is required.',
      s: 'Specific must be confirmed.',
      r: 'Relevant must be confirmed.',
      a: 'Attainable risks are required.',
      m: 'Acceptance criteria are required.',
      t: 'Deadline is required.',
    })
    expect(wrapper.vm.isValidationBlocked).toBe(true)

    await wrapper.find('input').setValue('Walk')

    expect(wrapper.vm.validationErrors.name).toBeUndefined()
    expect(wrapper.vm.isValidationBlocked).toBe(false)
  })

  it('Objective loads a key result before opening its dialog', async () => {
    api.get.mockResolvedValue(keyResult)
    const wrapper = shallowMount(Objective, {
      props: {objective: {...objective}},
    })
    await wrapper.vm.openKeyResult({id: 2}, 'active')
    expect(api.get).toHaveBeenCalledWith('/key_result/2')
    expect(wrapper.vm.openKrDialog).toBe(true)
  })

  it('sorts active key results before newer inactive ones', () => {
    const wrapper = shallowMount(Objective, {props: {objective: {...objective}}})
    const keyResults = [
      {id: 1, state: 'failed', date_created: '2026-01-05', date_reviewed: '2026-01-06'},
      {id: 2, state: 'active', date_created: '2026-01-01', date_reviewed: '2026-01-03'},
      {id: 3, state: 'active', date_created: '2026-01-02', date_reviewed: '2026-01-03'},
      {id: 4, state: 'completed', date_created: '2026-01-01', date_reviewed: '2026-01-04'},
    ]

    expect(keyResults.sort(wrapper.vm.compareKeyResults).map((keyResult) => keyResult.id))
        .toEqual([3, 2, 1, 4])
  })

  it('ObjectiveDialog loads ideas for its objective and emits close', async () => {
    api.get.mockResolvedValue([{id: 3, value: 'Idea'}])
    const wrapper = shallowMount(ObjectiveDialog, {
      props: {modelValue: true, obj: {...objective}},
    })
    await flushPromises()
    expect(api.get).toHaveBeenCalledWith('/objective/1/idea')
    await wrapper.vm.closeDialog()
    expect(wrapper.emitted('close')).toHaveLength(1)
    expect(wrapper.emitted('update:modelValue')).toEqual([[false]])
  })

  it('ObjectiveDialog emits updates instead of mutating its objective prop', async () => {
    api.put.mockResolvedValue(undefined)
    const inputObjective = {...objective}
    const wrapper = shallowMount(ObjectiveDialog, {
      props: {modelValue: true, obj: inputObjective},
    })
    await wrapper.vm.updateObjective('name', 'Updated exercise')

    expect(wrapper.emitted('updated')).toContainEqual([{
      id: 1, name: 'Updated exercise', description: 'Move more',
    }])
    expect(inputObjective.name).toBe('Exercise')
  })

  it('ObjectiveDialog keeps the draft and editor intact when saving fails', async () => {
    api.put.mockRejectedValueOnce(new Error('Network unavailable'))
    const wrapper = shallowMount(ObjectiveDialog, {
      props: {modelValue: true, obj: {...objective}},
    })
    await wrapper.vm.updateObjective('name', 'Updated exercise')

    expect(wrapper.vm.draftObjective.name).toBe('Exercise')
    expect(wrapper.vm.obj.name).toBe('Exercise')
    expect(wrapper.vm.submissionError).toBe('Network unavailable')
    expect(wrapper.emitted('updated')).toBeUndefined()
  })

  it('ObjectiveDialog turns an idea into a key result, then removes the source idea and closes', async () => {
    const idea = {id: 3, value: 'Walk after lunch'}
    api.get.mockResolvedValue([idea])
    api.delete.mockResolvedValue(undefined)
    const wrapper = shallowMount(ObjectiveDialog, {
      props: {modelValue: true, obj: {...objective, ideas_count: 1}},
    })
    await flushPromises()

    wrapper.vm.createKeyResultFromIdea(idea)
    expect(wrapper.vm.keyResultDraft).toEqual({name: 'Walk after lunch'})
    expect(wrapper.vm.openAddKeyResultDialog).toBe(true)

    const keyResult = {id: 9, name: 'Walk after lunch'}
    await wrapper.vm.keyResultCreatedFromIdea(keyResult)

    expect(api.delete).toHaveBeenCalledWith('/objective/1/idea/3')
    expect(wrapper.vm.ideas).toEqual([])
    expect(wrapper.emitted('key-result-created')).toEqual([[keyResult]])
    expect(wrapper.emitted('close')).toHaveLength(1)
    expect(wrapper.emitted('update:modelValue')).toContainEqual([false])
  })

  it('KeyResultDialog closes by emitting an event', () => {
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

  it('KeyResultDialog opens the Add Task dialog', async () => {
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

  it('AddTaskDialog creates one task when no mode is selected', async () => {
    api.post.mockResolvedValue({id: 11, kr_id: 2, state: 'active', value: 'Walk'})
    const wrapper = shallowMount(AddTaskDialog, {props: {modelValue: true, keyResultId: 2}})
    wrapper.vm.task.value = 'Walk'

    await wrapper.vm.addTasks()

    expect(api.post).toHaveBeenCalledWith('/task', {kr_id: 2, value: 'Walk'})
    expect(wrapper.emitted('created')).toEqual([[[{id: 11, kr_id: 2, state: 'active', value: 'Walk'}]]])
  })

  it('AddTaskDialog creates repetitive or daily tasks using their endpoints', async () => {
    api.post.mockResolvedValue([])
    const wrapper = shallowMount(AddTaskDialog, {props: {modelValue: true, keyResultId: 2}})

    wrapper.vm.task = {value: 'Walk', repetitive: true, daily: false, count: 3, fromDate: '', toDate: ''}
    await wrapper.vm.addTasks()
    expect(api.post).toHaveBeenCalledWith('/task/bulk', {kr_id: 2, value: 'Walk', count: 3})

    wrapper.vm.task = {value: 'Walk', repetitive: false, daily: true, count: 2, fromDate: '2026-07-02', toDate: '2026-07-03'}
    await wrapper.vm.addTasks()
    expect(api.post).toHaveBeenCalledWith('/task/daily', {
      kr_id: 2, value: 'Walk', from_date: '2026-07-02', to_date: '2026-07-03',
    })

    wrapper.vm.task = {value: '', repetitive: false, daily: true, count: 2, fromDate: '2026-07-02', toDate: '2026-07-03'}
    await wrapper.vm.addTasks()
    expect(api.post).toHaveBeenLastCalledWith('/task/daily', {
      kr_id: 2, value: '', from_date: '2026-07-02', to_date: '2026-07-03',
    })
  })

  it('KeyResultDialog sends named draft fields in its update payload', async () => {
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

  it('KeyResultDialog does not emit stale updates when refreshing its review date fails', async () => {
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
