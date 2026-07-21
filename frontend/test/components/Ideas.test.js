import {beforeEach, describe, expect, it, vi} from 'vitest'
import {mount} from '@vue/test-utils'

const {api} = vi.hoisted(() => ({
  api: {
    get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn(), login: vi.fn(),
  },
}))

vi.mock('@/services/apiClient', () => ({api}))

import Ideas from '@/components/Ideas.vue'
import IdeaItem from '@/components/ideas/IdeaItem.vue'
import SubvalueCard from '@/components/ideas/SubvalueCard.vue'
import AddIdeaDialog from '@/dialogs/AddIdeaDialog.vue'

describe('Ideas', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    api.get.mockResolvedValue([])
  })

  it('renders supplied subvalue lists without loading them itself', () => {
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

  it('rolls variable-height edge rows independently in each subvalue list', () => {
    const makeIdeas = (prefix) => [
      {id: `${prefix}-1`, name: `${prefix} one`, description: ''},
      {id: `${prefix}-2`, name: `${prefix} two`, description: 'A longer description'},
      {id: `${prefix}-3`, name: `${prefix} three`, description: ''},
    ]
    const wrapper = mount(Ideas, {
      props: {
        valueId: 7,
        subvalues: [
          {id: '0', name: 'Default', ideas: makeIdeas('Default')},
          {id: '1', name: 'Fitness', ideas: makeIdeas('Fitness')},
        ],
      },
    })
    const lists = wrapper.findAll('.subvalueIdeas').map((list) => list.element)
    const cards = wrapper.findAllComponents(SubvalueCard)

    function setListGeometry(list, scrollTop, clientHeight, rows) {
      Object.defineProperties(list, {
        scrollTop: {configurable: true, value: scrollTop, writable: true},
        clientHeight: {configurable: true, value: clientHeight},
      })
      rows.forEach(({top, height}, index) => {
        Object.defineProperties(list.children[index], {
          offsetTop: {configurable: true, value: top},
          offsetHeight: {configurable: true, value: height},
        })
      })
    }

    setListGeometry(lists[0], 30, 90, [
      {top: 0, height: 50},
      {top: 51, height: 80},
      {top: 132, height: 40},
    ])
    setListGeometry(lists[1], 10, 60, [
      {top: 0, height: 40},
      {top: 41, height: 40},
      {top: 82, height: 40},
    ])

    cards[0].vm.updateIdeaListRoll()
    cards[1].vm.updateIdeaListRoll()

    expect(lists[0].children[0].classList.contains('rollingTop')).toBe(true)
    expect(lists[0].children[1].classList.contains('rollingBottom')).toBe(true)
    expect(lists[1].children[0].classList.contains('rollingTop')).toBe(true)
    expect(lists[1].children[1].classList.contains('rollingBottom')).toBe(true)

    setListGeometry(lists[1], 0, 200, [
      {top: 0, height: 40},
      {top: 41, height: 40},
      {top: 82, height: 40},
    ])
    cards[1].vm.updateIdeaListRoll()

    expect(lists[0].children[0].classList.contains('rollingTop')).toBe(true)
    expect(lists[0].children[1].classList.contains('rollingBottom')).toBe(true)
    expect(lists[1].querySelector('.rollingTop, .rollingBottom')).toBeNull()
    wrapper.unmount()
  })

  it('controls the add dialog for the list whose plus button was clicked', async () => {
    const wrapper = mount(Ideas, {
      props: {valueId: 7, subvalues: [{id: '1', name: 'Fitness', ideas: []}]},
    })

    await wrapper.find('.addIdeaButton').trigger('click')

    expect(wrapper.findComponent(AddIdeaDialog).props('modelValue')).toBe(true)
  })

  it('saves inline edits and notifies its parent', async () => {
    const idea = {id: 'idea-1', name: 'Walk', description: 'Short walk'}
    const subvalue = {id: '1', name: 'Fitness', ideas: [idea]}
    const updatedIdea = {...idea, name: 'Run', description: 'Twenty minutes'}
    api.put.mockResolvedValue(updatedIdea)
    const wrapper = mount(Ideas, {props: {valueId: 7, subvalues: [subvalue]}})

    const ideaItem = wrapper.findComponent(IdeaItem)
    await ideaItem.vm.startEditing()
    ideaItem.vm.draftIdea = {name: 'Run', description: 'Twenty minutes'}
    await ideaItem.vm.saveIdea()

    expect(api.put).toHaveBeenCalledWith('/value/7/subvalue/1/idea/idea-1', {
      name: 'Run', description: 'Twenty minutes',
    })
    expect(wrapper.emitted('updated')).toEqual([[{subvalueId: '1', idea: updatedIdea}]])
  })

  it('offers objective creation from a hovered idea', async () => {
    const idea = {id: 'idea-1', name: 'Walk', description: 'Short walk'}
    const subvalue = {id: '1', name: 'Fitness', ideas: [idea]}
    const wrapper = mount(Ideas, {props: {valueId: 7, subvalues: [subvalue]}})

    await wrapper.find('.createObjectiveFromIdea').trigger('click')

    expect(wrapper.emitted('create-objective')).toEqual([[{
      subvalueId: '1', idea,
    }]])
  })

  it('saves an edited subvalue name and notifies its parent', async () => {
    const subvalue = {id: '1', name: 'Fitness', ideas: []}
    api.put.mockResolvedValue({id: '1', name: 'Training'})
    const wrapper = mount(Ideas, {props: {valueId: 7, subvalues: [subvalue]}})

    await wrapper.findComponent(SubvalueCard).vm.updateSubvalue('Training')

    expect(api.put).toHaveBeenCalledWith('/value/7/subvalue/1', {name: 'Training'})
    expect(wrapper.emitted('subvalue-updated')).toEqual([[{id: '1', name: 'Training'}]])
  })

  it('moves a dragged idea to another subvalue', async () => {
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

  it('does not move a dragged idea dropped in its source subvalue', async () => {
    const idea = {id: 'idea-1', name: 'Walk', description: ''}
    const subvalue = {id: '0', name: 'default', ideas: [idea]}
    const wrapper = mount(Ideas, {props: {valueId: 7, subvalues: [subvalue]}})
    wrapper.vm.draggedIdea = {sourceSubvalueId: '0', idea}

    await wrapper.vm.moveDraggedIdea(subvalue)

    expect(api.put).not.toHaveBeenCalled()
    expect(wrapper.emitted('moved')).toBeUndefined()
  })

  it('moves a selected touch idea after choosing a destination list', async () => {
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

  it('deletes a subvalue and notifies its parent', async () => {
    const subvalue = {id: '1', name: 'Fitness', ideas: []}
    api.delete.mockResolvedValue(undefined)
    const wrapper = mount(Ideas, {props: {valueId: 7, subvalues: [subvalue]}})

    await wrapper.findComponent(SubvalueCard).vm.deleteSubvalue()

    expect(api.delete).toHaveBeenCalledWith('/value/7/subvalue/1')
    expect(wrapper.emitted('subvalue-deleted')).toEqual([['1']])
  })
})
