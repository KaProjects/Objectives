<script setup>
import {computed, ref, watch} from 'vue'
import Editable from '@/components/Editable.vue'
import {formatDate, string_to_html} from '@/utils'
import {api} from '@/services/apiClient'
import {setError} from '@/state/appState'
import {OBJECTIVE_STATE} from '@/constants/states'
import DialogCard from '@/dialogs/DialogCard.vue'
import AddKeyResultDialog from '@/dialogs/AddKeyResultDialog.vue'
import IconAction from '@/components/IconAction.vue'

const props = defineProps({
  modelValue: Boolean,
  obj: Object,
})
const emit = defineEmits(['update:modelValue', 'close', 'deleted', 'updated', 'state-changed', 'key-result-created'])
const isOpen = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})
const objective = ref(null)
const draftObjective = ref({name: '', description: ''})
const statePendingConfirmation = ref(null)
const ideas = ref([])
const ideaPendingDeletionId = ref(null)
const openAddKeyResultDialog = ref(false)
const keyResultDraft = ref(null)
const ideaToDeleteAfterKeyResult = ref(null)
const confirmDeleteObjDialog = ref(false)
const isSubmitting = ref(false)
const submissionError = ref(null)
const canDeleteObjective = computed(() => (props.obj?.key_results?.length ?? 0) === 0)
const dateInputProps = Object.freeze({density: 'compact', style: 'width: 150px'})

watch(() => props.obj, async (value) => {
  objective.value = value ? {...value, key_results: [...value.key_results]} : null
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
      await api.put('/objective/' + objective.value.id, nextObjective)
      draftObjective.value = nextObjective
      Object.assign(objective.value, nextObjective)
      emit('updated', {id: objective.value.id, name: objective.value.name, description: objective.value.description})
      return true
    } catch (error) {
      submissionError.value = error.message
      return false
    }
  })
}

async function updateObjectiveDate(field, value) {
  return withSubmissionLock(async () => {
    const dates = {
      date_created: objective.value.date_created,
      date_finished: objective.value.date_finished,
      [field]: value,
    }
    try {
      const updatedDates = await api.put('/objective/' + objective.value.id + '/dates', dates)
      Object.assign(objective.value, updatedDates)
      emit('updated', {id: objective.value.id, ...updatedDates})
      return true
    } catch (error) {
      submissionError.value = error.message
      return false
    }
  })
}

function finishedDateLabel() {
  return objective.value.state === OBJECTIVE_STATE.ACHIEVED ? 'Achieved' : 'Failed'
}

function closeDialog() {
  isOpen.value = false;
  emit('close')
}

