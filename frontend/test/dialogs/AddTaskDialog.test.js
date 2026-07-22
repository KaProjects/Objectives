import {beforeEach, describe, expect, it, vi} from 'vitest'
import {shallowMount} from '@vue/test-utils'

const {api} = vi.hoisted(() => ({
  api: {
    get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn(), login: vi.fn(),
  },
}))

vi.mock('@/services/apiClient', () => ({api}))

import AddTaskDialog from '@/dialogs/AddTaskDialog.vue'

describe('AddTaskDialog', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('creates one task when no mode is selected', async () => {
    api.post.mockResolvedValue({id: 11, kr_id: 2, state: 'active', value: 'Walk'})
    const wrapper = shallowMount(AddTaskDialog, {props: {modelValue: true, keyResultId: 2}})
    wrapper.vm.task.value = 'Walk'

    await wrapper.vm.addTasks()

    expect(api.post).toHaveBeenCalledWith('/task', {kr_id: 2, value: 'Walk'})
    expect(wrapper.emitted('created')).toEqual([[[{id: 11, kr_id: 2, state: 'active', value: 'Walk'}]]])
  })

  it('creates repetitive or daily tasks using their endpoints', async () => {
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
})
