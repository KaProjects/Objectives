import {describe, expect, it} from 'vitest'
import {mount} from '@vue/test-utils'
import CarouselPager from '@/components/CarouselPager.vue'

describe('CarouselPager', () => {
  it('announces the selected card while keeping visual dots decorative', () => {
    const wrapper = mount(CarouselPager, {
      props: {count: 3, activeIndex: 1, label: 'Objectives'},
    })

    expect(wrapper.get('[role="status"]').text()).toContain('Objectives: Card 2 of 3')
    expect(wrapper.findAll('.carouselPagerDot')).toHaveLength(3)
    expect(wrapper.findAll('.carouselPagerDot').every((dot) => dot.attributes('aria-hidden') === 'true')).toBe(true)
  })
})
