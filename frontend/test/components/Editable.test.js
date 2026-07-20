import {describe, expect, it, vi} from 'vitest'
import {flushPromises, mount} from '@vue/test-utils'

import Editable from '@/components/Editable.vue'

describe('Editable', () => {
  it('renders the supplied editor content', () => {
    const wrapper = mount(Editable, {
      props: {value: 'Name', label: 'Name', submit: vi.fn()},
      slots: {display: '<input aria-label="Name">'},
    })

    expect(wrapper.find('input[aria-label="Name"]').exists()).toBe(true)
  })

  it('delays closing after an unfocus save', async () => {
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

  it('closes without saving when its value is unchanged', async () => {
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
})
