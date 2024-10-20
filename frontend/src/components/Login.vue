<script setup>

</script>
<script>
import {backend_fetch} from "@/utils";
import {app_state} from "@/main";

export default {
  name: "login",
  props: ["onLoggedIn"],
  data() {
    return {
      username: "",
      password: "",
    }
  },
  methods: {
    async login(){
      const requestOptions = {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({user: this.username, password: this.password})
      }
      const token = await backend_fetch("/authenticate", requestOptions)
      if (token) {
        app_state.set_token(token)
        this.onLoggedIn(token)
      }
    }
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