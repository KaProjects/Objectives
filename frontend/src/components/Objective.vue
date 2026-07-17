<script setup>
import {ref} from 'vue'
import {compareDates, formatDate, string_to_html} from '@/utils'
import {api} from '@/services/apiClient'
import {setError} from '@/state/appState'
import KeyResultDialog from '@/dialogs/KeyResultDialog.vue'
import ObjectiveDialog from '@/dialogs/ObjectiveDialog.vue'
import {KEY_RESULT_STATE, OBJECTIVE_STATE} from '@/constants/states'
import AddKeyResultDialog from '@/dialogs/AddKeyResultDialog.vue'

const props = defineProps({
  objective: {type: Object, required: true},
})
const emit = defineEmits(['deleted', 'state-changed', 'updated', 'key-result-created', 'key-result-updated', 'key-result-deleted'])

const objective = props.objective
const focused = ref(false)
const openObjDialog = ref(false)
const openAddKrDialog = ref(false)
const selectedKr = ref(null)
const selectedKr_parent = ref(null)
const selectedObj = ref(null)
const openKrDialog = ref(false)
const isSubmitting = ref(false)
const submissionError = ref(null)

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
  <v-card class="obj" :class="objective.state" width="300" elevation="3" shaped :key="objective.id"
          @mouseover="focused = true"
          @mouseleave="focused = false"
  >
    <ObjectiveDialog :obj="selectedObj" v-model="openObjDialog" @close="openObjDialog = false"
                     @deleted="emit('deleted', $event)" @updated="emit('updated', $event)"
                     @state-changed="emit('state-changed', $event)"/>
    <KeyResultDialog :kr="selectedKr" :kr_parent="selectedKr_parent" v-model="openKrDialog"
                     @close="openKrDialog = false"
                     @updated="emit('key-result-updated', {objectiveId: objective.id, keyResult: $event})"
                     @deleted="deleteKeyResult"/>

    <v-card-title>{{ objective.name }}</v-card-title>
    <v-card-text v-html="string_to_html(objective.description)"/>

    <v-icon class="objEdit" icon="mdi-pencil-circle-outline" large
            v-if="focused"
            @click="openObjective()"/>

    <div class="objIdeas" v-if="objective.ideas_count > 0">
      <v-icon icon="mdi-lightbulb-variant-outline" size="15" style="margin: 0 auto;"/>
      <div style="margin: -5px auto;">{{ objective.ideas_count }}</div>
    </div>

    <div style="display: grid; overflow-x:scroll; max-height: 650px">
      <v-list-item v-for="key_result in objective.key_results.slice().sort(compareKeyResults)"
                   :key="key_result.id"
                   class="kr" :class="key_result.state"
                   @click="openKeyResult(key_result, objective.state)">
        <v-list-item-content>

          <v-list-item-title class="inLine">{{ key_result.name }}</v-list-item-title>
          <v-icon style="vertical-align: top;" icon="mdi-check-bold"
                  v-if="key_result.state === KEY_RESULT_STATE.COMPLETED"/>
          <v-icon style="vertical-align: top;" icon="mdi-close-thick"
                  v-if="key_result.state === KEY_RESULT_STATE.FAILED"/>

          <div class="krInfo" v-if="key_result.state === KEY_RESULT_STATE.ACTIVE">
            <div class="krInfoChild" style="right: 0;">{{ formatDate(key_result.date_reviewed) }}</div>
            <div class="krInfoChild" style="left: 0;">
              {{ key_result.resolved_tasks_count }}/{{ key_result.all_tasks_count }}
            </div>
          </div>

        </v-list-item-content>
      </v-list-item>
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
  display: inline-block;
}

.obj {
  min-width: 300px;
  vertical-align: top;
  margin-bottom: auto;
  margin-left: 1px;
  color: #000000;
}

.obj.active {
  background: #b2d1ec;
}

.obj.failed {
  background: #dc1a1a;
}

.obj.achieved {
  background: #84e184;
}

.obj.failed > div > .kr {
  color: #262626;
}

.obj.achieved > div > .kr {
  color: #262626;
}

.objEdit {
  position: absolute;
  right: 0;
  top: 0;
}

.objIdeas {
  display: grid;
  position: absolute;
  right: 5px;
  top: 30px;
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
