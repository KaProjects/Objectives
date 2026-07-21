import {onBeforeUnmount, onMounted} from 'vue'

let consumerCount = 0
let pointerClickPending = false
const deferredCallbacks = new Set()

function handlePointerDown() {
  pointerClickPending = true
}

function handleWindowClick() {
  pointerClickPending = false
  const callbacks = [...deferredCallbacks]
  deferredCallbacks.clear()
  callbacks.forEach((callback) => callback())
}

function installListeners() {
  window.addEventListener('pointerdown', handlePointerDown, true)
  window.addEventListener('click', handleWindowClick)
}

function removeListeners() {
  window.removeEventListener('pointerdown', handlePointerDown, true)
  window.removeEventListener('click', handleWindowClick)
  pointerClickPending = false
  deferredCallbacks.clear()
}

export function useClickCompletion() {
  let deferredCallback = null

  function cancelDeferredClick() {
    if (!deferredCallback) return
    deferredCallbacks.delete(deferredCallback)
    deferredCallback = null
  }

  function deferUntilClick(callback) {
    if (!pointerClickPending) return false
    cancelDeferredClick()
    deferredCallback = () => {
      deferredCallback = null
      callback()
    }
    deferredCallbacks.add(deferredCallback)
    return true
  }

  onMounted(() => {
    consumerCount += 1
    if (consumerCount === 1) installListeners()
  })

  onBeforeUnmount(() => {
    cancelDeferredClick()
    consumerCount -= 1
    if (consumerCount === 0) removeListeners()
  })

  return {cancelDeferredClick, deferUntilClick}
}
