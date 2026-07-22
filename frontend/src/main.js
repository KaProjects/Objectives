import {createApp} from 'vue'
import App from './App.vue'
import router from './router'


import './assets/main.css'
// Vuetify
import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import {createVuetify} from 'vuetify'
import {aliases, mdi} from 'vuetify/iconsets/mdi'
import {
  VAlert,
  VBtn,
  VCard,
  VCardActions,
  VCardSubtitle,
  VCardText,
  VCardTitle,
  VCheckbox,
  VDialog,
  VDivider,
  VIcon,
  VList,
  VListItem,
  VListItemTitle,
  VMenu,
  VTab,
  VTabs,
  VTextField,
  VTextarea,
} from 'vuetify/components'

const components = {
  VAlert,
  VBtn,
  VCard,
  VCardActions,
  VCardSubtitle,
  VCardText,
  VCardTitle,
  VCheckbox,
  VDialog,
  VDivider,
  VIcon,
  VList,
  VListItem,
  VListItemTitle,
  VMenu,
  VTab,
  VTabs,
  VTextField,
  VTextarea,
}

const systemTheme = window.matchMedia('(prefers-color-scheme: dark)')
const vuetify = createVuetify({
  components,
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
