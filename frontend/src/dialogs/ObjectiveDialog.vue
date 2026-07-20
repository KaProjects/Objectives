<script setup>
import {computed, ref, watch} from 'vue'
import Editable from '@/components/Editable.vue'
import {formatDate, string_to_html} from '@/utils'
import {api} from '@/services/apiClient'
import {setError} from '@/state/appState'
import {OBJECTIVE_STATE} from '@/constants/states'
import DialogCard from '@/dialogs/DialogCard.vue'
import AddKeyResultDialog from '@/dialogs/AddKeyResultDialog.vue'

const props = defineProps({
  modelValue: Boolean,
  obj: Object,
})
const emit = defineEmits(['update:modelValue', 'close', 'deleted', 'updated', 'state-changed', 'key-result-created'])
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
const openAddKeyResultDialog = ref(false)
const keyResultDraft = ref(null)
const ideaToDeleteAfterKeyResult = ref(null)
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
      removeIdeaFromState(idea)
      ideaPendingDeletionId.value = null
    } catch (error) {
      submissionError.value = error.message
    }
  })
}

function removeIdeaFromState(idea) {
  const index = ideas.value.indexOf(idea)
  if (index < 0) return

  ideas.value.splice(index, 1)
  obj.value.ideas_count -= 1
  emit('updated', {id: obj.value.id, ideas_count: obj.value.ideas_count})
}

function createKeyResultFromIdea(idea) {
  if (isSubmitting.value || obj.value.state !== OBJECTIVE_STATE.ACTIVE) return

  keyResultDraft.value = {name: idea.value}
  ideaToDeleteAfterKeyResult.value = idea
  openAddKeyResultDialog.value = true
}

async function keyResultCreatedFromIdea(keyResult) {
  const idea = ideaToDeleteAfterKeyResult.value
  keyResultDraft.value = null
  ideaToDeleteAfterKeyResult.value = null
  if (!idea) return

  await withSubmissionLock(async () => {
    try {
      await api.delete('/objective/' + obj.value.id + '/idea/' + idea.id)
      removeIdeaFromState(idea)
      emit('key-result-created', keyResult)
      closeDialog()
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
  <v-dialog v-model="isOpen" width="600">
    <DialogCard :error="submissionError">
      <Editable :value="draftObjective.name" :editable="obj.state === OBJECTIVE_STATE.ACTIVE" hide-details
                :submit="(value) => updateObjective('name', value)" label="Name">
        <template #display="{startEditing}">
          <v-card-title @click="startEditing" class="dialogTitle text-h5 grey lighten-2">
            {{ obj.name }}
          </v-card-title>
        </template>
      </Editable>

      <Editable :value="draftObjective.description" :editable="obj.state === OBJECTIVE_STATE.ACTIVE" textarea hide-details
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
                   variant="plain" rounded="lg" icon="mdi-trash-can" size="small" v-bind="props"
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
        <Editable :value="idea.value" :editable="obj.state === OBJECTIVE_STATE.ACTIVE" hide-details
                  :submit="(value) => updateIdeaValue(idea, value)" label="Idea">
          <template #display="{startEditing}">
            <div class="idea">
          <v-icon class="ideaIcon" icon="mdi-lightbulb-variant-outline" size="18"/>
          <div class="ideaValue" v-html="string_to_html(idea.value)" @click="startEditing"/>

          <div v-if="obj.state === OBJECTIVE_STATE.ACTIVE" class="ideaActions">
            <v-icon class="ideaCreateKeyResultIcon" icon="mdi-flag-plus-outline" size="18"
                    @click.stop="createKeyResultFromIdea(idea)"/>

            <v-dialog
                :model-value="ideaPendingDeletionId === idea.id"
                @update:model-value="ideaPendingDeletionId = $event ? idea.id : null"
                width="300"
            >
              <template v-slot:activator="{ props }">
                <v-icon class="ideaDeleteIcon" icon="mdi-delete-forever" size="18" v-bind="props"/>
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
          </template>
        </Editable>
      </div>

      <Editable value="" :submit="addIdea" label="Add Idea" hide-details>
        <template #display="{startEditing}">
          <v-btn v-if="obj.state === OBJECTIVE_STATE.ACTIVE" block class="dialogAdd" color="secondary" @click="startEditing">
            Add Idea
          </v-btn>
        </template>
      </Editable>

      <AddKeyResultDialog
          v-model="openAddKeyResultDialog"
          :objective-id="obj.id"
          :initial-key-result="keyResultDraft"
          :show-activator="false"
          @created="keyResultCreatedFromIdea"
      />

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
.dialogTitle {
  display: block;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  width: 100%;
}

.idea {
  align-items: start;
  background-color: rgb(var(--v-theme-surface));
  color: rgb(var(--v-theme-on-surface));
  display: grid;
  grid-template-columns: 25px minmax(0, 1fr) min-content;
  padding-left: 5px;
}

.ideaIcon {
  margin-left: 3px;
  margin-top: 3px;
  opacity: var(--v-medium-emphasis-opacity);
}

.ideaValue {
  white-space: pre-wrap;
}

.ideaDeleteIcon {
  margin: 3px;
}

.ideaCreateKeyResultIcon {
  margin: 3px;
}

.ideaActions {
  align-items: center;
  display: none;
  gap: 4px;
}

.idea:hover .ideaActions {
  display: flex;
}

@media (max-width: 600px) {
  .ideaActions {
    display: flex;
  }
}

.objectiveDetails {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 12px;
  font-size: 12px;
}

.detailsSpacer {
  flex: 1;
}
</style>
