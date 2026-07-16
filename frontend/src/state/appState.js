import {reactive} from 'vue'

export const appState = reactive({
  token: null,
  selectedValue: null,
  error: null,
})

export function setToken(token) {
  appState.token = token
}

export function selectValue(value) {
  appState.selectedValue = value
}

export function unselectValue() {
  appState.selectedValue = null
}

export function setError(error) {
  console.error(error)
  appState.error = error instanceof Error ? error.message : String(error)
}

export function clearError() {
  appState.error = null
}
