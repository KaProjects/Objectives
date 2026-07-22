<script setup>
import {onMounted} from 'vue'
import {api} from '@/services/apiClient'
import {appState, setAuthStatus, setError} from '@/state/appState'
import Login from '@/components/Login.vue'

onMounted(async () => {
  try {
    await api.checkAuthentication()
    setAuthStatus('authenticated')
  } catch (error) {
    setAuthStatus('anonymous')
    if (error?.status !== 401) {
      setError(error)
    }
  }
})
</script>

<template>

  <v-alert v-if="appState.error" title="Backend Error" type="error">
    {{ appState.error }}
  </v-alert>

  <div v-else>
    <Login v-if="appState.authStatus === 'anonymous'"/>
    <RouterView v-else-if="appState.authStatus === 'authenticated'"/>
  </div>
</template>
