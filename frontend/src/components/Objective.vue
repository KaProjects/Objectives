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
                     class="kr" :class="key_result.state"
                     @click="openKeyResult(key_result, objective.state)">
        <v-list-item-content>

          <div class="krTitle">
            <v-list-item-title class="inLine">{{ key_result.name }}</v-list-item-title>
            <v-icon icon="mdi-check-bold"
                    v-if="key_result.state === KEY_RESULT_STATE.COMPLETED"/>
            <v-icon icon="mdi-close-thick"
                    v-if="key_result.state === KEY_RESULT_STATE.FAILED"/>
          </div>

          <div class="krInfo" v-if="key_result.state === KEY_RESULT_STATE.ACTIVE">
            <div class="krInfoChild" style="right: 0;">{{ formatDate(key_result.date_reviewed) }}</div>
            <div class="krInfoChild" style="left: 0;">
              {{ key_result.resolved_tasks_count }}/{{ key_result.all_tasks_count }}
            </div>
          </div>

        </v-list-item-content>
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

.kr:hover {
  border-width: 2px;
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

.inLine {
  flex: 1 1 auto;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.krTitle {
  align-items: center;
  display: flex;
  gap: 4px;
  min-width: 0;
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
  min-height: 0;
  overflow-y: auto;
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

.obj.failed > div > .kr {
  color: #262626;
}

.obj.achieved > div > .kr {
  color: #262626;
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

.krInfo {
  margin-top: 20px;
  margin-bottom: 10px;
  position: relative;
}

.krInfoChild {
  font-size: 10px;
  position: absolute;
  bottom: 0;
}
</style>
