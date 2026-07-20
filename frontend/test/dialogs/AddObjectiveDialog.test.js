import {describe, expect, it} from 'vitest'
import {mount} from '@vue/test-utils'

import AddObjectiveDialog from '@/dialogs/AddObjectiveDialog.vue'

describe('AddObjectiveDialog', () => {
  it('uses the supplied objective draft', () => {
    const wrapper = mount(AddObjectiveDialog, {
      props: {
        modelValue: true,
        valueId: 7,
        initialObjective: {name: 'Walk', description: 'Short walk'},
      },
    })

    expect(wrapper.vm.newObjective).toEqual({name: 'Walk', description: 'Short walk'})
  })
})
