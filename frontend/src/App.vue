<script setup>
import {onMounted} from 'vue'
import {appState, setToken} from '@/state/appState'
import Login from '@/components/Login.vue'

onMounted(() => {
  const token = sessionStorage.getItem('token')
  if (token) {
    setToken(token)
  }
})
</script>

<template>

  <v-alert v-if="appState.error" title="Backend Error" type="error">
    {{ appState.error }}
  </v-alert>

  <div v-else>
    <Login v-if="appState.token == null"/>
    <RouterView v-else/>
  </div>
</template>
