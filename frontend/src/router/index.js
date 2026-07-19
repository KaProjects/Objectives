import {createRouter, createWebHistory} from 'vue-router'
import Value from '@/view/Value.vue'
import KeyResults from '@/view/KeyResults.vue'

const ValuesListRoute = {template: '<div />'}

export default createRouter({
  history: createWebHistory(),
  routes: [
    {path: '/', name: 'values', component: ValuesListRoute},
    {path: '/values/:valueId', name: 'value', component: Value},
    {path: '/key-results', name: 'key-results', component: KeyResults},
  ],
})
