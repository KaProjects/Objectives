<script setup>
import {computed, ref, watch} from 'vue'
import Editable from '@/components/Editable.vue'
import {formatDate, string_to_html} from '@/utils'
import {api} from '@/services/apiClient'
import {KEY_RESULT_STATE, OBJECTIVE_STATE, TASK_STATE} from '@/constants/states'
import DialogCard from '@/dialogs/DialogCard.vue'
import AddTaskDialog from '@/dialogs/AddTaskDialog.vue'
import IconAction from '@/components/IconAction.vue'

const props = defineProps({
  modelValue: Boolean,
  kr: Object,
  kr_parent: Object,
  showLocateObjective: {type: Boolean, default: false},
})
const emit = defineEmits(['update:modelValue', 'close', 'updated', 'deleted', 'locate-objective'])
const isOpen = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})
const keyResult = ref(null)
const keyResultParent = ref(null)
const draftKeyResult = ref({
  name: '', description: '', specific: '', measurable: '', attainable: '', relevant: '', timeBound: '',
})
const taskPendingDeletionId = ref(null)
const statePendingConfirmation = ref(null)
const confirmDeleteKrDialog = ref(false)
const openAddTaskDialog = ref(false)
const isSubmitting = ref(false)
const submissionError = ref(null)
const dateInputProps = Object.freeze({density: 'compact', style: 'width: 150px'})

watch(() => props.kr, (value) => {
  keyResult.value = value ? {...value, tasks: value.tasks.map((task) => ({...task}))} : null
  keyResultParent.value = props.kr_parent ? {...props.kr_parent} : null
  if (!value) return
  draftKeyResult.value = {
    name: value.name, description: value.description, specific: value.s, measurable: value.m,
    attainable: value.a, relevant: value.r, timeBound: value.t,
  }
}, {immediate: true})

async function withSubmissionLock(action) {
  if (isSubmitting.value) return false
  isSubmitting.value = true
  submissionError.value = null
  try {
    return await action()
  } finally {
    isSubmitting.value = false
  }
}

function canEdit() {
  return keyResult.value.state === KEY_RESULT_STATE.ACTIVE && keyResultParent.value.obj_state === OBJECTIVE_STATE.ACTIVE
}

function compareTasks(a, b) {
  if (a.state === TASK_STATE.ACTIVE && b.state !== TASK_STATE.ACTIVE) return -1;
  if (a.state !== TASK_STATE.ACTIVE && b.state === TASK_STATE.ACTIVE) return 1;
  return a.id - b.id
}

async function updateKeyResult() {
  return withSubmissionLock(async () => {
    try {
      const updated = {
        name: draftKeyResult.value.name, description: draftKeyResult.value.description,
        s: draftKeyResult.value.specific, m: draftKeyResult.value.measurable,
        a: draftKeyResult.value.attainable, r: draftKeyResult.value.relevant, t: draftKeyResult.value.timeBound,
      }
      const body = await api.put('/key_result/' + keyResult.value.id, updated)
      Object.assign(keyResult.value, updated, {date_reviewed: body});
      Object.assign(keyResultParent.value, updated, {date_reviewed: body})
      emit('updated', {...keyResultParent.value})
      return true
    } catch (error) {
      submissionError.value = error.message
      return false
    }
  })
}

async function update(field, value) {
  const previousValue = draftKeyResult.value[field];
  draftKeyResult.value[field] = value;
  if (await updateKeyResult()) return true
  draftKeyResult.value[field] = previousValue
  return false
}

async function updateKeyResultDate(field, value) {
  return withSubmissionLock(async () => {
    const dates = {
      date_created: keyResult.value.date_created,
      date_reviewed: keyResult.value.date_reviewed,
      [field]: value,
    }
    try {
      const updatedDates = await api.put('/key_result/' + keyResult.value.id + '/dates', dates)
      Object.assign(keyResult.value, updatedDates)
      Object.assign(keyResultParent.value, updatedDates)
      emit('updated', {...keyResultParent.value})
      return true
    } catch (error) {
      submissionError.value = error.message
      return false
    }
  })
}

function reviewDateLabel() {
  if (keyResult.value.state === KEY_RESULT_STATE.FAILED) return 'Failed'
  if (keyResult.value.state === KEY_RESULT_STATE.COMPLETED) return 'Completed'
  return 'Reviewed'
}

