import {reactive} from 'vue'

export const appState = reactive({
  token: null,
  error: null,
})

export function setToken(token) {
  appState.token = token
}

export function setError(error) {
  console.error(error)
  appState.error = error instanceof Error ? error.message : String(error)
}

export function clearError() {
  appState.error = null
}
