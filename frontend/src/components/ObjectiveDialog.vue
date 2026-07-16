<script setup>
import {computed, ref, watch} from 'vue'
import Editable from '@/components/Editable.vue'
import {formatDate, string_to_html} from '@/utils'
import {api} from '@/services/apiClient'
import {setError} from '@/state/appState'
import {OBJECTIVE_STATE} from '@/constants/states'
import DialogCard from '@/components/DialogCard.vue'

const props = defineProps({
  modelValue: Boolean,
  obj: Object,
})
const emit = defineEmits(['update:modelValue', 'close', 'deleted', 'updated', 'state-changed'])
const isOpen = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})
const obj = ref(null)
const draftObjective = ref({name: '', description: ''})
const editingField = ref(null)
const editingValue = ref('')
const editingIdeaId = ref(null)
const statePendingConfirmation = ref(null)
const selectedIdeaId = ref(null)
const ideas = ref([])
const ideaPendingDeletionId = ref(null)
const confirmDeleteObjDialog = ref(false)
const isSubmitting = ref(false)
const submissionError = ref(null)

watch(() => props.obj, async (value) => {
  obj.value = value ? {...value, key_results: [...value.key_results]} : null
  if (!value) return
  draftObjective.value = {name: value.name, description: value.description}
  try {
    ideas.value = await api.get('/objective/' + value.id + '/idea')
  } catch (error) {
    setError(error)
  }
}, {immediate: true})

function stopEditing() { editingField.value = null; editingIdeaId.value = null }
async function withSubmissionLock(action) {
  if (isSubmitting.value) return
  isSubmitting.value = true
  submissionError.value = null
  try {
    await action()
  } finally {
    isSubmitting.value = false
  }
}
function startEditing(field) {
  if (obj.value.state !== OBJECTIVE_STATE.ACTIVE) return
  stopEditing(); editingValue.value = draftObjective.value[field]; editingField.value = field
}
async function updateObjective(field) {
  await withSubmissionLock(async () => {
    const nextObjective = {...draftObjective.value, [field]: editingValue.value}
    try {
      await api.put('/objective/' + obj.value.id, nextObjective)
      draftObjective.value = nextObjective
      Object.assign(obj.value, nextObjective)
      editingField.value = null
      emit('updated', {id: obj.value.id, name: obj.value.name, description: obj.value.description})
    } catch (error) {
      submissionError.value = error.message
    }
  })
}
function closeDialog() { stopEditing(); isOpen.value = false; emit('close') }
async function updateObjectiveState(state) {
  await withSubmissionLock(async () => {
    try {
      const body = await api.put('/objective/' + obj.value.id + '/state', {state})
      Object.assign(obj.value, {state: body.state, date_finished: body.date})
      emit('updated', {id: obj.value.id, state: body.state, date_finished: body.date})
      statePendingConfirmation.value = null; closeDialog(); emit('state-changed', body.state)
    } catch (error) {
      submissionError.value = error.message
    }
  })
}
function startEditingIdea(idea) {
  if (obj.value.state !== OBJECTIVE_STATE.ACTIVE) return
  stopEditing(); editingValue.value = idea.value; editingIdeaId.value = idea.id
}
async function updateIdeaValue(idea) {
  await withSubmissionLock(async () => {
    try {
      const body = await api.put('/objective/' + obj.value.id + '/idea/' + idea.id, {value: editingValue.value})
      idea.value = body.value; stopEditing()
    } catch (error) {
      submissionError.value = error.message
    }
  })
}
async function addIdea() {
  await withSubmissionLock(async () => {
    try {
      const body = await api.post('/objective/' + obj.value.id + '/idea', {value: editingValue.value})
      ideas.value.push(body); obj.value.ideas_count += 1; editingField.value = null
      emit('updated', {id: obj.value.id, ideas_count: obj.value.ideas_count})
    } catch (error) {
      submissionError.value = error.message
    }
  })
}
async function deleteIdea(idea) {
  await withSubmissionLock(async () => {
    try {
      await api.delete('/objective/' + obj.value.id + '/idea/' + idea.id)
      ideas.value.splice(ideas.value.indexOf(idea), 1); obj.value.ideas_count -= 1; ideaPendingDeletionId.value = null
      emit('updated', {id: obj.value.id, ideas_count: obj.value.ideas_count})
    } catch (error) {
      submissionError.value = error.message
    }
  })
}
function deleteObjective() { emit('deleted', obj.value); confirmDeleteObjDialog.value = false; closeDialog() }
</script>

