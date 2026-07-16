<script setup>
import {computed, ref, watch} from 'vue'
import Editable from '@/components/Editable.vue'
import {formatDate, string_to_html} from '@/utils'
import {api} from '@/services/apiClient'
import {setError} from '@/state/appState'
import {OBJECTIVE_STATE} from '@/constants/states'
import DialogCard from '@/dialogs/DialogCard.vue'

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

async function withSubmissionLock(action) {
  if (isSubmitting.value) return
  isSubmitting.value = true
  submissionError.value = null
  try {
    return await action()
  } finally {
    isSubmitting.value = false
  }
}

async function updateObjective(field, value) {
  return withSubmissionLock(async () => {
    const nextObjective = {...draftObjective.value, [field]: value}
    try {
      await api.put('/objective/' + obj.value.id, nextObjective)
      draftObjective.value = nextObjective
      Object.assign(obj.value, nextObjective)
      emit('updated', {id: obj.value.id, name: obj.value.name, description: obj.value.description})
      return true
    } catch (error) {
      submissionError.value = error.message
      return false
    }
  })
}

function closeDialog() {
  isOpen.value = false;
  emit('close')
}

async function updateObjectiveState(state) {
  await withSubmissionLock(async () => {
    try {
      const body = await api.put('/objective/' + obj.value.id + '/state', {state})
      Object.assign(obj.value, {state: body.state, date_finished: body.date})
      emit('updated', {id: obj.value.id, state: body.state, date_finished: body.date})
      statePendingConfirmation.value = null;
      closeDialog();
      emit('state-changed', body.state)
    } catch (error) {
      submissionError.value = error.message
    }
  })
}

async function updateIdeaValue(idea, value) {
  return withSubmissionLock(async () => {
    try {
      const body = await api.put('/objective/' + obj.value.id + '/idea/' + idea.id, {value})
      idea.value = body.value;
      return true
    } catch (error) {
      submissionError.value = error.message
      return false
    }
  })
}

async function addIdea(value) {
  return withSubmissionLock(async () => {
    try {
      const body = await api.post('/objective/' + obj.value.id + '/idea', {value})
      ideas.value.push(body);
      obj.value.ideas_count += 1;
      emit('updated', {id: obj.value.id, ideas_count: obj.value.ideas_count})
      return true
    } catch (error) {
      submissionError.value = error.message
      return false
    }
  })
}

async function deleteIdea(idea) {
  await withSubmissionLock(async () => {
    try {
      await api.delete('/objective/' + obj.value.id + '/idea/' + idea.id)
      ideas.value.splice(ideas.value.indexOf(idea), 1);
      obj.value.ideas_count -= 1;
      ideaPendingDeletionId.value = null
      emit('updated', {id: obj.value.id, ideas_count: obj.value.ideas_count})
    } catch (error) {
      submissionError.value = error.message
    }
  })
}

function deleteObjective() {
  emit('deleted', obj.value);
  confirmDeleteObjDialog.value = false;
  closeDialog()
}
</script>

