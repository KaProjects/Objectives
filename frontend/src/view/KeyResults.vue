<script setup lang="ts">
import {onMounted, ref} from 'vue'
import {useRouter} from 'vue-router'
import {setError} from '@/state/appState'
import {api} from '@/services/apiClient'
import {formatDate, isDeadlineClose, isDueOrOverdue, parseIsoDate, sortKeyResultsByDeadline} from '@/utils'
import KeyResultDialog from '@/dialogs/KeyResultDialog.vue'
import {KEY_RESULT_STATE, TASK_STATE} from '@/constants/states'
import type {KeyResult, KeyResultOverview, KeyResultParent} from '@/types/domain'

const keyResults = ref<KeyResultOverview[]>([])
const router = useRouter()
const selectedKeyResult = ref<KeyResult | null>(null)
const selectedKeyResultParent = ref<KeyResultParent | null>(null)
const openKeyResultDialog = ref(false)

async function loadKeyResults() {
  try {
    keyResults.value = sortKeyResultsByDeadline(await api.get<KeyResultOverview[]>('/key_result/overview'))
  } catch (error) {
    setError(error)
  }
}

function deadline(keyResult: KeyResultOverview) {
  return parseIsoDate(keyResult.t)
}

function deadlineNeedsAttention(keyResult: KeyResultOverview) {
  return isDueOrOverdue(keyResult.t)
}

function deadlineIsClose(keyResult: KeyResultOverview) {
  return isDeadlineClose(keyResult.t)
}

function deadlineIsMissing(keyResult: KeyResultOverview) {
  return deadline(keyResult) === null
}

async function openKeyResult(keyResult: KeyResultOverview) {
  try {
    const fullKeyResult = await api.get<KeyResult>('/key_result/' + keyResult.id)
    selectedKeyResult.value = fullKeyResult
    selectedKeyResultParent.value = {
      ...keyResult,
      state: fullKeyResult.state,
      obj_state: keyResult.objective_state,
      all_tasks_count: fullKeyResult.tasks.length,
      resolved_tasks_count: fullKeyResult.tasks.filter((task) => task.state !== TASK_STATE.ACTIVE).length,
    }
    openKeyResultDialog.value = true
  } catch (error) {
    setError(error)
  }
}

function updateKeyResult(updatedKeyResult: KeyResultParent) {
  const keyResult = keyResults.value.find((item) => item.id === updatedKeyResult.id)
  if (!keyResult) return
  if (updatedKeyResult.state === KEY_RESULT_STATE.COMPLETED || updatedKeyResult.state === KEY_RESULT_STATE.FAILED) {
    keyResults.value = keyResults.value.filter((item) => item.id !== updatedKeyResult.id)
    openKeyResultDialog.value = false
    return
  }
  Object.assign(keyResult, updatedKeyResult)
  keyResults.value = sortKeyResultsByDeadline(keyResults.value)
}

function removeKeyResult(keyResult: KeyResultParent) {
  keyResults.value = keyResults.value.filter((item) => item.id !== keyResult.id)
  openKeyResultDialog.value = false
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
      <h1>Active KRs Overview</h1>
    </header>

    <section class="keyResultsList">
      <v-card v-for="keyResult in keyResults"
              :key="keyResult.id"
              :class="{
                'keyResultCard--due': deadlineNeedsAttention(keyResult) || deadlineIsMissing(keyResult),
                'keyResultCard--close': deadlineIsClose(keyResult),
              }"
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
          <v-icon v-else-if="deadlineIsMissing(keyResult)"
                  class="deadlineAlert"
                  color="error"
                  icon="mdi-alert-circle"
                  aria-label="Deadline is not set"/>
          <v-icon v-else-if="deadlineIsClose(keyResult)"
                  class="deadlineAlert"
                  color="warning"
                  icon="mdi-alert-outline"
                  aria-label="Deadline is within four weeks"/>
        </div>
        <v-card-subtitle>{{ keyResult.value_name }} / {{ keyResult.objective_name }}</v-card-subtitle>
        <v-card-text>
          <span :class="{'missingDeadline': deadlineIsMissing(keyResult)}">
            Deadline: {{ deadline(keyResult) ? formatDate(deadline(keyResult)) : 'Not set' }}
          </span>
        </v-card-text>
      </v-card>

      <p v-if="keyResults.length === 0" class="emptyState">No Key Results yet.</p>
    </section>

    <KeyResultDialog v-if="selectedKeyResult && selectedKeyResultParent"
                     v-model="openKeyResultDialog"
                     :kr="selectedKeyResult"
                     :kr_parent="selectedKeyResultParent"
                     @updated="updateKeyResult"
                     @deleted="removeKeyResult"/>
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

.keyResultCard--close {
  background-color: rgba(var(--v-theme-warning), 0.08);
  border: 1px solid rgba(var(--v-theme-warning), 0.5);
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

.missingDeadline {
  color: rgb(var(--v-theme-error));
  font-weight: 600;
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