<template>
  <v-dialog v-model="isOpen" persistent width="600">
    <DialogCard :error="submissionError">
      <Editable v-if="editingField === 'name'" :cancel="stopEditing" :submit="updateObjective" index="name">
        <v-text-field @keydown.enter="updateObjective('name')" @keydown.esc="stopEditing"
                      v-model="editingValue"
                      label="Name"
        ></v-text-field>
      </Editable>
      <div v-else class="datesInfo">
        <v-card-title @click="startEditing('name')" class="text-h5 grey lighten-2">
          {{obj.name}}
        </v-card-title>
        <div class="datesInfoChild" style="top: 0;">created: {{formatDate(obj.date_created)}}</div>
        <div class="datesInfoChild" style="top: 15px;" v-if="obj.state === OBJECTIVE_STATE.ACHIEVED">achieved: {{formatDate(obj.date_finished)}}</div>
        <div class="datesInfoChild" style="top: 15px;" v-if="obj.state === OBJECTIVE_STATE.FAILED">failed: {{formatDate(obj.date_finished)}}</div>
      </div>

      <Editable v-if="editingField === 'description'" :cancel="stopEditing" :submit="updateObjective" index="description">
        <v-textarea @keydown.enter="updateObjective('description')" @keydown.esc="stopEditing"
                    v-model="editingValue"
                    label="Description"
        ></v-textarea>
      </Editable>
      <div v-else>
        <v-card-text v-html="string_to_html(obj.description)" @click="startEditing('description')"/>

        <v-dialog v-model="confirmDeleteObjDialog" width="300"> TODO only if no KR
          <template v-slot:activator="{ props }">
            <v-btn :disabled="obj.key_results.length > 0"
                   style="bottom: -10px; right: -10px; position: absolute;"
                   variant="plain" icon="mdi-trash-can" v-bind="props"
            />
          </template>
          <v-card>
            <v-card-title class="text-h5 grey lighten-2">
              Delete permanently?
            </v-card-title>
            <v-card-actions>
              <v-btn block @click="deleteObjective()">Confirm</v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>
      </div>

      <v-divider></v-divider>

      <div v-for="idea in ideas" :key="idea.id">
        <Editable v-if="editingIdeaId === idea.id" :cancel="stopEditing" :submit="updateIdeaValue" :index="idea">
          <v-text-field @keydown.enter="updateIdeaValue(idea)" @keydown.esc="stopEditing"
                        v-model="editingValue"
                        label="Idea"
          ></v-text-field>
        </Editable>
        <div v-else class="idea"
             @mouseover="selectedIdeaId = idea.id"
             @mouseleave="selectedIdeaId = null">
          <v-icon icon="mdi-lightbulb-variant-outline" large/>
          <div v-html="string_to_html(idea.value)" @click="startEditingIdea(idea)" style="margin-left: 5px; flex: 25;"/>

          <v-dialog
              :model-value="ideaPendingDeletionId === idea.id"
              @update:model-value="ideaPendingDeletionId = $event ? idea.id : null"
              width="300"
          >
            <template v-slot:activator="{ props }">
              <v-icon style="flex: 1;" icon="mdi-delete-forever" large v-bind="props" v-if="selectedIdeaId === idea.id && obj.state === OBJECTIVE_STATE.ACTIVE"/>
            </template>

            <v-card>
              <v-card-title class="text-h5 grey lighten-2">
                Delete Idea?
              </v-card-title>
              <v-card-text>
                {{ idea.value }}
              </v-card-text>
              <v-card-actions>
                <v-btn block :disabled="isSubmitting" @click="deleteIdea(idea)">Confirm</v-btn>
              </v-card-actions>
            </v-card>
          </v-dialog>
        </div>
      </div>

      <Editable v-if="editingField === 'newIdea'" :cancel="stopEditing" :submit="addIdea">
        <v-text-field @keydown.enter="addIdea" @keydown.esc="stopEditing"
                      v-model="editingValue"
                      label="Add Idea"
        ></v-text-field>
      </Editable>
      <v-btn v-else v-if="obj.state === OBJECTIVE_STATE.ACTIVE" color="secondary" @click="editingField = 'newIdea'; editingValue = ''">
        Add Idea
      </v-btn>

    </DialogCard>

    <div>
      <v-dialog :model-value="statePendingConfirmation === OBJECTIVE_STATE.FAILED" @update:model-value="statePendingConfirmation = $event ? OBJECTIVE_STATE.FAILED : null" width="300" v-if="obj.state === OBJECTIVE_STATE.ACTIVE">
        <template v-slot:activator="{ props }">
          <v-btn style="width: 50%;" color="red" v-bind="props">fail</v-btn>
        </template>
        <v-card>
          <v-card-title class="text-h5 grey lighten-2">
            Fail?
          </v-card-title>
          <v-card-actions>
            <v-btn block :disabled="isSubmitting" @click="updateObjectiveState(OBJECTIVE_STATE.FAILED)">Confirm</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
      <v-dialog :model-value="statePendingConfirmation === OBJECTIVE_STATE.ACHIEVED" @update:model-value="statePendingConfirmation = $event ? OBJECTIVE_STATE.ACHIEVED : null" width="300" v-if="obj.state === OBJECTIVE_STATE.ACTIVE">
        <template v-slot:activator="{ props }">
          <v-btn style="width: 50%;" color="green" v-bind="props">achieve</v-btn>
        </template>
        <v-card>
          <v-card-title class="text-h5 grey lighten-2">
            Achieve?
          </v-card-title>
          <v-card-actions>
            <v-btn block :disabled="isSubmitting" @click="updateObjectiveState(OBJECTIVE_STATE.ACHIEVED)">Confirm</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
      <v-dialog :model-value="statePendingConfirmation === OBJECTIVE_STATE.ACTIVE" @update:model-value="statePendingConfirmation = $event ? OBJECTIVE_STATE.ACTIVE : null" width="300" v-if="obj.state !== OBJECTIVE_STATE.ACTIVE">
        <template v-slot:activator="{ props }">
          <v-btn style="width: 100%;" color="blue" v-bind="props">activate</v-btn>
        </template>
        <v-card>
          <v-card-title class="text-h5 grey lighten-2">
            Activate?
          </v-card-title>
          <v-card-actions>
            <v-btn block :disabled="isSubmitting" @click="updateObjectiveState(OBJECTIVE_STATE.ACTIVE)">Confirm</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </div>

    <v-btn color="primary" @click="closeDialog">Close</v-btn>

  </v-dialog>
</template>

<style scoped>
.idea {
  display: flex;
  background: white;
}
.idea:hover {
  background: #f5f5f5;
}
.datesInfo {
  position: relative;
}
.datesInfoChild {
  font-size: 12px;
  position: absolute;
  right: 5px;
}
</style>
