<script setup>
import {onMounted, ref} from 'vue'
import {useRouter} from 'vue-router'
import {setError} from '@/state/appState'
import {api} from '@/services/apiClient'
import {formatDate, isDueOrOverdue, parseIsoDate, sortKeyResultsByDeadline} from '@/utils'
import KeyResultDialog from '@/dialogs/KeyResultDialog.vue'
import {KEY_RESULT_STATE} from '@/constants/states'

const keyResults = ref([])
const router = useRouter()
const selectedKeyResult = ref(null)
const selectedKeyResultParent = ref(null)
const openKeyResultDialog = ref(false)

async function loadKeyResults() {
  try {
    keyResults.value = sortKeyResultsByDeadline(await api.get('/key_result/overview'))
  } catch (error) {
    setError(error)
  }
}

function deadline(keyResult) {
  return parseIsoDate(keyResult.t)
}

function deadlineNeedsAttention(keyResult) {
  return isDueOrOverdue(keyResult.t)
}

async function openKeyResult(keyResult) {
  try {
    const fullKeyResult = await api.get('/key_result/' + keyResult.id)
    selectedKeyResult.value = fullKeyResult
    selectedKeyResultParent.value = {
      ...keyResult,
      obj_state: keyResult.objective_state,
      all_tasks_count: fullKeyResult.tasks.length,
      resolved_tasks_count: fullKeyResult.tasks.filter((task) => task.state !== 'active').length,
    }
    openKeyResultDialog.value = true
  } catch (error) {
    setError(error)
  }
}

function updateKeyResult(updatedKeyResult) {
  const keyResult = keyResults.value.find((item) => item.id === updatedKeyResult.id)
  if (!keyResult) return
  if (updatedKeyResult.state !== KEY_RESULT_STATE.ACTIVE) {
    keyResults.value = keyResults.value.filter((item) => item.id !== updatedKeyResult.id)
    openKeyResultDialog.value = false
    return
  }
  Object.assign(keyResult, updatedKeyResult)
}

async function deleteKeyResult(keyResult) {
  try {
    await api.delete('/key_result/' + keyResult.id)
    keyResults.value = keyResults.value.filter((item) => item.id !== keyResult.id)
    openKeyResultDialog.value = false
  } catch (error) {
    setError(error)
  }
}

function returnToValues() {
  router.push({name: 'values'})
}

onMounted(loadKeyResults)
</script>

<template>
  <main class="keyResultsPage">
    <header class="appbar">
      <v-btn class="backButton" variant="tonal" rounded="lg" @click="returnToValues">
        <v-icon icon="mdi-arrow-left"/>
      </v-btn>
      <h1>Active Key Results Overview</h1>
    </header>

    <section class="keyResultsList">
      <v-card v-for="keyResult in keyResults"
              :key="keyResult.id"
              :class="{'keyResultCard--due': deadlineNeedsAttention(keyResult)}"
              class="keyResultCard"
              elevation="6"
              @click="openKeyResult(keyResult)">
        <div class="cardHeader">
          <v-card-title>{{ keyResult.name }}</v-card-title>
          <v-icon v-if="deadlineNeedsAttention(keyResult)"
                  class="deadlineAlert"
                  color="error"
                  icon="mdi-alert-circle"
                  aria-label="Deadline is due or overdue"/>
        </div>
        <v-card-subtitle>{{ keyResult.value_name }} / {{ keyResult.objective_name }}</v-card-subtitle>
        <v-card-text>
          Deadline: {{ deadline(keyResult) ? formatDate(deadline(keyResult)) : 'Not set' }}
        </v-card-text>
      </v-card>

      <p v-if="keyResults.length === 0" class="emptyState">No Key Results yet.</p>
    </section>

    <KeyResultDialog v-if="selectedKeyResult"
                     v-model="openKeyResultDialog"
                     :kr="selectedKeyResult"
                     :kr_parent="selectedKeyResultParent"
                     @updated="updateKeyResult"
                     @deleted="deleteKeyResult"/>
  </main>
</template>

<style scoped>
.keyResultsPage {
  max-width: 700px;
  margin: 0 auto;
  padding: 1rem;
}

.appbar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.keyResultsList {
  display: grid;
  gap: 0.75rem;
}

.keyResultCard {
  color: rgb(var(--v-theme-on-surface));
}

.keyResultCard--due {
  background-color: rgba(var(--v-theme-error), 0.08);
  border: 1px solid rgba(var(--v-theme-error), 0.5);
}

.cardHeader {
  align-items: center;
  display: flex;
  justify-content: space-between;
}

.cardHeader :deep(.v-card-title) {
  flex: 1 1 auto;
  min-width: 0;
  overflow-wrap: anywhere;
}

.deadlineAlert {
  flex: 0 0 auto;
  font-size: 2rem;
  height: 2rem;
  margin-right: 1rem;
  width: 2rem;
}

.emptyState {
  color: rgb(var(--v-theme-on-surface-variant));
  text-align: center;
}

@media (max-width: 600px) {
  .backButton {
    display: none;
  }
}
</style>
