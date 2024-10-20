import {createApp, reactive} from 'vue'
import App from './App.vue'


import './assets/main.css'
// Vuetify
import 'vuetify/styles'
import {createVuetify} from 'vuetify'
import {aliases, mdi} from 'vuetify/iconsets/mdi'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

export const app_state = reactive({
    token: null,
    set_token(token) {
        this.token = token
    },
    value: null,
    select_value(value) {
        this.value = value
    },
    unselect_value() {
        this.value = null
    },
    fetchErrorValue: null,
    handle_fetch_error(error) {
        console.error(error)
        this.fetchErrorValue = error
    }
})

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