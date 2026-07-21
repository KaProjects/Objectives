import {describe, expect, it} from 'vitest'
import {mount} from '@vue/test-utils'
import {ref} from 'vue'
import {useEdgeRoll} from '@/composables/useEdgeRoll'

const EdgeRollHarness = {
  setup() {
    const list = ref(null)
    const {updateEdgeRoll} = useEdgeRoll(list)
    return {list, updateEdgeRoll}
  },
  template: `
    <div ref="list">
      <div v-for="index in 3" :key="index">Item {{ index }}</div>
    </div>
  `,
}

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

describe('useEdgeRoll', () => {
  it('rolls partially clipped variable-height rows and clears them when fully visible', () => {
    const wrapper = mount(EdgeRollHarness)
    const list = wrapper.element
    setListGeometry(list, 30, 90, [
      {top: 0, height: 50},
      {top: 51, height: 80},
      {top: 132, height: 40},
    ])

    wrapper.vm.updateEdgeRoll()

    expect(list.children[0].classList.contains('rollingTop')).toBe(true)
    expect(list.children[1].classList.contains('rollingBottom')).toBe(true)

    setListGeometry(list, 0, 200, [
      {top: 0, height: 50},
      {top: 51, height: 80},
      {top: 132, height: 40},
    ])
    wrapper.vm.updateEdgeRoll()

    expect(list.querySelector('.rollingTop, .rollingBottom')).toBeNull()
    wrapper.unmount()
  })
})
