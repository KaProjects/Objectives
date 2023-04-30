import {createApp, reactive} from 'vue'
import App from './App.vue'


import './assets/main.css'

export const app_state = reactive({
    value: null,
    select_value(value) {
        this.value = value
    },
    unselect_value() {
        this.value = null
    },
    krDialogToggle: false,
    objDialogToggle: false,
})

// Vuetify
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import { aliases, mdi } from 'vuetify/iconsets/mdi'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

const vuetify = createVuetify({
    components,
    directives,
    icons: {
        defaultSet: 'mdi',
        aliases,
        sets: {
            mdi,
        }
    },
})


createApp(App).use(vuetify).mount('#app')