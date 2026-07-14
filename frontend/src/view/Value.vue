<script setup>
import {onMounted, ref, watch} from 'vue'
import {appState, setError, unselectValue} from '@/state/appState'
import Objective from '@/components/Objective.vue'
import {compare_dates} from '@/utils'
import {api} from '@/services/apiClient'
import Ideas from '@/components/Ideas.vue'

const value = ref({objectives: []})
const tab = ref('active')
const openAddObjDialog = ref(false)
const newObj = ref({name: '', description: ''})
const showIdeas = ref(false)

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
      if (a.state !== "active" &&  b.state !== "active") {
        comparison = - compare_dates(a.date_finished, b.date_finished)
      } else {
    comparison = - compare_dates(a.date_created, b.date_created)
  }
  return comparison !== 0 ? comparison : b.id - a.id
}

function filterObjectives(objectives, isActive) {
  if (objectives === undefined) return objectives
  return objectives.filter((objective) => isActive ? objective.state === 'active' : objective.state !== 'active')
    .slice().sort(compareObjectives)
}

async function addObjective() {
  try {
    const objective = {...newObj.value, value_id: value.value.id}
    const body = await api.post('/objective', objective)
    value.value.objectives.push(body)
    openAddObjDialog.value = false
    tab.value = 'active'
  } catch (error) {
    setError(error)
  }
}

function selectTab(state) {
  tab.value = state === 'active' ? 'active' : 'inactive'
}

async function deleteObjective(objective) {
  try {
    await api.delete('/objective/' + objective.id)
    value.value.objectives.splice(value.value.objectives.indexOf(objective), 1)
  } catch (error) {
    setError(error)
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
        <v-tab value="active">Active</v-tab>
        <v-tab value="inactive">Done</v-tab>
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
            <v-btn block @click="addObjective" :disabled="!newObj.name">Add</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </div>

    <div style="display: flex; overflow-x:scroll;">
      <Ideas class="obj" :valueId="appState.selectedValue.id" v-if="showIdeas"/>
      <Objective v-for="objective in filterObjectives(value.objectives, tab === 'active')"
                 :key="objective.id"
                 :objective="objective"
                 @deleted="deleteObjective"
                 @state-changed="selectTab"/>
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