async function retrieveKeyResultReviewDate() {
  const body = await api.get('/key_result/' + keyResult.value.id);
  keyResult.value.date_reviewed = body.date_reviewed;
  keyResultParent.value.date_reviewed = body.date_reviewed
}

async function updateTaskValue(task, value) {
  return withSubmissionLock(async () => {
    try {
      const body = await api.put('/task/' + task.id, {
        kr_id: keyResult.value.id,
        value,
        state: task.state
      });
      task.value = body.value;
      await retrieveKeyResultReviewDate();
      emit('updated', {...keyResultParent.value});
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

function showObjective() {
  const objectiveId = keyResult.value.objective_id ?? keyResultParent.value.objective_id
  const location = {
    objectiveId,
    valueId: keyResultParent.value.value_id,
    objectiveState: keyResultParent.value.obj_state,
  }
  closeDialog()
  emit('locate-objective', location)
}

async function addCreatedTasks(tasks) {
  keyResult.value.tasks.push(...tasks)
  keyResultParent.value.all_tasks_count += tasks.length
  try {
    await retrieveKeyResultReviewDate()
    emit('updated', {...keyResultParent.value})
  } catch (error) {
    submissionError.value = error.message
  }
}

async function updateTaskState(task, state) {
  return withSubmissionLock(async () => {
    try {
      const body = await api.put('/task/' + task.id, {kr_id: keyResult.value.id, value: task.value, state});
      if (task.state === TASK_STATE.ACTIVE && body.state !== TASK_STATE.ACTIVE) keyResultParent.value.resolved_tasks_count += 1;
      if (task.state !== TASK_STATE.ACTIVE && body.state === TASK_STATE.ACTIVE) keyResultParent.value.resolved_tasks_count -= 1;
      task.state = body.state;
      await retrieveKeyResultReviewDate();
      emit('updated', {...keyResultParent.value})
    } catch (error) {
      submissionError.value = error.message
    }
  })
}

async function deleteTask(task) {
  return withSubmissionLock(async () => {
    try {
      await api.delete('/task/' + task.id);
      taskPendingDeletionId.value = null;
      keyResult.value.tasks.splice(keyResult.value.tasks.indexOf(task), 1);
      keyResultParent.value.all_tasks_count -= 1;
      if (task.state !== TASK_STATE.ACTIVE) keyResultParent.value.resolved_tasks_count -= 1;
      await retrieveKeyResultReviewDate();
      emit('updated', {...keyResultParent.value})
    } catch (error) {
      submissionError.value = error.message
    }
  })
}

async function updateKeyResultState(state) {
  return withSubmissionLock(async () => {
    try {
      const body = await api.put('/key_result/' + keyResult.value.id + '/state', {state});
      keyResult.value.state = body;
      keyResultParent.value.state = body;
      await retrieveKeyResultReviewDate();
      emit('updated', {...keyResultParent.value});
      statePendingConfirmation.value = null
      if (body === KEY_RESULT_STATE.FAILED || body === KEY_RESULT_STATE.COMPLETED) showObjective()
    } catch (error) {
      submissionError.value = error.message
    }
  })
}

async function deleteKeyResult() {
  return withSubmissionLock(async () => {
    try {
      await api.delete('/key_result/' + keyResult.value.id)
      emit('deleted', keyResultParent.value)
      confirmDeleteKrDialog.value = false
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

      <Editable :value="draftKeyResult.name" :editable="canEdit()" :submit="(value) => update('name', value)" label="Name" hide-details>
        <template #display="{startEditing}">
          <v-card-title class="dialogTitle text-h5 grey lighten-2"
                        :role="canEdit() ? 'button' : undefined"
                        :tabindex="canEdit() ? 0 : undefined"
                        :aria-label="canEdit() ? 'Edit Key Result name' : undefined"
                        @click="startEditing"
                        @keydown.enter.prevent="startEditing"
                        @keydown.space.prevent="startEditing">
            {{ keyResult.name }}
          </v-card-title>
        </template>
      </Editable>

      <Editable :value="draftKeyResult.description" :editable="canEdit()" textarea hide-details
                :submit="(value) => update('description', value)" label="Description">
        <template #display="{startEditing}">
          <div class="v-card-text"
               :role="canEdit() ? 'button' : undefined"
               :tabindex="canEdit() ? 0 : undefined"
               :aria-label="canEdit() ? 'Edit Key Result description' : undefined"
               v-html="string_to_html(keyResult.description)"
               @click="startEditing"
               @keydown.enter.prevent="startEditing"
               @keydown.space.prevent="startEditing"/>
        </template>
      </Editable>
      <div class="keyResultDetails">
        <Editable class="dateEditor" :value="keyResult.date_created" date-picker hide-details
                  :input-props="dateInputProps"
                  :submit="(value) => updateKeyResultDate('date_created', value)" label="Created">
          <template #display="{startEditing}">
            <button type="button" class="dateDisplay" aria-label="Edit Key Result created date"
                    @click="startEditing">
              created: {{ formatDate(keyResult.date_created) }}
            </button>
          </template>
        </Editable>
        <Editable class="dateEditor" :value="keyResult.date_reviewed" date-picker hide-details
                  :input-props="dateInputProps"
                  :submit="(value) => updateKeyResultDate('date_reviewed', value)" :label="reviewDateLabel()">
          <template #display="{startEditing}">
            <button type="button" class="dateDisplay" aria-label="Edit Key Result review date"
                    @click="startEditing">
              {{ reviewDateLabel().toLowerCase() }}: {{ formatDate(keyResult.date_reviewed) }}
            </button>
          </template>
        </Editable>
        <span class="detailsSpacer"/>
        <div class="detailActions">
          <v-btn v-if="showLocateObjective" class="locateObjectiveButton" variant="plain" rounded="lg"
                 icon="mdi-target" size="small" aria-label="Show Key Result objective" @click="showObjective"/>
          <v-dialog v-model="confirmDeleteKrDialog" width="300">
            <template v-slot:activator="{ props }">
              <v-btn variant="plain" rounded="lg" icon="mdi-trash-can" size="small"
                     aria-label="Delete Key Result" v-bind="props"/>
            </template>
            <v-card>
              <v-card-title class="text-h5 grey lighten-2">
                Delete permanently?
              </v-card-title>
              <v-card-actions>
                <v-btn block :disabled="isSubmitting" @click="deleteKeyResult()">Confirm</v-btn>
              </v-card-actions>
            </v-card>
          </v-dialog>
        </div>
      </div>


      <v-divider></v-divider>

      <div v-if="keyResult.state === KEY_RESULT_STATE.ACTIVE && keyResultParent.obj_state === OBJECTIVE_STATE.ACTIVE && keyResult.s && keyResult.r"
           class="smartMarks">
        <div class="smartMark">
          <v-icon icon="mdi-check-bold" size="14"/>
          SMART
        </div>
      </div>

      <v-divider class="smartDivider"/>

      <Editable :value="draftKeyResult.measurable" :editable="canEdit()" :submit="(value) => update('measurable', value)" textarea hide-details
                label="Acceptance Criteria">
        <template #display="{startEditing}">
          <div v-if="keyResult.state === KEY_RESULT_STATE.ACTIVE && keyResultParent.obj_state === OBJECTIVE_STATE.ACTIVE"
               class="smart smartRow" role="button" tabindex="0" aria-label="Edit Acceptance Criteria"
               @click="startEditing"
               @keydown.enter.prevent="startEditing"
               @keydown.space.prevent="startEditing">
        <v-icon class="smartIcon" icon="mdi-format-list-checks" size="18"/>
        <div class="smartValue">{{ keyResult.m }}</div>
      </div>
        </template>
      </Editable>

      <v-divider class="smartDivider"/>

      <Editable :value="draftKeyResult.attainable" :editable="canEdit()" :submit="(value) => update('attainable', value)" textarea hide-details
                label="Completion Risks">
        <template #display="{startEditing}">
          <div v-if="keyResult.state === KEY_RESULT_STATE.ACTIVE && keyResultParent.obj_state === OBJECTIVE_STATE.ACTIVE"
               class="smart smartRow smartRiskRow" role="button" tabindex="0" aria-label="Edit Completion Risks"
               @click="startEditing"
               @keydown.enter.prevent="startEditing"
               @keydown.space.prevent="startEditing">
        <v-icon class="smartIcon" icon="mdi-alert-outline" size="18"/>
        <div class="smartValue">{{ keyResult.a }}</div>
      </div>
        </template>
      </Editable>

      <v-divider class="smartDivider"/>

      <Editable :value="draftKeyResult.timeBound" :editable="canEdit()" :submit="(value) => update('timeBound', value)" date-picker hide-details
                label="Deadline">
        <template #display="{startEditing}">
          <div v-if="keyResult.state === KEY_RESULT_STATE.ACTIVE && keyResultParent.obj_state === OBJECTIVE_STATE.ACTIVE"
               class="smart smartRow" role="button" tabindex="0" aria-label="Edit Deadline"
               @click="startEditing"
               @keydown.enter.prevent="startEditing"
               @keydown.space.prevent="startEditing">
        <v-icon class="smartIcon" icon="mdi-calendar" size="18"/>
        <div class="smartValue">{{ keyResult.t }}</div>
      </div>
        </template>
      </Editable>

      <v-divider></v-divider>

      <div class="tasks">
      <div v-for="task in keyResult.tasks.slice().sort(compareTasks)" :key="task.id">
        <Editable :value="task.value" :editable="canEdit()" :submit="(value) => updateTaskValue(task, value)" label="Task" hide-details>
          <template #display="{startEditing}">
            <div class="task">
              <div class="taskMain smart">
                <div class="taskState" :class="task.state">
                  <v-icon class="smartIcon" icon="mdi-close-box-outline" size="18" v-if="task.state === TASK_STATE.FAILED"/>
                  <v-icon class="smartIcon" icon="mdi-checkbox-marked-outline" size="18" v-if="task.state === TASK_STATE.FINISHED"/>
                  <v-icon class="smartIcon" icon="mdi-checkbox-blank-outline" size="18" v-if="task.state === TASK_STATE.ACTIVE"/>
                </div>
                <div class="smartValue taskValue" :class="task.state"
                     :role="canEdit() ? 'button' : undefined"
                     :tabindex="canEdit() ? 0 : undefined"
                     :aria-label="canEdit() ? `Edit task ${task.value}` : undefined"
                     v-html="string_to_html(task.value)"
                     @click="startEditing"
                     @keydown.enter.prevent="startEditing"
                     @keydown.space.prevent="startEditing"/>
              </div>

              <div class="taskActions">
          <IconAction v-if="task.state !== TASK_STATE.ACTIVE && canEdit()"
                      icon="mdi-checkbox-blank-outline" size="18" :label="`Mark ${task.value} active`"
                      @click="updateTaskState(task, TASK_STATE.ACTIVE)"/>
          <IconAction v-if="task.state !== TASK_STATE.FINISHED && canEdit()"
                      icon="mdi-checkbox-marked-outline" size="18" :label="`Mark ${task.value} finished`"
                      @click="updateTaskState(task, TASK_STATE.FINISHED)"/>
          <IconAction v-if="task.state !== TASK_STATE.FAILED && canEdit()"
                      icon="mdi-close-box-outline" size="18" :label="`Mark ${task.value} failed`"
                      @click="updateTaskState(task, TASK_STATE.FAILED)"/>

          <v-dialog
              :model-value="taskPendingDeletionId === task.id"
              @update:model-value="taskPendingDeletionId = $event ? task.id : null"
              width="300"
          >
            <template v-slot:activator="{ props }">
              <IconAction v-if="canEdit()" icon="mdi-delete-forever" size="18"
                          :label="`Delete task ${task.value}`" v-bind="props"/>
            </template>

            <v-card>
              <v-card-title class="text-h5 grey lighten-2">
                Delete Task?
              </v-card-title>
              <v-card-text>
                {{ task.value }}
              </v-card-text>
              <v-card-actions>
                <v-btn block @click="deleteTask(task)">Confirm</v-btn>
              </v-card-actions>
            </v-card>
          </v-dialog>
              </div>
            </div>
          </template>
        </Editable>
      </div>
      </div>

      <v-btn v-if="keyResult.state === KEY_RESULT_STATE.ACTIVE && keyResultParent.obj_state === OBJECTIVE_STATE.ACTIVE"
             block class="dialogAdd" color="secondary" @click="openAddTaskDialog = true">
        Add Task
      </v-btn>
      <AddTaskDialog v-if="keyResult" v-model="openAddTaskDialog" :key-result-id="keyResult.id" @created="addCreatedTasks"/>

    </DialogCard>

    <div>
      <v-dialog :model-value="statePendingConfirmation === KEY_RESULT_STATE.FAILED"
                @update:model-value="statePendingConfirmation = $event ? KEY_RESULT_STATE.FAILED : null"
                width="300"
                v-if="keyResult.state === KEY_RESULT_STATE.ACTIVE && keyResultParent.obj_state === OBJECTIVE_STATE.ACTIVE">
        <template v-slot:activator="{ props }">
          <v-btn class="dialogFail" style="width: 50%;" color="red" v-bind="props">fail</v-btn>
        </template>
        <v-card>
          <v-card-title class="text-h5 grey lighten-2">
            Fail?
          </v-card-title>
          <v-card-actions>
            <v-btn block @click="updateKeyResultState(KEY_RESULT_STATE.FAILED)">Confirm</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
      <v-dialog :model-value="statePendingConfirmation === KEY_RESULT_STATE.COMPLETED"
                @update:model-value="statePendingConfirmation = $event ? KEY_RESULT_STATE.COMPLETED : null"
                width="300"
                v-if="keyResult.state === KEY_RESULT_STATE.ACTIVE && keyResultParent.obj_state === OBJECTIVE_STATE.ACTIVE">
        <template v-slot:activator="{ props }">
          <v-btn class="dialogSuccess" style="width: 50%;" color="green" v-bind="props">complete</v-btn>
        </template>
        <v-card>
          <v-card-title class="text-h5 grey lighten-2">
            Complete?
          </v-card-title>
          <v-card-actions>
            <v-btn block @click="updateKeyResultState(KEY_RESULT_STATE.COMPLETED)">Confirm</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
      <v-dialog :model-value="statePendingConfirmation === KEY_RESULT_STATE.ACTIVE"
                @update:model-value="statePendingConfirmation = $event ? KEY_RESULT_STATE.ACTIVE : null"
                width="300"
                v-if="keyResult.state !== KEY_RESULT_STATE.ACTIVE && keyResultParent.obj_state === OBJECTIVE_STATE.ACTIVE">
        <template v-slot:activator="{ props }">
          <v-btn class="dialogActivate" style="width: 100%;" color="blue" v-bind="props">activate</v-btn>
        </template>
        <v-card>
          <v-card-title class="text-h5 grey lighten-2">
            Activate?
          </v-card-title>
          <v-card-actions>
            <v-btn block @click="updateKeyResultState(KEY_RESULT_STATE.ACTIVE)">Confirm</v-btn>
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

.task {
  align-items: start;
  background-color: rgb(var(--v-theme-surface));
  color: rgb(var(--v-theme-on-surface));
  display: flex;
}

.tasks {
  max-height: 252px;
  overflow-y: auto;
}

.taskMain {
  flex: 1;
}

.task .smartIcon {
  margin-top: -3px;
}

.taskState.failed,
.taskValue.failed {
  color: rgba(246, 28, 28, 0.40);
  text-decoration: line-through;
}

.taskState.finished,
.taskValue.finished {
  color: rgba(74, 194, 6, 0.35);
  text-decoration: line-through;
}

.taskActions {
  display: none;
  gap: 4px;
  margin: 3px;
}

.task:hover .taskActions,
.task:focus-within .taskActions {
  display: flex;
}

@media (max-width: 600px) {
  .taskActions {
    display: flex;
  }
}

.smart {
  align-items: start;
  display: grid;
  grid-template-columns: 25px minmax(0, 1fr);
  padding-left: 5px;
}

.smartValue {
  display: inline;
  white-space: pre-wrap;
}

.smartIcon {
  margin-left: 3px;
  margin-top: 3px;
  opacity: var(--v-medium-emphasis-opacity);
}

.smartRiskRow .smartIcon {
  color: #b87500;
  opacity: 1;
}

.smartDivider {
  margin: 4px 10px;
  opacity: 0.35;
}

.smartMarks {
  display: flex;
  gap: 12px;
  margin-bottom: -6px;
  padding: 4px 10px 4px 11px;
}

.smartMark {
  align-items: center;
  color: #017901;
  display: flex;
  font-size: 14px;
  gap: 4px;
}

.keyResultDetails {
  display: flex;
  align-items: center;
  flex-wrap: nowrap;
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
  min-width: 0;
}

.detailActions {
  align-items: center;
  display: flex;
  flex: 0 0 auto;
}

@media (max-width: 600px) {
  .keyResultDetails {
    font-size: 10px;
    gap: 4px;
    padding: 0 6px;
  }

  .dateDisplay {
    white-space: nowrap;
  }

  .detailActions :deep(.v-btn) {
    height: 28px;
    min-width: 28px;
    padding: 0;
    width: 28px;
  }
}
</style>
