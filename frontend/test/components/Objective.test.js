import {beforeEach, describe, expect, it, vi} from 'vitest'
import {flushPromises, shallowMount} from '@vue/test-utils'

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
      props: {
        objective: {
          ...objective,
          key_results: [{
            id: 2,
            name: 'Walk',
            state: 'active',
            date_created: '2026-01-01',
            date_reviewed: '2026-01-01',
          }],
        },
      },
    })

    const keyResultCard = wrapper.get('.kr')
    expect(keyResultCard.attributes()).toMatchObject({
      role: 'button',
      tabindex: '0',
      'aria-label': 'Open Key Result Walk',
    })

    await keyResultCard.trigger('keydown.enter')
    await flushPromises()

    expect(api.get).toHaveBeenCalledWith('/key_result/2')
    expect(wrapper.vm.openKrDialog).toBe(true)
  })

  it('uses a replacement objective prop when opening its dialog', async () => {
    const wrapper = shallowMount(Objective, {
      props: {objective: {...objective}},
    })
    const replacement = {...objective, id: 8, name: 'Updated objective'}

    await wrapper.setProps({objective: replacement})
    wrapper.vm.openObjective()

    expect(wrapper.vm.selectedObj).toEqual(replacement)
  })

  it('sorts active key results by deadline before inactive ones', () => {
    const wrapper = shallowMount(Objective, {props: {objective: {...objective}}})
    const keyResults = [
      {id: 1, state: 'failed', date_created: '2026-01-05', date_reviewed: '2026-01-06'},
      {id: 2, state: 'active', t: '2026-03-01', date_created: '2026-01-01', date_reviewed: '2026-01-03'},
      {id: 3, state: 'active', t: '2026-02-01', date_created: '2026-01-02', date_reviewed: '2026-01-03'},
      {id: 4, state: 'completed', date_created: '2026-01-01', date_reviewed: '2026-01-04'},
      {id: 5, state: 'active', t: 'text', date_created: '2026-01-03', date_reviewed: '2026-01-10'},
      {id: 6, state: 'active', t: '', date_created: '2026-01-04', date_reviewed: '2026-01-02'},
    ]

    expect(keyResults.sort(wrapper.vm.compareKeyResults).map((result) => result.id))
        .toEqual([3, 2, 5, 6, 1, 4])
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
    expect(historicalWrapper.findAll('.krMeta')).toHaveLength(0)
    expect(historicalWrapper.findAll('.standardKrContent')).toHaveLength(3)
    historicalWrapper.unmount()
  })

  it('shows active deadlines and terminal review dates only inside active Objectives', () => {
    const keyResults = [
      {
        id: 1, name: 'Valid deadline', state: 'active', t: '2026-08-15',
        date_reviewed: '2026-07-03', resolved_tasks_count: 1, all_tasks_count: 3,
      },
      {
        id: 2, name: 'Missing deadline', state: 'active', t: '15 August',
        date_reviewed: '2026-07-02', resolved_tasks_count: 0, all_tasks_count: 1,
      },
      {id: 3, name: 'Completed', state: 'completed', date_reviewed: '2026-08-16'},
      {id: 4, name: 'Failed', state: 'failed', date_reviewed: '2026-08-17'},
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

    const activePlaques = wrapper.findAll('.kr.active')
    expect(activePlaques[0].find('.krMetaDate').text()).toBe('15/08/2026')
    expect(activePlaques[0].text()).not.toContain('03/07/2026')
    expect(activePlaques[1].classes()).not.toContain('krPlaque--missingDeadline')
    expect(activePlaques[1].find('.krMetaDate').text()).toBe('')
    expect(activePlaques[1].find('.krDeadlineMissing').attributes('aria-label')).toBe('Deadline not set')
    expect(wrapper.find('.kr.completed .krMetaDate').text()).toBe('16/08/2026')
    expect(wrapper.find('.kr.failed .krMetaDate').text()).toBe('17/08/2026')
  })
})
