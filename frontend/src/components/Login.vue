<script setup>
import {ref} from 'vue'
import {api} from '@/services/apiClient'
import {setError, setToken} from '@/state/appState'

const emit = defineEmits(['logged-in'])

const username = ref('')
const password = ref('')
const isSubmitting = ref(false)

async function login() {
  if (isSubmitting.value) return
  isSubmitting.value = true
  try {
    const token = await api.login(username.value, password.value)
    setToken(token)
    sessionStorage.setItem('token', token)
    emit('logged-in', token)
  } catch (error) {
    setError(error)
  } finally {
    isSubmitting.value = false
  }
}
</script>
<template>
  <div class="loginPage">
    <v-card class="loginCard elevation-12">
      <v-card-text>
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

          <v-btn type="submit" :disabled="isSubmitting" class="mt-4" color="primary" value="log in">
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
</style>
