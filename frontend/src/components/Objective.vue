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
let keyResultsResizeObserver
let keyResultsAnimationFrame = null
let rollingTopItem = null
let rollingBottomItem = null

const keyResultStatus = Object.freeze({
  [KEY_RESULT_STATE.ACTIVE]: {label: 'Active', icon: 'mdi-progress-clock'},
  [KEY_RESULT_STATE.COMPLETED]: {label: 'Completed', icon: 'mdi-check-bold'},
  [KEY_RESULT_STATE.FAILED]: {label: 'Failed', icon: 'mdi-close-thick'},
})

function clearRollingItem(item, className) {
  if (!item) return

  item.classList.remove(className)
  item.style.removeProperty('--roll-angle')
}

function setRollingItem(item, className, angle) {
  item.classList.add(className)
  item.style.setProperty('--roll-angle', `${angle}deg`)
}

function updateKeyResultsRoll() {
  const list = keyResultsList.value
  if (!list) return

  clearRollingItem(rollingTopItem, 'rollingTop')
  clearRollingItem(rollingBottomItem, 'rollingBottom')
  rollingTopItem = null
  rollingBottomItem = null

  const items = list.children
  if (items.length === 0) return

  const viewportTop = list.scrollTop
  const viewportBottom = viewportTop + list.clientHeight
  const firstItem = items[0]
  const itemHeight = firstItem.offsetHeight
  const contentTop = firstItem.offsetTop
  const itemPitch = items.length > 1 ? items[1].offsetTop - contentTop : itemHeight + 1
  if (itemHeight <= 0 || itemPitch <= 0) return

  const topIndex = Math.max(0, Math.min(items.length - 1, Math.floor((viewportTop - contentTop) / itemPitch)))
  const topItem = items[topIndex]
  const topItemTop = contentTop + topIndex * itemPitch
  const topProgress = Math.min(Math.max((viewportTop - topItemTop) / itemHeight, 0), 1)
  if (topProgress > 0) {
    rollingTopItem = topItem
    setRollingItem(topItem, 'rollingTop', topProgress * 68)
  }

  const bottomIndex = Math.max(0, Math.min(items.length - 1, Math.floor((viewportBottom - contentTop) / itemPitch)))
  const bottomItem = items[bottomIndex]
  const bottomItemTop = contentTop + bottomIndex * itemPitch
  const visibleBottomPart = viewportBottom - bottomItemTop
  const bottomProgress = 1 - Math.min(Math.max(visibleBottomPart / itemHeight, 0), 1)
  if (bottomProgress > 0 && bottomItem !== rollingTopItem) {
    rollingBottomItem = bottomItem
    setRollingItem(bottomItem, 'rollingBottom', bottomProgress * -68)
  }
}

function scheduleKeyResultsRoll() {
  if (keyResultsAnimationFrame !== null) return
  if (typeof requestAnimationFrame === 'undefined') {
    updateKeyResultsRoll()
    return
  }

  keyResultsAnimationFrame = requestAnimationFrame(() => {
    keyResultsAnimationFrame = null
    updateKeyResultsRoll()
  })
}

onMounted(() => {
  nextTick(updateKeyResultsRoll)
  if (typeof ResizeObserver === 'undefined' || !keyResultsList.value) return
  keyResultsResizeObserver = new ResizeObserver(scheduleKeyResultsRoll)
  keyResultsResizeObserver.observe(keyResultsList.value)
})

onBeforeUnmount(() => {
  keyResultsResizeObserver?.disconnect()
  if (keyResultsAnimationFrame !== null) cancelAnimationFrame(keyResultsAnimationFrame)
  clearRollingItem(rollingTopItem, 'rollingTop')
  clearRollingItem(rollingBottomItem, 'rollingBottom')
})

