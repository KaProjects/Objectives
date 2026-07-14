<script setup>
import {ref} from 'vue'
import {api} from '@/services/apiClient'
import {setToken} from '@/state/appState'

const props = defineProps({
  onLoggedIn: Function,
})

const username = ref('')
const password = ref('')

async function login() {
  const token = await api.login(username.value, password.value)
  if (token) {
    setToken(token)
    sessionStorage.setItem('token', token)
    props.onLoggedIn(token)
  }
}
</script>
<template>
  <v-container fluid fill-height>
    <v-layout align-center justify-center>
      <v-flex xs12 sm8 md4>
        <v-card class="elevation-12" min-width="300px">
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

              <v-btn type="submit" class="mt-4" color="primary" value="log in">Login</v-btn>
            </form>
          </v-card-text>
        </v-card>

      </v-flex>
    </v-layout>
  </v-container>
</template>
<style scoped>

</style>
