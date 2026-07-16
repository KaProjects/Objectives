import {createApp} from 'vue'
import App from './App.vue'
import router from './router'


import './assets/main.css'
// Vuetify
import 'vuetify/styles'
import {createVuetify} from 'vuetify'
import {aliases, mdi} from 'vuetify/iconsets/mdi'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

const systemTheme = window.matchMedia('(prefers-color-scheme: dark)')
const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: systemTheme.matches ? 'dark' : 'light',
  },
  icons: {
    defaultSet: 'mdi',
    aliases,
    sets: {
      mdi,
    }
  },
})

systemTheme.addEventListener('change', (event) => {
  vuetify.theme.global.name.value = event.matches ? 'dark' : 'light'
})

createApp(App).use(vuetify).use(router).mount('#app')
