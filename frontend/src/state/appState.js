import {reactive} from 'vue'

export const appState = reactive({
  authStatus: 'checking',
  error: null,
})

export function setAuthStatus(status) {
  appState.authStatus = status
}

export function setError(error) {
  if (error?.status === 401) {
    appState.error = null
    return
  }
  console.error(error)
  appState.error = error instanceof Error ? error.message : String(error)
}

export function clearError() {
  appState.error = null
}
