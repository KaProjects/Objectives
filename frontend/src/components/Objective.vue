<script setup>
import {nextTick, onBeforeUnmount, onMounted, ref, watch} from 'vue'
import {compareDates, formatDate, string_to_html} from '@/utils'
import {api} from '@/services/apiClient'
import {setError} from '@/state/appState'
import KeyResultDialog from '@/dialogs/KeyResultDialog.vue'
import ObjectiveDialog from '@/dialogs/ObjectiveDialog.vue'
import {KEY_RESULT_STATE, OBJECTIVE_STATE} from '@/constants/states'
import AddKeyResultDialog from '@/dialogs/AddKeyResultDialog.vue'
import achievementStamp from '@/assets/achievement-stamp.png'
import failStamp from '@/assets/fail-stamp.png'

const props = defineProps({
  objective: {type: Object, required: true},
})
const emit = defineEmits(['deleted', 'state-changed', 'updated', 'key-result-created', 'key-result-updated', 'key-result-deleted'])

const objective = props.objective
const openObjDialog = ref(false)
const openAddKrDialog = ref(false)
const selectedKr = ref(null)
const selectedKr_parent = ref(null)
const selectedObj = ref(null)
const openKrDialog = ref(false)
const isSubmitting = ref(false)
const submissionError = ref(null)
const keyResultsList = ref(null)
const showKeyResultsTopFade = ref(false)
const showKeyResultsBottomFade = ref(false)
let keyResultsResizeObserver

const keyResultStatus = Object.freeze({
  [KEY_RESULT_STATE.ACTIVE]: {label: 'Active', icon: 'mdi-progress-clock'},
  [KEY_RESULT_STATE.COMPLETED]: {label: 'Completed', icon: 'mdi-check-bold'},
  [KEY_RESULT_STATE.FAILED]: {label: 'Failed', icon: 'mdi-close-thick'},
})

function updateKeyResultsFades() {
  const list = keyResultsList.value
  if (!list) return

  showKeyResultsTopFade.value = list.scrollTop > 1
  showKeyResultsBottomFade.value = list.scrollTop + list.clientHeight < list.scrollHeight - 1
}

onMounted(() => {
  nextTick(updateKeyResultsFades)
  if (typeof ResizeObserver === 'undefined' || !keyResultsList.value) return
  keyResultsResizeObserver = new ResizeObserver(updateKeyResultsFades)
  keyResultsResizeObserver.observe(keyResultsList.value)
})

onBeforeUnmount(() => keyResultsResizeObserver?.disconnect())

watch(() => props.objective.key_results.length, () => nextTick(updateKeyResultsFades))

function compareKeyResults(a, b) {
  const activeComparison = Number(b.state === KEY_RESULT_STATE.ACTIVE) - Number(a.state === KEY_RESULT_STATE.ACTIVE)
  if (activeComparison !== 0) return activeComparison

  const reviewedComparison = -compareDates(a.date_reviewed || '', b.date_reviewed || '')
  if (reviewedComparison !== 0) return reviewedComparison

  const createdComparison = -compareDates(a.date_created || '', b.date_created || '')
  return createdComparison !== 0 ? createdComparison : b.id - a.id
}

async function openKeyResult(keyResult, objectiveState) {
  try {
    selectedKr.value = await api.get('/key_result/' + keyResult.id)
    selectedKr_parent.value = {...keyResult, obj_state: objectiveState}
    openKrDialog.value = true
  } catch (error) {
    setError(error)
  }
}

function openObjective() {
  selectedObj.value = objective
  openObjDialog.value = true
}

