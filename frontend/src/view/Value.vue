<script setup>
import {onMounted, ref, watch} from 'vue'
import {appState, setError, unselectValue} from '@/state/appState'
import Objective from '@/components/Objective.vue'
import {compareDates} from '@/utils'
import {api} from '@/services/apiClient'
import Ideas from '@/components/Ideas.vue'
import {OBJECTIVE_STATE, OBJECTIVE_TAB} from '@/constants/states'

const value = ref({objectives: []})
const tab = ref(OBJECTIVE_TAB.ACTIVE)
const openAddObjDialog = ref(false)
const newObj = ref({name: '', description: ''})
const showIdeas = ref(false)
const isSubmitting = ref(false)

watch(openAddObjDialog, (isOpen) => {
  if (isOpen) newObj.value = {name: '', description: ''}
})

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

async function addObjective() {
  if (isSubmitting.value) return
  isSubmitting.value = true
  try {
    const objective = {...newObj.value, value_id: value.value.id}
    const body = await api.post('/objective', objective)
    value.value.objectives.push(body)
    openAddObjDialog.value = false
    tab.value = OBJECTIVE_TAB.ACTIVE
  } catch (error) {
    setError(error)
  } finally {
    isSubmitting.value = false
  }
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
      <v-btn class="button" icon="mdi-arrow-left" @click="unselectValue()"/>
      <h1 class="title">{{value.name}}</h1>

      <v-tabs v-model="tab" bg-color="primary">
        <v-tab :value="OBJECTIVE_TAB.ACTIVE">Active</v-tab>
        <v-tab :value="OBJECTIVE_TAB.INACTIVE">Done</v-tab>
      </v-tabs>

      <v-btn class="button" icon="mdi-lightbulb" @click.stop="showIdeas = false" v-if="showIdeas"/>
      <v-btn class="button" icon="mdi-lightbulb-outline" @click.stop="showIdeas = true" v-else/>

      <v-dialog v-model="openAddObjDialog" width="300">
        <template v-slot:activator="{ props }">
          <v-btn v-bind="props" class="button" icon="mdi-plus"/>
        </template>
        <v-card>
          <v-text-field label="Name" v-model="newObj.name"/>
          <v-text-field label="Description" v-model="newObj.description"/>
          <v-card-actions>
            <v-btn block @click="addObjective" :disabled="isSubmitting || !newObj.name">Add</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </div>

    <div style="display: flex; overflow-x:scroll;">
      <Ideas class="obj" :valueId="appState.selectedValue.id" v-if="showIdeas"/>
      <Objective v-for="objective in filterObjectives(value.objectives, tab === OBJECTIVE_TAB.ACTIVE)"
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
}
.title {
  width: 300px;
}
.button {
  margin-left: 10px;
  margin-right: 10px;
  background: #181818;
  color: darkgrey
}
.button:hover {
  background: #2f2f2f;
}
</style>