async function updateObjectiveState(state) {
  await withSubmissionLock(async () => {
    try {
      const body = await api.put('/objective/' + objective.value.id + '/state', {state})
      Object.assign(objective.value, {state: body.state, date_finished: body.date})
      emit('updated', {id: objective.value.id, state: body.state, date_finished: body.date})
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
      const body = await api.put('/objective/' + objective.value.id + '/idea/' + idea.id, {value})
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
      const body = await api.post('/objective/' + objective.value.id + '/idea', {value})
      ideas.value.push(body);
      objective.value.ideas_count += 1;
      emit('updated', {id: objective.value.id, ideas_count: objective.value.ideas_count})
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
      await api.delete('/objective/' + objective.value.id + '/idea/' + idea.id)
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
  objective.value.ideas_count -= 1
  emit('updated', {id: objective.value.id, ideas_count: objective.value.ideas_count})
}

function createKeyResultFromIdea(idea) {
  if (isSubmitting.value || objective.value.state !== OBJECTIVE_STATE.ACTIVE) return

  keyResultDraft.value = {name: idea.value}
  ideaToDeleteAfterKeyResult.value = idea
  openAddKeyResultDialog.value = true
}

async function keyResultCreatedFromIdea(keyResult) {
  const idea = ideaToDeleteAfterKeyResult.value
  keyResultDraft.value = null
  ideaToDeleteAfterKeyResult.value = null
  if (!idea) return

  emit('key-result-created', keyResult)

  await withSubmissionLock(async () => {
    try {
      await api.delete('/objective/' + objective.value.id + '/idea/' + idea.id)
      removeIdeaFromState(idea)
      closeDialog()
    } catch (error) {
      submissionError.value = `Key Result was created, but its source idea could not be deleted: ${error.message}`
    }
  })
}

async function deleteObjective() {
  return withSubmissionLock(async () => {
    try {
      await api.delete('/objective/' + objective.value.id)
      emit('deleted', objective.value)
      confirmDeleteObjDialog.value = false
      closeDialog()
      return true
    } catch (error) {
      submissionError.value = error.message
      return false
    }
  })
}
</script>

<template>
  <v-dialog v-model="isOpen" width="600">
    <DialogCard :error="submissionError">
      <Editable :value="draftObjective.name" :editable="objective.state === OBJECTIVE_STATE.ACTIVE" hide-details
                :submit="(value) => updateObjective('name', value)" label="Name">
        <template #display="{startEditing}">
          <v-card-title class="dialogTitle text-h5 grey lighten-2"
                        :role="objective.state === OBJECTIVE_STATE.ACTIVE ? 'button' : undefined"
                        :tabindex="objective.state === OBJECTIVE_STATE.ACTIVE ? 0 : undefined"
                        :aria-label="objective.state === OBJECTIVE_STATE.ACTIVE ? 'Edit Objective name' : undefined"
                        @click="startEditing"
                        @keydown.enter.prevent="startEditing"
                        @keydown.space.prevent="startEditing">
            {{ objective.name }}
          </v-card-title>
        </template>
      </Editable>

      <Editable :value="draftObjective.description" :editable="objective.state === OBJECTIVE_STATE.ACTIVE" textarea hide-details
                :submit="(value) => updateObjective('description', value)" label="Description">
        <template #display="{startEditing}">
          <div class="v-card-text"
               :role="objective.state === OBJECTIVE_STATE.ACTIVE ? 'button' : undefined"
               :tabindex="objective.state === OBJECTIVE_STATE.ACTIVE ? 0 : undefined"
               :aria-label="objective.state === OBJECTIVE_STATE.ACTIVE ? 'Edit Objective description' : undefined"
               v-html="string_to_html(objective.description)"
               @click="startEditing"
               @keydown.enter.prevent="startEditing"
               @keydown.space.prevent="startEditing"/>
        </template>
      </Editable>

      <div class="objectiveDetails">
        <Editable class="dateEditor" :value="objective.date_created" date-picker hide-details
                  :input-props="dateInputProps"
                  :submit="(value) => updateObjectiveDate('date_created', value)" label="Created">
          <template #display="{startEditing}">
            <button type="button" class="dateDisplay" aria-label="Edit Objective created date"
                    @click="startEditing">
              created: {{ formatDate(objective.date_created) }}
            </button>
          </template>
        </Editable>
        <Editable v-if="objective.state !== OBJECTIVE_STATE.ACTIVE" class="dateEditor"
                  :value="objective.date_finished" date-picker hide-details :input-props="dateInputProps"
                  :submit="(value) => updateObjectiveDate('date_finished', value)" :label="finishedDateLabel()">
          <template #display="{startEditing}">
            <button type="button" class="dateDisplay" aria-label="Edit Objective finished date"
                    @click="startEditing">
              {{ finishedDateLabel().toLowerCase() }}: {{ formatDate(objective.date_finished) }}
            </button>
          </template>
        </Editable>
        <span class="detailsSpacer"/>
        <v-dialog v-model="confirmDeleteObjDialog" width="300">
          <template v-slot:activator="{ props }">
            <v-btn :disabled="!canDeleteObjective"
                   variant="plain" rounded="lg" icon="mdi-trash-can" size="small"
                   aria-label="Delete Objective" v-bind="props"
            />
          </template>
          <v-card>
            <v-card-title class="text-h5 grey lighten-2">
              Delete permanently?
            </v-card-title>
            <v-card-actions>
              <v-btn block :disabled="isSubmitting" @click="deleteObjective()">Confirm</v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>
      </div>

      <v-divider></v-divider>

      <div class="ideasList">
        <div v-for="idea in ideas" :key="idea.id">
          <Editable :value="idea.value" :editable="objective.state === OBJECTIVE_STATE.ACTIVE" hide-details
                    :submit="(value) => updateIdeaValue(idea, value)" label="Idea">
            <template #display="{startEditing}">
              <div class="idea">
                <v-icon class="ideaIcon" icon="mdi-lightbulb-variant-outline" size="18"/>
                <div class="ideaValue"
                     :role="objective.state === OBJECTIVE_STATE.ACTIVE ? 'button' : undefined"
                     :tabindex="objective.state === OBJECTIVE_STATE.ACTIVE ? 0 : undefined"
                     :aria-label="objective.state === OBJECTIVE_STATE.ACTIVE ? `Edit idea ${idea.value}` : undefined"
                     v-html="string_to_html(idea.value)"
                     @click="startEditing"
                     @keydown.enter.prevent="startEditing"
                     @keydown.space.prevent="startEditing"/>

                <div v-if="objective.state === OBJECTIVE_STATE.ACTIVE" class="ideaActions">
                  <IconAction class="ideaCreateKeyResultIcon" icon="mdi-flag-plus-outline" size="18"
                              :label="`Create Key Result from ${idea.value}`"
                              @click.stop="createKeyResultFromIdea(idea)"/>

                  <v-dialog
                      :model-value="ideaPendingDeletionId === idea.id"
                      @update:model-value="ideaPendingDeletionId = $event ? idea.id : null"
                      width="300"
                  >
                    <template v-slot:activator="{ props }">
                      <IconAction class="ideaDeleteIcon" icon="mdi-delete-forever" size="18"
                                  :label="`Delete idea ${idea.value}`" v-bind="props"/>
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
      </div>

      <Editable value="" :submit="addIdea" label="Add Idea" hide-details>
        <template #display="{startEditing}">
          <v-btn v-if="objective.state === OBJECTIVE_STATE.ACTIVE" block class="dialogAdd" color="secondary" @click="startEditing">
            Add Idea
          </v-btn>
        </template>
      </Editable>

      <AddKeyResultDialog
          v-model="openAddKeyResultDialog"
          :objective-id="objective.id"
          :initial-key-result="keyResultDraft"
          :show-activator="false"
          @created="keyResultCreatedFromIdea"
      />

    </DialogCard>

    <div>
      <v-dialog :model-value="statePendingConfirmation === OBJECTIVE_STATE.FAILED"
                @update:model-value="statePendingConfirmation = $event ? OBJECTIVE_STATE.FAILED : null"
                width="300" v-if="objective.state === OBJECTIVE_STATE.ACTIVE">
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
                width="300" v-if="objective.state === OBJECTIVE_STATE.ACTIVE">
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
                width="300" v-if="objective.state !== OBJECTIVE_STATE.ACTIVE">
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

.ideasList {
  max-height: min(360px, calc(100dvh - 360px));
  overflow-y: auto;
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

.idea:hover .ideaActions,
.idea:focus-within .ideaActions {
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
  flex-wrap: wrap;
  gap: 12px;
  padding: 0 12px;
  font-size: 12px;
}

.dateEditor {
  flex: 0 0 auto;
}

.dateDisplay {
  background: none;
  border: 0;
  color: inherit;
  cursor: pointer;
  font: inherit;
  padding: 0;
}

.dateDisplay:focus-visible {
  outline: 2px solid rgb(var(--v-theme-primary));
  outline-offset: 2px;
}

.detailsSpacer {
  flex: 1;
}
</style>