async function deleteKeyResult(keyResult) {
  if (isSubmitting.value) return
  isSubmitting.value = true
  submissionError.value = null
  try {
    await api.delete('/key_result/' + keyResult.id)
    emit('key-result-deleted', {objectiveId: objective.id, keyResultId: keyResult.id})
  } catch (error) {
    submissionError.value = error.message
  } finally {
    isSubmitting.value = false
  }
}
</script>
<template>
  <v-card class="obj" :class="objective.state" width="300" elevation="3" shaped :key="objective.id">
    <ObjectiveDialog :obj="selectedObj" v-model="openObjDialog" @close="openObjDialog = false"
                     @deleted="emit('deleted', $event)" @updated="emit('updated', $event)"
                     @state-changed="emit('state-changed', $event)"
                     @key-result-created="emit('key-result-created', {objectiveId: objective.id, keyResult: $event})"/>
    <KeyResultDialog :kr="selectedKr" :kr_parent="selectedKr_parent" v-model="openKrDialog"
                     @close="openKrDialog = false"
                     @updated="emit('key-result-updated', {objectiveId: objective.id, keyResult: $event})"
                     @deleted="deleteKeyResult"/>

    <v-card-title>{{ objective.name }}</v-card-title>
    <v-card-text v-html="string_to_html(objective.description)"/>

    <img v-if="objective.state === OBJECTIVE_STATE.ACHIEVED"
         :src="achievementStamp"
         alt="Achievement"
         class="achievementStamp">
    <img v-else-if="objective.state === OBJECTIVE_STATE.FAILED"
         :src="failStamp"
         alt="Fail"
         class="failureStamp">

    <v-icon class="objEdit" icon="mdi-pencil-circle-outline" large @click="openObjective()"/>

    <div class="objIdeas" v-if="objective.state === OBJECTIVE_STATE.ACTIVE && objective.ideas_count > 0">
      <v-icon icon="mdi-lightbulb-variant-outline" size="15" style="margin: 0 auto;"/>
      <div style="margin: -5px auto;">{{ objective.ideas_count }}</div>
    </div>

    <div class="keyResultsListWrapper"
         :class="{hasKeyResultsAbove: showKeyResultsTopFade, hasKeyResultsBelow: showKeyResultsBottomFade}">
      <div ref="keyResultsList" class="keyResultsList" @scroll="updateKeyResultsFades">
        <v-list-item v-for="key_result in objective.key_results.slice().sort(compareKeyResults)"
                     :key="key_result.id"
                     class="kr"
                     :class="[key_result.state, {krPlaque: objective.state === OBJECTIVE_STATE.ACTIVE}]"
                     @click="openKeyResult(key_result, objective.state)">
          <div v-if="objective.state === OBJECTIVE_STATE.ACTIVE" class="krLayout">
            <div class="krStatusMark" aria-hidden="true">
              <v-icon :icon="keyResultStatus[key_result.state].icon"/>
            </div>

            <div class="krContent">
              <div class="krHeader">
                <v-list-item-title class="krName">{{ key_result.name }}</v-list-item-title>
                <span v-if="key_result.state !== KEY_RESULT_STATE.ACTIVE" class="krStateLabel">
                  {{ keyResultStatus[key_result.state].label }}
                </span>
              </div>

              <div v-if="key_result.state === KEY_RESULT_STATE.ACTIVE" class="krMeta">
                <span class="krMetaItem">
                  <v-icon icon="mdi-checkbox-marked-circle-outline" size="12"/>
                  {{ key_result.resolved_tasks_count ?? 0 }}/{{ key_result.all_tasks_count ?? 0 }}
                </span>
                <span class="krMetaItem">
                  <v-icon icon="mdi-calendar-clock-outline" size="12"/>
                  {{ formatDate(key_result.date_reviewed) }}
                </span>
              </div>
            </div>
          </div>

          <div v-else class="standardKrContent">
            <v-list-item-title class="standardKrName">{{ key_result.name }}</v-list-item-title>
            <v-icon v-if="key_result.state === KEY_RESULT_STATE.COMPLETED" icon="mdi-check-bold"/>
            <v-icon v-else-if="key_result.state === KEY_RESULT_STATE.FAILED" icon="mdi-close-thick"/>
          </div>
        </v-list-item>
      </div>
    </div>

    <v-card-actions v-if="objective.state === OBJECTIVE_STATE.ACTIVE">
      <AddKeyResultDialog
          v-model="openAddKrDialog"
          :objective-id="objective.id"
          @created="emit('key-result-created', {objectiveId: objective.id, keyResult: $event})"
      />

    </v-card-actions>
  </v-card>
</template>
<style scoped>
.kr {
  border: 1px solid #2c3e50;
  flex: 0 0 auto;
  height: 60px;
  min-height: 60px;
}

.kr.completed {
  color: #017901;
}

.kr.failed {
  color: #ab0000;
}

.kr.active {
  color: #000000;
}

.kr:not(.krPlaque):hover {
  border-width: 2px;
}

.krPlaque {
  --kr-dark: #245c82;
  --kr-light: #3c82aa;
  align-items: center;
  background: linear-gradient(105deg, var(--kr-dark), var(--kr-light));
  border: 1px solid rgba(255, 255, 255, 0.24);
  border-radius: 9px;
  box-shadow:
    0 2px 4px rgba(16, 24, 40, 0.32),
    inset 0 1px 0 rgba(255, 255, 255, 0.24),
    inset 0 -2px 0 rgba(0, 0, 0, 0.2);
  color: #ffffff;
  cursor: pointer;
  flex: 0 0 auto;
  height: 60px;
  min-height: 60px;
  overflow: hidden;
  padding: 0 9px;
  transition: filter 120ms ease, transform 120ms ease;
}

.krPlaque :deep(.v-list-item__content) {
  height: 100%;
  min-width: 0;
}

.krLayout {
  align-items: center;
  display: flex;
  gap: 9px;
  height: 100%;
  min-width: 0;
  width: 100%;
}

.krPlaque:hover {
  filter: brightness(1.08);
  transform: translateY(-1px);
}

.krPlaque:active {
  filter: brightness(0.96);
  transform: translateY(0);
}

.krPlaque.active {
  color: #ffffff;
  --kr-dark: #245c82;
  --kr-light: #3c82aa;
}

.krPlaque.completed {
  color: #ffffff;
  --kr-dark: #176b49;
  --kr-light: #269566;
}

.krPlaque.failed {
  color: #ffffff;
  --kr-dark: #8f2539;
  --kr-light: #c34259;
}

