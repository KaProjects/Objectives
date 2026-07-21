import {afterEach, beforeEach, describe, expect, it, vi} from 'vitest'
import {flushPromises, shallowMount} from '@vue/test-utils'

const {api} = vi.hoisted(() => ({
  api: {
    get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn(), login: vi.fn(),
  },
}))

vi.mock('@/services/apiClient', () => ({api}))

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

describe('ObjectiveDialog', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.spyOn(console, 'error').mockImplementation(() => {})
    api.get.mockResolvedValue([])
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('loads ideas for its objective and emits close', async () => {
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

  it('emits updates instead of mutating its objective prop', async () => {
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

  it('keeps the draft and editor intact when saving fails', async () => {
    api.put.mockRejectedValueOnce(new Error('Network unavailable'))
    const wrapper = shallowMount(ObjectiveDialog, {
      props: {modelValue: true, obj: {...objective}},
    })
    await wrapper.vm.updateObjective('name', 'Updated exercise')

    expect(wrapper.vm.draftObjective.name).toBe('Exercise')
    expect(wrapper.vm.objective.name).toBe('Exercise')
    expect(wrapper.vm.submissionError).toBe('Network unavailable')
    expect(wrapper.emitted('updated')).toBeUndefined()
  })

  it('deletes and closes only after the request succeeds', async () => {
    api.delete.mockResolvedValue(undefined)
    const wrapper = shallowMount(ObjectiveDialog, {
      props: {modelValue: true, obj: {...objective}},
    })

    await wrapper.vm.deleteObjective()

    expect(api.delete).toHaveBeenCalledWith('/objective/1')
    expect(wrapper.emitted('deleted')).toEqual([[expect.objectContaining({id: 1})]])
    expect(wrapper.emitted('close')).toHaveLength(1)
    expect(wrapper.emitted('update:modelValue')).toContainEqual([false])
  })

  it('keeps the dialog open and displays a failed deletion', async () => {
    api.delete.mockRejectedValue(new Error('Delete failed'))
    const wrapper = shallowMount(ObjectiveDialog, {
      props: {modelValue: true, obj: {...objective}},
    })

    await wrapper.vm.deleteObjective()

    expect(wrapper.vm.submissionError).toBe('Delete failed')
    expect(wrapper.emitted('deleted')).toBeUndefined()
    expect(wrapper.emitted('close')).toBeUndefined()
    expect(wrapper.emitted('update:modelValue')).toBeUndefined()
  })

  it('turns an idea into a key result, then removes the source idea and closes', async () => {
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

  it('keeps a created Key Result visible when source-idea cleanup fails', async () => {
    const idea = {id: 3, value: 'Walk after lunch'}
    api.get.mockResolvedValue([idea])
    api.delete.mockRejectedValue(new Error('Firebase unavailable'))
    const wrapper = shallowMount(ObjectiveDialog, {
      props: {modelValue: true, obj: {...objective, ideas_count: 1}},
    })
    await flushPromises()
    wrapper.vm.createKeyResultFromIdea(idea)

    const keyResult = {id: 9, name: 'Walk after lunch'}
    await wrapper.vm.keyResultCreatedFromIdea(keyResult)

    expect(wrapper.emitted('key-result-created')).toEqual([[keyResult]])
    expect(wrapper.vm.ideas).toEqual([idea])
    expect(wrapper.vm.submissionError).toContain('Key Result was created')
    expect(wrapper.emitted('close')).toBeUndefined()
  })
})
