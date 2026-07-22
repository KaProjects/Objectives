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

    const createButton = wrapper.get('.createObjectiveFromIdea')
    expect(createButton.element.tagName).toBe('BUTTON')
    expect(createButton.attributes('aria-label')).toBe('Create Objective from Walk')

    await createButton.trigger('click')

    expect(wrapper.emitted('create-objective')).toEqual([[{
      subvalueId: '1', idea,
    }]])
  })

  it('enters idea editing from the keyboard', async () => {
    const idea = {id: 'idea-1', name: 'Walk', description: 'Short walk'}
    const wrapper = mount(Ideas, {
      props: {valueId: 7, subvalues: [{id: '1', name: 'Fitness', ideas: [idea]}]},
    })

    const content = wrapper.get('.ideaContent')
    expect(content.attributes()).toMatchObject({
      role: 'button',
      tabindex: '0',
      'aria-label': 'Edit idea Walk',
    })

    await content.trigger('keydown.enter')

    expect(wrapper.find('.ideaEditor').exists()).toBe(true)
  })

  it('opens idea deletion without entering edit mode', async () => {
    const idea = {id: 'idea-1', name: 'Walk', description: 'Short walk'}
    const wrapper = mount(Ideas, {
      props: {valueId: 7, subvalues: [{id: '1', name: 'Fitness', ideas: [idea]}]},
    })
    const ideaItem = wrapper.findComponent(IdeaItem)

    await wrapper.get('.deleteIdea').trigger('click')

    expect(ideaItem.vm.confirmDeletion).toBe(true)
    expect(ideaItem.vm.isEditing).toBe(false)
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
