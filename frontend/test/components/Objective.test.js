import {beforeEach, describe, expect, it, vi} from 'vitest'
import {shallowMount} from '@vue/test-utils'

const {api} = vi.hoisted(() => ({
  api: {
    get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn(), login: vi.fn(),
  },
}))

vi.mock('@/services/apiClient', () => ({api}))

import Objective from '@/components/Objective.vue'

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

describe('Objective', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    api.get.mockResolvedValue([])
  })

  it('loads a key result before opening its dialog', async () => {
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

    expect(keyResults.sort(wrapper.vm.compareKeyResults).map((result) => result.id))
        .toEqual([3, 2, 1, 4])
  })

  it('renders distinct active, completed, and failed Key Result plaques', () => {
    const keyResults = [
      {id: 1, name: 'In progress', state: 'active', resolved_tasks_count: 1, all_tasks_count: 3},
      {id: 2, name: 'Finished result', state: 'completed'},
      {id: 3, name: 'Missed result', state: 'failed'},
    ]
    const wrapper = shallowMount(Objective, {
      props: {objective: {...objective, key_results: keyResults}},
      global: {
        stubs: {
          ObjectiveDialog: true,
          KeyResultDialog: true,
          AddKeyResultDialog: true,
        },
      },
    })

    expect(wrapper.findAll('.krPlaque')).toHaveLength(3)
    expect(wrapper.findAll('.krStatusMark')).toHaveLength(3)
    expect(wrapper.find('.kr.active .krStateLabel').exists()).toBe(false)
    expect(wrapper.find('.kr.completed .krStateLabel').text()).toBe('Completed')
    expect(wrapper.find('.kr.failed .krStateLabel').text()).toBe('Failed')
    expect(wrapper.vm.keyResultStatus).toEqual({
      active: {label: 'Active', icon: 'mdi-progress-clock'},
      completed: {label: 'Completed', icon: 'mdi-check-bold'},
      failed: {label: 'Failed', icon: 'mdi-close-thick'},
    })
    wrapper.unmount()

    const historicalWrapper = shallowMount(Objective, {
      props: {objective: {...objective, state: 'achieved', key_results: keyResults}},
    })
    expect(historicalWrapper.findAll('.krPlaque')).toHaveLength(0)
    expect(historicalWrapper.findAll('.krStatusMark')).toHaveLength(0)
    expect(historicalWrapper.findAll('.standardKrContent')).toHaveLength(3)
    historicalWrapper.unmount()
  })
})
