<script setup>
import {ref} from 'vue'
import {api} from '@/services/apiClient'
import {setAuthStatus, setError} from '@/state/appState'

const emit = defineEmits(['logged-in'])

const username = ref('')
const password = ref('')
const isSubmitting = ref(false)
const authenticationError = ref(null)

async function login() {
  if (isSubmitting.value) return
  isSubmitting.value = true
  authenticationError.value = null
  try {
    await api.login(username.value, password.value)
    setAuthStatus('authenticated')
    emit('logged-in')
  } catch (error) {
    if (error?.status === 401) {
      authenticationError.value = 'Invalid username or password'
    } else {
      setError(error)
    }
  } finally {
    isSubmitting.value = false
  }
}
</script>
<template>
  <div class="loginPage">
    <v-card class="loginCard elevation-12">
      <v-card-text>
        <v-alert v-if="authenticationError" type="error" class="mb-4">
          {{ authenticationError }}
        </v-alert>
        <form ref="form" @submit.prevent="login()">
          <v-text-field
              v-model="username"
              name="username"
              label="Username"
              type="text"
              placeholder="username"
              required
          ></v-text-field>

          <v-text-field
              v-model="password"
              name="password"
              label="Password"
              type="password"
              placeholder="password"
              required
          ></v-text-field>

          <v-btn type="submit" :disabled="isSubmitting" class="mt-4 loginSubmit" color="primary" size="large" value="log in">
            Login
          </v-btn>
        </form>
      </v-card-text>
    </v-card>
  </div>
</template>
<style scoped>
.loginPage {
  display: grid;
  place-items: center;
  min-height: 50vh;
  padding: 16px;
}

.loginCard {
  width: min(100%, 400px);
}

.loginSubmit {
  display: flex;
  margin-inline: auto;
}
</style>
