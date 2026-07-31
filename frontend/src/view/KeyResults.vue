<script setup lang="ts">
import {onMounted, ref, watch} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {setError} from '@/state/appState'
import {api} from '@/services/apiClient'
import {formatDate, isDeadlineClose, isDueOrOverdue, parseIsoDate, sortKeyResultsByDeadline} from '@/utils'
import KeyResultDialog from '@/dialogs/KeyResultDialog.vue'
import {KEY_RESULT_STATE, TASK_STATE} from '@/constants/states'
import type {KeyResult, KeyResultOverview, KeyResultParent} from '@/types/domain'
import {
  DIALOG_QUERY_PARAM,
  parseDialogId,
  withDialogQuery,
  withoutDialogQuery,
} from '@/router/dialogQuery'

const keyResults = ref<KeyResultOverview[]>([])
const route = useRoute()
const router = useRouter()
const selectedKeyResult = ref<KeyResult | null>(null)
const selectedKeyResultParent = ref<KeyResultParent | null>(null)
const openKeyResultDialog = ref(false)
const keyResultsLoaded = ref(false)

async function loadKeyResults() {
  try {
    keyResults.value = sortKeyResultsByDeadline(await api.get<KeyResultOverview[]>('/key_result/overview'))
    keyResultsLoaded.value = true
    await syncKeyResultDialog()
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

async function openKeyResult(keyResult: KeyResultOverview, updateRoute = true) {
  try {
    const fullKeyResult = await api.get<KeyResult>('/key_result/' + keyResult.id)
    if (!updateRoute && parseDialogId(route.query[DIALOG_QUERY_PARAM.KEY_RESULT]) !== keyResult.id) return
    selectedKeyResult.value = fullKeyResult
    selectedKeyResultParent.value = {
      ...fullKeyResult,
      value_id: keyResult.value_id,
      obj_state: keyResult.objective_state,
      all_tasks_count: fullKeyResult.tasks.length,
      resolved_tasks_count: fullKeyResult.tasks.filter((task) => task.state !== TASK_STATE.ACTIVE).length,
    }
    openKeyResultDialog.value = true
    if (updateRoute) {
      await router.push({
        query: withDialogQuery(route.query, DIALOG_QUERY_PARAM.KEY_RESULT, keyResult.id),
      })
    }
  } catch (error) {
    setError(error)
  }
}

async function syncKeyResultDialog() {
  if (!keyResultsLoaded.value || route.name !== 'key-results') return
  const rawKeyResultId = route.query[DIALOG_QUERY_PARAM.KEY_RESULT]
  if (rawKeyResultId == null) {
    openKeyResultDialog.value = false
    return
  }

  const keyResultId = parseDialogId(rawKeyResultId)
  const keyResult = keyResults.value.find((item) => item.id === keyResultId)
  if (keyResultId == null || !keyResult) {
    await router.replace({
      query: withoutDialogQuery(route.query, DIALOG_QUERY_PARAM.KEY_RESULT),
    })
    return
  }
  if (openKeyResultDialog.value && selectedKeyResult.value?.id === keyResultId) return
  await openKeyResult(keyResult, false)
}

async function setKeyResultDialogOpen(open: boolean) {
  openKeyResultDialog.value = open
  if (open) return
  const routeKeyResultId = parseDialogId(route.query[DIALOG_QUERY_PARAM.KEY_RESULT])
  if (routeKeyResultId !== selectedKeyResult.value?.id) return
  await router.replace({
    query: withoutDialogQuery(route.query, DIALOG_QUERY_PARAM.KEY_RESULT),
  })
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

function locateObjective({valueId, objectiveId}: {valueId: number; objectiveId: number}) {
  if (valueId == null || objectiveId == null) return
  router.push({
    name: 'value',
    params: {valueId, tab: 'active'},
    query: {objective: String(objectiveId)},
  })
}

watch(() => route.query[DIALOG_QUERY_PARAM.KEY_RESULT], syncKeyResultDialog)
onMounted(loadKeyResults)
</script>

<template>
  <main class="keyResultsPage">
    <header class="appbar">
      <v-btn class="backButton" variant="tonal" rounded="lg" aria-label="Back to Values" @click="returnToValues">
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
              role="button"
              tabindex="0"
              :aria-label="`Open Key Result ${keyResult.name}`"
              @click="openKeyResult(keyResult)"
              @keydown.enter.prevent="openKeyResult(keyResult)"
              @keydown.space.prevent="openKeyResult(keyResult)">
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
                     :model-value="openKeyResultDialog"
                     @update:model-value="setKeyResultDialogOpen"
                     :kr="selectedKeyResult"
                     :kr_parent="selectedKeyResultParent"
                     show-locate-objective
                     @updated="updateKeyResult"
                     @deleted="removeKeyResult"
                     @locate-objective="locateObjective"/>
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
