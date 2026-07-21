import {nextTick, onBeforeUnmount, onMounted} from 'vue'

export function useEdgeRoll(resolveList) {
  let resizeObserver
  let observedList = null
  let animationFrame = null
  let rollingTopItem = null
  let rollingBottomItem = null

  function listElement() {
    const target = typeof resolveList === 'function' ? resolveList() : resolveList.value
    return target?.$el ?? target ?? null
  }

  function clearRollingItem(item, className) {
    if (!item) return
    item.classList.remove(className)
    item.style.removeProperty('--roll-angle')
  }

  function clearRoll() {
    clearRollingItem(rollingTopItem, 'rollingTop')
    clearRollingItem(rollingBottomItem, 'rollingBottom')
    rollingTopItem = null
    rollingBottomItem = null
  }

  function setRollingItem(item, className, angle) {
    item.classList.add(className)
    item.style.setProperty('--roll-angle', `${angle}deg`)
  }

  function observeCurrentList() {
    const list = listElement()
    if (!resizeObserver || list === observedList) return list
    if (observedList) resizeObserver.unobserve(observedList)
    observedList = list
    if (observedList) resizeObserver.observe(observedList)
    return list
  }

  function updateEdgeRoll() {
    const list = observeCurrentList() ?? listElement()
    clearRoll()
    if (!list) return

    const viewportTop = list.scrollTop
    const viewportBottom = viewportTop + list.clientHeight

    for (const item of list.children) {
      const itemHeight = item.offsetHeight
      if (itemHeight <= 0) continue

      const itemTop = item.offsetTop
      const itemBottom = itemTop + itemHeight

      if (!rollingTopItem && itemTop < viewportTop && itemBottom > viewportTop) {
        const progress = Math.min((viewportTop - itemTop) / itemHeight, 1)
        rollingTopItem = item
        setRollingItem(item, 'rollingTop', progress * 68)
      }

      if (itemTop < viewportBottom && itemBottom > viewportBottom) {
        const visiblePart = viewportBottom - itemTop
        const progress = 1 - Math.min(Math.max(visiblePart / itemHeight, 0), 1)
        if (item !== rollingTopItem) {
          rollingBottomItem = item
          setRollingItem(item, 'rollingBottom', progress * -68)
        }
        break
      }

      if (itemTop >= viewportBottom) break
    }
  }

  function scheduleEdgeRoll() {
    observeCurrentList()
    if (animationFrame !== null) return
    if (typeof requestAnimationFrame === 'undefined') {
      updateEdgeRoll()
      return
    }
    animationFrame = requestAnimationFrame(() => {
      animationFrame = null
      updateEdgeRoll()
    })
  }

  onMounted(() => {
    if (typeof ResizeObserver !== 'undefined') {
      resizeObserver = new ResizeObserver(scheduleEdgeRoll)
    }
    nextTick(() => {
      observeCurrentList()
      updateEdgeRoll()
    })
  })

  onBeforeUnmount(() => {
    resizeObserver?.disconnect()
    if (animationFrame !== null) cancelAnimationFrame(animationFrame)
    clearRoll()
  })

  return {scheduleEdgeRoll, updateEdgeRoll}
}
