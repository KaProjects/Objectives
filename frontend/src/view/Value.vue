<script setup>
import {onMounted, ref} from 'vue'
import {appState, setError, unselectValue} from '@/state/appState'
import Objective from '@/components/Objective.vue'
import {compareDates} from '@/utils'
import {api} from '@/services/apiClient'
import Ideas from '@/components/Ideas.vue'
import {OBJECTIVE_STATE, OBJECTIVE_TAB} from '@/constants/states'
import AddObjectiveDialog from '@/dialogs/AddObjectiveDialog.vue'
import AddIdeaDialog from '@/dialogs/AddIdeaDialog.vue'

const value = ref({objectives: []})
const tab = ref(OBJECTIVE_TAB.ACTIVE)
const openAddObjDialog = ref(false)
const openAddIdeaDialog = ref(false)
const ideas = ref(null)
const isSubmitting = ref(false)

async function loadData() {
  try {
    value.value = await api.get('/value/' + appState.selectedValue.id)
  } catch (error) {
    setError(error)
  }
}

function compareObjectives(a, b) {
  let comparison
  if (a.state !== OBJECTIVE_STATE.ACTIVE && b.state !== OBJECTIVE_STATE.ACTIVE) {
    comparison = -compareDates(a.date_finished, b.date_finished)
  } else {
    comparison = -compareDates(a.date_created, b.date_created)
  }
  return comparison !== 0 ? comparison : b.id - a.id
}

function filterObjectives(objectives, isActive) {
  if (objectives === undefined) return objectives
  return objectives.filter((objective) => isActive ? objective.state === OBJECTIVE_STATE.ACTIVE : objective.state !== OBJECTIVE_STATE.ACTIVE)
      .slice().sort(compareObjectives)
}

function addObjective(objective) {
  value.value.objectives.push(objective)
  tab.value = OBJECTIVE_TAB.ACTIVE
}

function addIdea(idea) {
  ideas.value?.addCreatedIdea(idea)
}

function selectTab(state) {
  tab.value = state === OBJECTIVE_STATE.ACTIVE ? OBJECTIVE_TAB.ACTIVE : OBJECTIVE_TAB.INACTIVE
}

function updateObjective(updatedObjective) {
  const objective = value.value.objectives.find((item) => item.id === updatedObjective.id)
  if (objective) Object.assign(objective, updatedObjective)
}

function addKeyResult({objectiveId, keyResult}) {
  const objective = value.value.objectives.find((item) => item.id === objectiveId)
  if (objective) objective.key_results.push(keyResult)
}

function updateKeyResult({objectiveId, keyResult}) {
  const objective = value.value.objectives.find((item) => item.id === objectiveId)
  const existingKeyResult = objective?.key_results.find((item) => item.id === keyResult.id)
  if (existingKeyResult) Object.assign(existingKeyResult, keyResult)
}

function removeKeyResult({objectiveId, keyResultId}) {
  const objective = value.value.objectives.find((item) => item.id === objectiveId)
  if (!objective) return
  objective.key_results = objective.key_results.filter((item) => item.id !== keyResultId)
}

async function deleteObjective(objective) {
  if (isSubmitting.value) return
  isSubmitting.value = true
  try {
    await api.delete('/objective/' + objective.id)
    const index = value.value.objectives.findIndex((item) => item.id === objective.id)
    if (index !== -1) value.value.objectives.splice(index, 1)
  } catch (error) {
    setError(error)
  } finally {
    isSubmitting.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <div>

    <div class="appbar">
      <v-btn class="button" variant="tonal" rounded="lg" @click="unselectValue()">
        <v-icon icon="mdi-arrow-left"/>
      </v-btn>
      <h1 class="title">{{ value.name }}</h1>

      <v-tabs v-model="tab" bg-color="primary">
        <v-tab :value="OBJECTIVE_TAB.ACTIVE">Active</v-tab>
        <v-tab :value="OBJECTIVE_TAB.INACTIVE">Done</v-tab>
        <v-tab :value="OBJECTIVE_TAB.IDEAS">Ideas</v-tab>
      </v-tabs>

      <AddObjectiveDialog
          v-if="tab === OBJECTIVE_TAB.ACTIVE"
          v-model="openAddObjDialog"
          :value-id="value.id"
          @created="addObjective"
      />
      <AddIdeaDialog
          v-if="tab === OBJECTIVE_TAB.IDEAS"
          v-model="openAddIdeaDialog"
          :value-id="value.id"
          @created="addIdea"
      />
    </div>

    <div style="display: flex; overflow-x:scroll;">
      <Ideas ref="ideas" class="obj" :valueId="appState.selectedValue.id" v-if="tab === OBJECTIVE_TAB.IDEAS"/>
      <Objective v-for="objective in filterObjectives(value.objectives, tab === OBJECTIVE_TAB.ACTIVE)"
                 v-if="tab !== OBJECTIVE_TAB.IDEAS"
                 :key="objective.id"
                 :objective="objective"
                 @deleted="deleteObjective"
                 @state-changed="selectTab"
                 @updated="updateObjective"
                 @key-result-created="addKeyResult"
                 @key-result-updated="updateKeyResult"
                 @key-result-deleted="removeKeyResult"/>
    </div>
  </div>
</template>

<style scoped>
.appbar {
  display: inline-flex;
  align-items: center;
}

.title {
  width: 300px;
}

.button {
  margin-left: 10px;
  margin-right: 10px;
}
</style>