watch(() => props.objective.key_results.length, () => nextTick(updateKeyResultsRoll))

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
  <v-card class="obj" :class="objective.state" width="330" elevation="3" shaped :key="objective.id">
    <ObjectiveDialog :obj="selectedObj" v-model="openObjDialog" @close="openObjDialog = false"
                     @deleted="emit('deleted', $event)" @updated="emit('updated', $event)"
                     @state-changed="emit('state-changed', $event)"
                     @key-result-created="emit('key-result-created', {objectiveId: objective.id, keyResult: $event})"/>
    <KeyResultDialog :kr="selectedKr" :kr_parent="selectedKr_parent" v-model="openKrDialog"
                     @close="openKrDialog = false"
                     @updated="emit('key-result-updated', {objectiveId: objective.id, keyResult: $event})"
                     @deleted="deleteKeyResult"/>

    <div class="objHeader">
      <v-card-title>{{ objective.name }}</v-card-title>
      <div class="v-card-text" v-html="string_to_html(objective.description)"/>
    </div>

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

    <div v-if="objective.key_results.length > 0"
         class="keyResultsListWrapper">
      <div ref="keyResultsList" class="keyResultsList" @scroll="scheduleKeyResultsRoll">
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
  backface-visibility: hidden;
  border: 1px solid #2c3e50;
  flex: 0 0 auto;
  height: 60px;
  min-height: 60px;
  transform-style: preserve-3d;
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
  transition: filter 120ms ease;
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
  border-radius: 10px !important;
  box-shadow:
    0 2px 4px rgba(16, 24, 40, 0.18),
    inset 0 1px 0 rgba(255, 255, 255, 0.4);
  display: flex;
  flex-direction: column;
  max-height: calc(100dvh - 90px);
  min-width: 330px;
  position: relative;
  vertical-align: top;
  margin-bottom: auto;
  margin-left: 1px;
  color: #000000;
  overflow: hidden;
}

.objHeader {
  flex: 0 0 auto;
  min-width: 0;
}

.objHeader :deep(.v-card-title) {
  font-weight: 650;
}

.keyResultsList {
  display: flex;
  flex: 1 1 auto;
  flex-direction: column;
  gap: 1px;
  min-height: 0;
  overflow-y: auto;
  overscroll-behavior-y: contain;
  padding: 2px;
  perspective: 380px;
  perspective-origin: center;
  position: relative;
  z-index: 1;
}

.keyResultsListWrapper {
  display: flex;
  flex: 1 1 auto;
  flex-direction: column;
  min-height: 0;
  position: relative;
}

.kr.rollingTop {
  transform: rotateX(var(--roll-angle));
  transform-origin: center bottom;
  will-change: transform;
}

.kr.rollingBottom {
  transform: rotateX(var(--roll-angle));
  transform-origin: center top;
  will-change: transform;
}

.obj.active {
  background: #dce8f1;
  border: 1px solid #7899ae;
}

.obj.active .objHeader {
  background: linear-gradient(105deg, #e5eff5, #c9dce8);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.65),
    inset 0 -1px 0 rgba(55, 91, 114, 0.16),
    0 1px 2px rgba(16, 24, 40, 0.12);
  color: #213846;
}

.obj.active .objHeader :deep(a) {
  color: inherit;
}

.obj.active .keyResultsListWrapper {
  background: linear-gradient(145deg, #d7e5ed, #c8dbe7);
  border-bottom: 1px solid rgba(71, 108, 132, 0.18);
  border-radius: 7px;
  border-top: 1px solid rgba(71, 108, 132, 0.18);
  box-shadow:
    inset 0 1px 2px rgba(37, 74, 97, 0.12),
    inset 0 -1px 0 rgba(255, 255, 255, 0.5);
  margin: 4px 4px 0;
}

.obj.active :deep(.v-card-actions) {
  background: linear-gradient(105deg, #dce9f1, #c8dce8);
  border-top: 1px solid rgba(71, 108, 132, 0.18);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.55);
}

.obj.active :deep(.v-card-actions .v-btn) {
  background: rgba(95, 136, 166, 0.12);
  border: 1px solid rgba(71, 108, 132, 0.24);
  box-shadow: none;
}

.obj.active :deep(.v-card-actions .v-icon),
.obj.active .objEdit,
.obj.active .objIdeas {
  color: #213846 !important;
}

.obj.failed {
  background: #f2e1e1;
  border-left: 4px solid #ad5757;
}

.obj.achieved {
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

  .kr.rollingTop,
  .kr.rollingBottom {
    transform: none;
  }
}
</style>
