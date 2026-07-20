<script setup>
import {computed, onMounted, ref} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {appState, setError, setToken} from '@/state/appState'
import Login from '@/components/Login.vue'
import {api} from '@/services/apiClient'

const values = ref([])
const route = useRoute()
const router = useRouter()
const isValuesList = computed(() => route.name === 'values')

async function loadData() {
  try {
    values.value = await api.get('/values')
  } catch (error) {
    setError(error)
  }
}

function addValue() {
  alert('add value')
}

function openValue(value) {
  router.push({name: 'value', params: {valueId: value.id}})
}

function openKeyResults() {
  router.push({name: 'key-results'})
}

onMounted(() => {
  const token = sessionStorage.getItem('token')
  if (token) {
    setToken(token)
    loadData()
  }
})
</script>

<template>

  <v-alert v-if="appState.error" title="Backend Error" type="error">
    {{ appState.error }}
  </v-alert>

  <div v-else>
    <Login v-if="appState.token == null" @logged-in="loadData"/>

    <div v-else>
      <div class="values0" v-if="isValuesList">
        <div class="values">
          <v-btn class="keyResultsButton" variant="tonal" rounded="lg" @click="openKeyResults">
            <v-icon icon="mdi-format-list-bulleted"/>
            Key Results
          </v-btn>

          <v-card class="value" elevation="20" outlined shaped

                  v-for="value in values"
                  :key="value.id"
                  @click.stop="openValue(value)">
            <v-card-text>
              <div class="valueHeader">
                <div class="valueName text-h4 text--primary">
                  {{ value.name }}
                </div>
                <div class="valueCounts">
                  <span>Active: {{ value.active_count }}</span>
                  <span>Achievements: {{ value.achievements_count }}</span>
                </div>
              </div>
              <div class="text--primary">
                {{ value.description }}
              </div>
            </v-card-text>
          </v-card>

          <v-card class="addValue" elevation="20" outlined shaped @click="addValue">
            <v-card-actions>
              <v-icon class="centerButton" icon="mdi-plus" large/>
            </v-card-actions>
          </v-card>

        </div>
      </div>

      <RouterView v-else/>

    </div>
  </div>
</template>
<style scoped>

.values {
  max-width: 600px;
  margin: 0 auto;
  padding: 2rem;
  font-weight: normal;
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 0.5rem;
}

.value,
.addValue {
  width: 100%;
  background-color: #b2d5f3;
}

.keyResultsButton {
  justify-self: end;
}

.value {
  color: #000000;
}

.value:hover {
  background-color: #96c6ef;
}

.valueHeader {
  align-items: center;
  display: flex;
  justify-content: space-between;
}

.valueCounts {
  display: flex;
  gap: 0.75rem;
}

.valueCounts span {
  white-space: nowrap;
}

.centerButton {
  margin-left: auto;
  margin-right: auto;
  height: 3em;
}

.addValue {
  background-color: #181818;
  color: #96c6ef;
}

.addValue:hover {
  background-color: #96c6ef;
  color: #181818;
}

@media (max-width: 600px) {
  .valueName {
    flex: 1 1 auto;
    min-width: 0;
    overflow-wrap: normal;
    word-break: normal;
  }

  .valueCounts {
    align-items: flex-end;
    background-color: inherit;
    flex: 0 0 auto;
    flex-direction: column;
    gap: 0;
    margin-left: auto;
    position: relative;
    z-index: 1;
  }
}

</style>
