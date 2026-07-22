import {createRouter, createWebHistory} from 'vue-router'
import Values from '@/view/Values.vue'
import Value from '@/view/Value.vue'
import KeyResults from '@/view/KeyResults.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    {path: '/', name: 'values', component: Values},
    {
      path: '/value/:valueId',
      redirect: (to) => ({name: 'value', params: {valueId: to.params.valueId, tab: 'active'}}),
    },
    {path: '/value/:valueId/:tab', name: 'value', component: Value},
    {path: '/key-results', name: 'key-results', component: KeyResults},
  ],
})