.krStatusMark {
  align-items: center;
  border: 2px solid rgba(255, 255, 255, 0.94);
  border-radius: 50%;
  box-shadow:
    0 1px 2px rgba(0, 0, 0, 0.28),
    0 0 0 2px rgba(255, 255, 255, 0.1);
  display: flex;
  flex: 0 0 31px;
  height: 31px;
  justify-content: center;
  width: 31px;
}

.krStatusMark :deep(.v-icon) {
  font-size: 19px;
  text-shadow: 0 1px 1px rgba(0, 0, 0, 0.25);
}

.krContent {
  display: flex;
  flex: 1 1 auto;
  flex-direction: column;
  justify-content: center;
  min-width: 0;
  padding: 0;
}

.krHeader {
  align-items: center;
  display: flex;
  gap: 6px;
  min-width: 0;
}

.krName {
  color: inherit;
  flex: 1 1 auto;
  font-size: 0.84rem;
  font-weight: 650;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.krStateLabel {
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.36);
  border-radius: 999px;
  flex: 0 0 auto;
  font-size: 0.54rem;
  font-weight: 800;
  letter-spacing: 0.07em;
  line-height: 1;
  padding: 4px 5px 3px;
  text-transform: uppercase;
}

.krMeta {
  align-items: center;
  display: flex;
  font-size: 0.62rem;
  justify-content: space-between;
  margin-top: 4px;
  opacity: 0.9;
}

.krMetaItem {
  align-items: center;
  display: inline-flex;
  gap: 3px;
}

.standardKrContent {
  align-items: center;
  display: flex;
  gap: 4px;
  min-width: 0;
}

.standardKrName {
  flex: 1 1 auto;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.obj {
  display: flex;
  flex-direction: column;
  max-height: calc(100dvh - 90px);
  min-width: 300px;
  position: relative;
  vertical-align: top;
  margin-bottom: auto;
  margin-left: 1px;
  color: #000000;
}

.keyResultsList {
  display: flex;
  flex: 1 1 auto;
  flex-direction: column;
  gap: 1px;
  min-height: 0;
  overflow-y: auto;
  padding: 2px;
}

.keyResultsListWrapper {
  display: flex;
  flex: 1 1 auto;
  flex-direction: column;
  min-height: 0;
  position: relative;
}

.keyResultsListWrapper::before,
.keyResultsListWrapper::after {
  content: '';
  height: 24px;
  left: 0;
  opacity: 0;
  pointer-events: none;
  position: absolute;
  right: 0;
  transition: opacity 120ms ease;
  z-index: 1;
}

.keyResultsListWrapper::before {
  background: linear-gradient(to bottom, var(--key-results-fade), transparent);
  top: 0;
}

.keyResultsListWrapper::after {
  background: linear-gradient(to top, var(--key-results-fade), transparent);
  bottom: 0;
}

.keyResultsListWrapper.hasKeyResultsAbove::before,
.keyResultsListWrapper.hasKeyResultsBelow::after {
  opacity: 1;
}

.obj.active {
  --key-results-fade: #dce8f1;
  background: #dce8f1;
  border-left: 4px solid #5f88a6;
}

.obj.failed {
  --key-results-fade: #f2e1e1;
  background: #f2e1e1;
  border-left: 4px solid #ad5757;
}

.obj.achieved {
  --key-results-fade: #e0eddf;
  background: #e0eddf;
  border-left: 4px solid #5f8c61;
}

.objectiveStamp {
  align-items: center;
  border: 3px double currentColor;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  font-size: 0.7rem;
  font-weight: 700;
  height: 108px;
  justify-content: center;
  letter-spacing: 0.08em;
  line-height: 1.05;
  opacity: 0.55;
  pointer-events: none;
  position: absolute;
  right: 12px;
  text-align: center;
  text-transform: uppercase;
  transform: rotate(-12deg);
  top: 12px;
  width: 108px;
}

.objectiveStamp.achieved {
  color: #337a38;
}

.achievementStamp {
  height: 76px;
  object-fit: contain;
  opacity: 0.72;
  pointer-events: none;
  position: absolute;
  right: 8px;
  top: 6px;
  transform: rotate(-6deg);
  width: 87px;
}

.failureStamp {
  height: 44px;
  object-fit: contain;
  opacity: 0.72;
  pointer-events: none;
  position: absolute;
  right: 4px;
  top: 14px;
  transform: rotate(8deg);
  width: 110px;
}

.objectiveStamp.failed {
  color: #a33f3f;
  transform: rotate(10deg);
}

.objEdit {
  display: none;
  position: absolute;
  right: 0;
  top: 0;
  z-index: 1;
}

.obj:hover .objEdit {
  display: block;
}

.objIdeas {
  display: grid;
  position: absolute;
  right: 5px;
  top: 30px;
}

@media (max-width: 600px) {
  .objEdit {
    display: block;
  }
}

@media (prefers-reduced-motion: reduce) {
  .krPlaque {
    transition: none;
  }

  .krPlaque:hover {
    transform: none;
  }
}
</style>
