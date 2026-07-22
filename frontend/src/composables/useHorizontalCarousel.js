import {ref, unref, watch} from 'vue'

export function useHorizontalCarousel(itemCount) {
  const carousel = ref(null)
  const activeIndex = ref(0)

  function count() {
    return Math.max(0, Number(unref(itemCount)) || 0)
  }

  function updateActiveIndex() {
    const element = carousel.value
    if (!element || element.clientWidth === 0) return
    activeIndex.value = Math.min(
        Math.max(0, count() - 1),
        Math.max(0, Math.round(element.scrollLeft / element.clientWidth)),
    )
  }

  watch(() => count(), (nextCount) => {
    activeIndex.value = Math.min(activeIndex.value, Math.max(0, nextCount - 1))
  })

  return {activeIndex, carousel, updateActiveIndex}
}