<template>
  <v-dialog v-model="isOpen" persistent width="600">
    <DialogCard :error="submissionError">
      <Editable :value="draftObjective.name" :editable="obj.state === OBJECTIVE_STATE.ACTIVE"
                :submit="(value) => updateObjective('name', value)" label="Name">
        <template #display="{startEditing}">
          <v-card-title @click="startEditing" class="text-h5 grey lighten-2">
            {{ obj.name }}
          </v-card-title>
        </template>
      </Editable>

      <Editable :value="draftObjective.description" :editable="obj.state === OBJECTIVE_STATE.ACTIVE" textarea
                :submit="(value) => updateObjective('description', value)" label="Description">
        <template #display="{startEditing}">
          <v-card-text v-html="string_to_html(obj.description)" @click="startEditing"/>
        </template>
      </Editable>

      <div class="objectiveDetails">
        <span>created: {{ formatDate(obj.date_created) }}</span>
        <span v-if="obj.state === OBJECTIVE_STATE.ACHIEVED">achieved: {{ formatDate(obj.date_finished) }}</span>
        <span v-if="obj.state === OBJECTIVE_STATE.FAILED">failed: {{ formatDate(obj.date_finished) }}</span>
        <span class="detailsSpacer"/>
        <v-dialog v-model="confirmDeleteObjDialog" width="300">
          <template v-slot:activator="{ props }">
            <v-btn :disabled="obj.key_results.length > 0"
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
        <Editable :value="idea.value" :editable="obj.state === OBJECTIVE_STATE.ACTIVE"
                  :submit="(value) => updateIdeaValue(idea, value)" label="Idea">
          <template #display="{startEditing}">
            <div class="idea"
             @mouseover="selectedIdeaId = idea.id"
             @mouseleave="selectedIdeaId = null">
          <v-icon icon="mdi-lightbulb-variant-outline" large/>
          <div v-html="string_to_html(idea.value)" @click="startEditing"
               style="margin-left: 5px; flex: 25;"/>

          <v-dialog
              :model-value="ideaPendingDeletionId === idea.id"
              @update:model-value="ideaPendingDeletionId = $event ? idea.id : null"
              width="300"
          >
            <template v-slot:activator="{ props }">
              <v-icon style="flex: 1;" icon="mdi-delete-forever" large v-bind="props"
                      v-if="selectedIdeaId === idea.id && obj.state === OBJECTIVE_STATE.ACTIVE"/>
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
          </template>
        </Editable>
      </div>

      <Editable value="" :submit="addIdea" label="Add Idea">
        <template #display="{startEditing}">
          <v-btn v-if="obj.state === OBJECTIVE_STATE.ACTIVE" block class="dialogAdd" color="secondary" @click="startEditing">
            Add Idea
          </v-btn>
        </template>
      </Editable>

    </DialogCard>

    <div>
      <v-dialog :model-value="statePendingConfirmation === OBJECTIVE_STATE.FAILED"
                @update:model-value="statePendingConfirmation = $event ? OBJECTIVE_STATE.FAILED : null"
                width="300" v-if="obj.state === OBJECTIVE_STATE.ACTIVE">
        <template v-slot:activator="{ props }">
          <v-btn class="dialogFail" style="width: 50%;" color="red" v-bind="props">fail</v-btn>
        </template>
        <v-card>
          <v-card-title class="text-h5 grey lighten-2">
            Fail?
          </v-card-title>
          <v-card-actions>
            <v-btn block :disabled="isSubmitting" @click="updateObjectiveState(OBJECTIVE_STATE.FAILED)">
              Confirm
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
      <v-dialog :model-value="statePendingConfirmation === OBJECTIVE_STATE.ACHIEVED"
                @update:model-value="statePendingConfirmation = $event ? OBJECTIVE_STATE.ACHIEVED : null"
                width="300" v-if="obj.state === OBJECTIVE_STATE.ACTIVE">
        <template v-slot:activator="{ props }">
          <v-btn class="dialogSuccess" style="width: 50%;" color="green" v-bind="props">achieve</v-btn>
        </template>
        <v-card>
          <v-card-title class="text-h5 grey lighten-2">
            Achieve?
          </v-card-title>
          <v-card-actions>
            <v-btn block :disabled="isSubmitting" @click="updateObjectiveState(OBJECTIVE_STATE.ACHIEVED)">
              Confirm
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
      <v-dialog :model-value="statePendingConfirmation === OBJECTIVE_STATE.ACTIVE"
                @update:model-value="statePendingConfirmation = $event ? OBJECTIVE_STATE.ACTIVE : null"
                width="300" v-if="obj.state !== OBJECTIVE_STATE.ACTIVE">
        <template v-slot:activator="{ props }">
          <v-btn class="dialogActivate" style="width: 100%;" color="blue" v-bind="props">activate</v-btn>
        </template>
        <v-card>
          <v-card-title class="text-h5 grey lighten-2">
            Activate?
          </v-card-title>
          <v-card-actions>
            <v-btn block :disabled="isSubmitting" @click="updateObjectiveState(OBJECTIVE_STATE.ACTIVE)">
              Confirm
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </div>

    <v-btn class="dialogClose" color="primary" @click="closeDialog">Close</v-btn>

  </v-dialog>
</template>

<style scoped>
.idea {
  display: flex;
  background-color: rgb(var(--v-theme-surface));
  color: rgb(var(--v-theme-on-surface));
}

.idea:hover {
  background-color: rgb(var(--v-theme-surface-variant));
}

.objectiveDetails {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 12px 8px;
  font-size: 12px;
}

.detailsSpacer {
  flex: 1;
}
</style>
