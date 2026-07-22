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
    wrapper.unmount()
  })

  it('hides its display content while editing', async () => {
    const wrapper = mount(Editable, {
      props: {value: 'Name', label: 'Name', submit: vi.fn()},
      slots: {display: '<span class="display-value">Name</span>'},
    })

    expect(wrapper.find('.display-value').exists()).toBe(true)

    await wrapper.vm.startEditing()

    expect(wrapper.find('.display-value').exists()).toBe(false)
    expect(wrapper.find('input').exists()).toBe(true)
    wrapper.unmount()
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

  it('submits a date selected with its native date picker', async () => {
    const submit = vi.fn().mockResolvedValue(true)
    const wrapper = mount(Editable, {
      props: {value: '2026-07-01', label: 'Deadline', submit, datePicker: true},
      slots: {display: '<span>2026-07-01</span>'},
    })

    await wrapper.vm.startEditing()
    const datePicker = wrapper.find('input[type="date"]')
    datePicker.element.value = '2026-08-15'
    await datePicker.trigger('change')
    await flushPromises()

    expect(submit).toHaveBeenCalledWith('2026-08-15')
    expect(wrapper.vm.isEditing).toBe(false)
    wrapper.unmount()
  })

  it('shares one pair of window listeners across all editor instances', () => {
    const addListener = vi.spyOn(window, 'addEventListener')
    const removeListener = vi.spyOn(window, 'removeEventListener')
    const wrapper = mount({
      components: {Editable},
      setup: () => ({submit: vi.fn()}),
      template: `
        <div>
          <Editable value="First" label="First" :submit="submit"><template #display>First</template></Editable>
          <Editable value="Second" label="Second" :submit="submit"><template #display>Second</template></Editable>
        </div>
      `,
    })

    expect(addListener.mock.calls.filter(([type]) => type === 'pointerdown')).toHaveLength(1)
    expect(addListener.mock.calls.filter(([type]) => type === 'click')).toHaveLength(1)

    wrapper.unmount()

    expect(removeListener.mock.calls.filter(([type]) => type === 'pointerdown')).toHaveLength(1)
    expect(removeListener.mock.calls.filter(([type]) => type === 'click')).toHaveLength(1)
    addListener.mockRestore()
    removeListener.mockRestore()
  })
})
