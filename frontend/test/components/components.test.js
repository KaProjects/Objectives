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
import KeyResultDialog from '@/components/KeyResultDialog.vue'
import Login from '@/components/Login.vue'
import Objective from '@/components/Objective.vue'
import ObjectiveDialog from '@/components/ObjectiveDialog.vue'

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

  it('Editable invokes cancel and submit callbacks', async () => {
    const cancel = vi.fn()
    const submit = vi.fn()
    const wrapper = mount(Editable, {props: {cancel, submit, index: 3}})

    await wrapper.findAll('button')[0].trigger('click')
    await wrapper.findAll('button')[1].trigger('click')
    expect(cancel).toHaveBeenCalledOnce()
    expect(submit).toHaveBeenCalledWith(3)
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

  it('Ideas loads ideas and adds a newly created idea', async () => {
    api.get.mockResolvedValue([{id: 1, value: 'First'}])
    api.post.mockResolvedValue({new_id: 2, idea: 'Second'})
    const wrapper = mount(Ideas, {props: {valueId: 7}})
    await flushPromises()
    expect(wrapper.text()).toContain('First')

    const input = wrapper.find('input')
    await input.setValue('Second')
    await wrapper.vm.addIdea()
    expect(wrapper.text()).toContain('Second')
    expect(api.post).toHaveBeenCalledWith('/value/7/idea', {idea: 'Second'})
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
    wrapper.vm.editingValue = 'Updated exercise'
    await wrapper.vm.updateObjective('name')

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
    wrapper.vm.editingField = 'name'
    wrapper.vm.editingValue = 'Updated exercise'
    await wrapper.vm.updateObjective('name')

    expect(wrapper.vm.draftObjective.name).toBe('Exercise')
    expect(wrapper.vm.obj.name).toBe('Exercise')
    expect(wrapper.vm.editingField).toBe('name')
    expect(wrapper.vm.submissionError).toBe('Network unavailable')
    expect(wrapper.emitted('updated')).toBeUndefined()
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
    wrapper.vm.editingValue = 'Updated task'
    await wrapper.vm.updateTaskValue(wrapper.vm.kr.tasks[0])

    expect(wrapper.emitted('updated')).toBeUndefined()
  })
})
