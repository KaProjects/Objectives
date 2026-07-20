import {beforeEach, describe, expect, it, vi} from 'vitest'
import {mount} from '@vue/test-utils'

const {api} = vi.hoisted(() => ({
  api: {
    get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn(), login: vi.fn(),
  },
}))

vi.mock('@/services/apiClient', () => ({api}))

import AddKeyResultDialog from '@/dialogs/AddKeyResultDialog.vue'

describe('AddKeyResultDialog', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('submits SMART setup values', async () => {
    const keyResult = {
      id: 3,
      name: 'Walk',
      description: 'Daily walk',
      s: 'true',
      m: '10 km',
      a: '5 km',
      r: 'true',
      t: '2026-12-31',
    }
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

  it('uses an initial key result draft', () => {
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

  it('validates required fields and unlocks Add after a correction', async () => {
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
})
