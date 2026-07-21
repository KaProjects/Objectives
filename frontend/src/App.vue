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
  router.push({name: 'value', params: {valueId: value.id, tab: 'active'}})
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
        <header class="valuesAppbar">
          <v-btn class="addValueButton" variant="tonal" rounded="lg" aria-label="Add Value" @click="addValue">
            <v-icon icon="mdi-plus"/>
          </v-btn>
          <v-btn class="keyResultsButton" variant="tonal" rounded="lg" @click="openKeyResults">
            <v-icon icon="mdi-format-list-bulleted"/>
            Key Results
          </v-btn>
        </header>

        <div class="values">
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

        </div>
      </div>

      <RouterView v-else/>

    </div>
  </div>
</template>
<style scoped>

.valuesAppbar {
  align-items: center;
  background: rgb(var(--v-theme-surface));
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  box-shadow: 0 1px 3px rgba(16, 24, 40, 0.12);
  display: flex;
  justify-content: flex-end;
  min-height: 56px;
  padding: 6px 12px;
  position: sticky;
  top: 0;
  z-index: 10;
}

.values {
  max-width: 600px;
  margin: 0 auto;
  padding: 0.5rem 2rem 2rem;
  font-weight: normal;
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 0.25rem;
}

.keyResultsButton {
  margin-left: auto;
}

.addValueButton {
  height: 40px;
  min-width: 40px;
  padding: 0;
  width: 40px;
}

.value {
  background: linear-gradient(135deg, #c2ddf3 0%, #a9cfee 100%);
  border: 1px solid #7899ae;
  border-radius: 12px !important;
  color: #000000;
  overflow: hidden;
  width: 100%;
}

.value:hover {
  background: linear-gradient(135deg, #b7d7f0 0%, #96c6ef 100%);
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

@media (max-width: 600px) {
  .valuesAppbar {
    min-height: 48px;
    padding: 4px 8px;
  }

  .values {
    padding-left: 0.5rem;
    padding-right: 0.5rem;
  }

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
