<script setup>
import {computed, ref, watch} from 'vue'
import Editable from '@/components/Editable.vue'
import {formatDate, string_to_html} from '@/utils'
import {api} from '@/services/apiClient'
import {setError} from '@/state/appState'
import {KEY_RESULT_STATE, OBJECTIVE_STATE, TASK_STATE} from '@/constants/states'
import DialogCard from '@/dialogs/DialogCard.vue'
import AddTaskDialog from '@/dialogs/AddTaskDialog.vue'

const props = defineProps({
  modelValue: Boolean,
  kr: Object,
  kr_parent: Object,
})
const emit = defineEmits(['update:modelValue', 'close', 'updated', 'deleted'])
const isOpen = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})
const kr = ref(null)
const kr_parent = ref(null)
const draftKeyResult = ref({
  name: '', description: '', specific: '', measurable: '', attainable: '', relevant: '', timeBound: '',
})
const selectedTaskId = ref(null)
const taskPendingDeletionId = ref(null)
const statePendingConfirmation = ref(null)
const confirmDeleteKrDialog = ref(false)
const openAddTaskDialog = ref(false)
const isSubmitting = ref(false)
const submissionError = ref(null)

watch(() => props.kr, (value) => {
  kr.value = value ? {...value, tasks: value.tasks.map((task) => ({...task}))} : null
  kr_parent.value = props.kr_parent ? {...props.kr_parent} : null
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
  return kr.value.state === KEY_RESULT_STATE.ACTIVE && kr_parent.value.obj_state === OBJECTIVE_STATE.ACTIVE
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
      const body = await api.put('/key_result/' + kr.value.id, updated)
      Object.assign(kr.value, updated, {date_reviewed: body});
      Object.assign(kr_parent.value, updated, {date_reviewed: body})
      emit('updated', {...kr_parent.value})
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

async function retrieveKeyResultReviewDate() {
  const body = await api.get('/key_result/' + kr.value.id);
  kr.value.date_reviewed = body.date_reviewed;
  kr_parent.value.date_reviewed = body.date_reviewed
}

async function updateTaskValue(task, value) {
  return withSubmissionLock(async () => {
    try {
      const body = await api.put('/task/' + task.id, {
        kr_id: kr.value.id,
        value,
        state: task.state
      });
      task.value = body.value;
      await retrieveKeyResultReviewDate();
      emit('updated', {...kr_parent.value});
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

async function addCreatedTasks(tasks) {
  kr.value.tasks.push(...tasks)
  kr_parent.value.all_tasks_count += tasks.length
  try {
    await retrieveKeyResultReviewDate()
    emit('updated', {...kr_parent.value})
  } catch (error) {
    submissionError.value = error.message
  }
}

async function updateTaskState(task, state) {
  return withSubmissionLock(async () => {
    try {
      const body = await api.put('/task/' + task.id, {kr_id: kr.value.id, value: task.value, state});
      if (task.state === TASK_STATE.ACTIVE && body.state !== TASK_STATE.ACTIVE) kr_parent.value.resolved_tasks_count += 1;
      if (task.state !== TASK_STATE.ACTIVE && body.state === TASK_STATE.ACTIVE) kr_parent.value.resolved_tasks_count -= 1;
      task.state = body.state;
      await retrieveKeyResultReviewDate();
      emit('updated', {...kr_parent.value})
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
      kr.value.tasks.splice(kr.value.tasks.indexOf(task), 1);
      kr_parent.value.all_tasks_count -= 1;
      if (task.state !== TASK_STATE.ACTIVE) kr_parent.value.resolved_tasks_count -= 1;
      await retrieveKeyResultReviewDate();
      emit('updated', {...kr_parent.value})
    } catch (error) {
      submissionError.value = error.message
    }
  })
}

async function updateKeyResultState(state) {
  return withSubmissionLock(async () => {
    try {
      const body = await api.put('/key_result/' + kr.value.id + '/state', {state});
      kr.value.state = body;
      kr_parent.value.state = body;
      await retrieveKeyResultReviewDate();
      emit('updated', {...kr_parent.value});
      statePendingConfirmation.value = null
    } catch (error) {
      submissionError.value = error.message
    }
  })
}

function deleteKeyResult() {
  emit('deleted', kr_parent.value);
  confirmDeleteKrDialog.value = false;
  closeDialog()
}
</script>

<template>
  <v-dialog v-model="isOpen" width="600">
    <DialogCard :error="submissionError">

      <Editable :value="draftKeyResult.name" :editable="canEdit()" :submit="(value) => update('name', value)" label="Name" hide-details>
        <template #display="{startEditing}">
          <v-card-title @click="startEditing" class="dialogTitle text-h5 grey lighten-2">
            {{ kr.name }}
          </v-card-title>
        </template>
      </Editable>

      <Editable :value="draftKeyResult.description" :editable="canEdit()" textarea hide-details
                :submit="(value) => update('description', value)" label="Description">
        <template #display="{startEditing}">
          <v-card-text v-html="string_to_html(kr.description)" @click="startEditing"/>
        </template>
      </Editable>
      <div class="keyResultDetails">
        <span>created: {{ formatDate(kr.date_created) }}</span>
        <span v-if="kr.state === KEY_RESULT_STATE.ACTIVE">reviewed: {{ formatDate(kr.date_reviewed) }}</span>
        <span v-if="kr.state === KEY_RESULT_STATE.FAILED">failed: {{ formatDate(kr.date_reviewed) }}</span>
        <span v-if="kr.state === KEY_RESULT_STATE.COMPLETED">completed: {{ formatDate(kr.date_reviewed) }}</span>
        <span class="detailsSpacer"/>
        <v-dialog v-model="confirmDeleteKrDialog" width="300">
          <template v-slot:activator="{ props }">
            <v-btn variant="plain" rounded="lg" icon="mdi-trash-can" size="small" v-bind="props"/>
          </template>
          <v-card>
            <v-card-title class="text-h5 grey lighten-2">
              Delete permanently?
            </v-card-title>
            <v-card-actions>
              <v-btn block @click="deleteKeyResult()">Confirm</v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>
      </div>


      <v-divider></v-divider>

      <div v-if="kr.state === KEY_RESULT_STATE.ACTIVE && kr_parent.obj_state === OBJECTIVE_STATE.ACTIVE && kr.s && kr.r"
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
          <div v-if="kr.state === KEY_RESULT_STATE.ACTIVE && kr_parent.obj_state === OBJECTIVE_STATE.ACTIVE"
           @click="startEditing"
           class="smart smartRow">
        <v-icon class="smartIcon" icon="mdi-format-list-checks" size="18"/>
        <div class="smartValue">{{ kr.m }}</div>
      </div>
        </template>
      </Editable>

      <v-divider class="smartDivider"/>

      <Editable :value="draftKeyResult.attainable" :editable="canEdit()" :submit="(value) => update('attainable', value)" textarea hide-details
                label="Completion Risks">
        <template #display="{startEditing}">
          <div v-if="kr.state === KEY_RESULT_STATE.ACTIVE && kr_parent.obj_state === OBJECTIVE_STATE.ACTIVE"
           @click="startEditing"
           class="smart smartRow smartRiskRow">
        <v-icon class="smartIcon" icon="mdi-alert-outline" size="18"/>
        <div class="smartValue">{{ kr.a }}</div>
      </div>
        </template>
      </Editable>

      <v-divider class="smartDivider"/>

      <Editable :value="draftKeyResult.timeBound" :editable="canEdit()" :submit="(value) => update('timeBound', value)" hide-details
                label="Deadline">
        <template #display="{startEditing}">
          <div v-if="kr.state === KEY_RESULT_STATE.ACTIVE && kr_parent.obj_state === OBJECTIVE_STATE.ACTIVE"
           @click="startEditing"
           class="smart smartRow">
        <v-icon class="smartIcon" icon="mdi-calendar" size="18"/>
        <div class="smartValue">{{ kr.t }}</div>
      </div>
        </template>
      </Editable>

      <v-divider></v-divider>

      <div class="tasks">
      <div v-for="task in kr.tasks.slice().sort(compareTasks)" :key="task.id">
        <Editable :value="task.value" :editable="canEdit()" :submit="(value) => updateTaskValue(task, value)" label="Task" hide-details>
          <template #display="{startEditing}">
            <div class="task">
              <div class="taskMain smart">
                <div class="taskState" :class="task.state">
                  <v-icon class="smartIcon" icon="mdi-close-box-outline" size="18" v-if="task.state === TASK_STATE.FAILED"/>
                  <v-icon class="smartIcon" icon="mdi-checkbox-marked-outline" size="18" v-if="task.state === TASK_STATE.FINISHED"/>
                  <v-icon class="smartIcon" icon="mdi-checkbox-blank-outline" size="18" v-if="task.state === TASK_STATE.ACTIVE"/>
                </div>
                <div class="smartValue taskValue" v-html="string_to_html(task.value)" @click="startEditing" :class="task.state"/>
              </div>

              <div class="taskActions">
          <v-icon icon="mdi-checkbox-blank-outline" size="18"
                  v-if="task.state !== TASK_STATE.ACTIVE && canEdit()"
                  @click="updateTaskState(task, TASK_STATE.ACTIVE)"/>
          <v-icon icon="mdi-checkbox-marked-outline" size="18"
                  v-if="task.state !== TASK_STATE.FINISHED && canEdit()"
                  @click="updateTaskState(task, TASK_STATE.FINISHED)"/>
          <v-icon icon="mdi-close-box-outline" size="18"
                  v-if="task.state !== TASK_STATE.FAILED && canEdit()"
                  @click="updateTaskState(task, TASK_STATE.FAILED)"/>

          <v-dialog
              :model-value="taskPendingDeletionId === task.id"
              @update:model-value="taskPendingDeletionId = $event ? task.id : null"
              width="300"
          >
            <template v-slot:activator="{ props }">
              <v-icon icon="mdi-delete-forever" size="18" v-bind="props"
                      v-if="canEdit()"/>
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

      <v-btn v-if="kr.state === KEY_RESULT_STATE.ACTIVE && kr_parent.obj_state === OBJECTIVE_STATE.ACTIVE"
             block class="dialogAdd" color="secondary" @click="openAddTaskDialog = true">
        Add Task
      </v-btn>
      <AddTaskDialog v-if="kr" v-model="openAddTaskDialog" :key-result-id="kr.id" @created="addCreatedTasks"/>

    </DialogCard>

    <div>
      <v-dialog :model-value="statePendingConfirmation === KEY_RESULT_STATE.FAILED"
                @update:model-value="statePendingConfirmation = $event ? KEY_RESULT_STATE.FAILED : null"
                width="300"
                v-if="kr.state === KEY_RESULT_STATE.ACTIVE && kr_parent.obj_state === OBJECTIVE_STATE.ACTIVE">
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
                v-if="kr.state === KEY_RESULT_STATE.ACTIVE && kr_parent.obj_state === OBJECTIVE_STATE.ACTIVE">
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
                v-if="kr.state !== KEY_RESULT_STATE.ACTIVE && kr_parent.obj_state === OBJECTIVE_STATE.ACTIVE">
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

.task:hover .taskActions {
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
  gap: 12px;
  padding: 0 12px;
  font-size: 12px;
}

.detailsSpacer {
  flex: 1;
}
</style>
