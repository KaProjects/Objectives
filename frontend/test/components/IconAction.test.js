import {describe, expect, it, vi} from 'vitest'
import {mount} from '@vue/test-utils'
import IconAction from '@/components/IconAction.vue'

describe('IconAction', () => {
  it('renders a named native button and forwards its action', async () => {
    const onClick = vi.fn()
    const parentClick = vi.fn()
    const wrapper = mount({
      components: {IconAction},
      setup: () => ({onClick, parentClick}),
      template: `
        <div @click="parentClick">
          <IconAction label="Delete idea" icon="mdi-delete" :size="18" @click="onClick"/>
        </div>
      `,
    })
    const button = wrapper.get('button')

    expect(button.attributes('type')).toBe('button')
    expect(button.attributes('aria-label')).toBe('Delete idea')

    await button.trigger('click')
    expect(onClick).toHaveBeenCalledOnce()
    expect(parentClick).not.toHaveBeenCalled()
  })
})
