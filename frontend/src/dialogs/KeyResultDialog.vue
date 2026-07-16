<script setup>
import {computed, ref, watch} from 'vue'
import Editable from '@/components/Editable.vue'
import {formatDate, string_to_html} from '@/utils'
import {api} from '@/services/apiClient'
import {setError} from '@/state/appState'
import {KEY_RESULT_STATE, OBJECTIVE_STATE, TASK_STATE} from '@/constants/states'
import DialogCard from '@/dialogs/DialogCard.vue'

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
const editingField = ref(null)
const isAddingTask = ref(false)
const editingTaskId = ref(null)
const editingValue = ref('')
const selectedTaskId = ref(null)
const taskPendingDeletionId = ref(null)
const statePendingConfirmation = ref(null)
const showSmart = ref(false)
const confirmDeleteKrDialog = ref(false)
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

function stopEditing() {
  editingField.value = null;
  isAddingTask.value = false;
  editingTaskId.value = null
}

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

function validateSmart(value) {
  return value !== null && value !== undefined && value.length > 0 && !value.startsWith('[!!!]')
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
      kr.value.is_smart = [kr.value.s, kr.value.m, kr.value.a, kr.value.r, kr.value.t].every(validateSmart);
      kr_parent.value.is_smart = kr.value.is_smart
      emit('updated', {...kr_parent.value})
      return true
    } catch (error) {
      submissionError.value = error.message
      return false
    }
  })
}

function startEditing(field) {
  if (!canEdit()) return;
  stopEditing();
  editingValue.value = draftKeyResult.value[field];
  editingField.value = field
}

async function update(field) {
  const previousValue = draftKeyResult.value[field];
  draftKeyResult.value[field] = editingValue.value;
  if (await updateKeyResult()) editingField.value = null; else draftKeyResult.value[field] = previousValue
}

function startAddingTask() {
  if (!canEdit()) return;
  stopEditing();
  editingValue.value = '';
  isAddingTask.value = true
}

function startEditingTask(task) {
  if (!canEdit()) return;
  stopEditing();
  editingValue.value = task.value;
  editingTaskId.value = task.id
}

async function retrieveKeyResultReviewDate() {
  const body = await api.get('/key_result/' + kr.value.id);
  kr.value.date_reviewed = body.date_reviewed;
  kr_parent.value.date_reviewed = body.date_reviewed
}

async function updateTaskValue(task) {
  return withSubmissionLock(async () => {
    try {
      const body = await api.put('/task/' + task.id, {
        kr_id: kr.value.id,
        value: editingValue.value,
        state: task.state
      });
      task.value = body.value;
      await retrieveKeyResultReviewDate();
      emit('updated', {...kr_parent.value});
      stopEditing()
    } catch (error) {
      submissionError.value = error.message
    }
  })
}

function closeDialog() {
  stopEditing();
  showSmart.value = false;
  isOpen.value = false;
  emit('close')
}

async function addTask() {
  return withSubmissionLock(async () => {
    try {
      const body = await api.post('/task', {kr_id: kr.value.id, value: editingValue.value});
      kr.value.tasks.push(body);
      kr_parent.value.all_tasks_count += 1;
      await retrieveKeyResultReviewDate();
      emit('updated', {...kr_parent.value});
      isAddingTask.value = false
    } catch (error) {
      submissionError.value = error.message
    }
  })
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
  <v-dialog v-model="isOpen" persistent width="600">
    <DialogCard :error="submissionError">

      <Editable v-if="editingField === 'name'" :cancel="stopEditing" :submit="update" index="name">
        <v-text-field @keydown.enter="update('name')" @keydown.esc="stopEditing"
                      v-model="editingValue"
                      label="Name"
        ></v-text-field>
      </Editable>
      <div v-else class="datesInfo">
        <v-card-title @click="startEditing('name')" class="text-h5 grey lighten-2">
          {{ kr.name }}
        </v-card-title>
        <div class="datesInfoChild" style="top: 0;">created: {{ formatDate(kr.date_created) }}</div>
        <div class="datesInfoChild" style="top: 15px;" v-if="kr.state === KEY_RESULT_STATE.ACTIVE">reviewed:
          {{ formatDate(kr.date_reviewed) }}
        </div>
        <div class="datesInfoChild" style="top: 15px;" v-if="kr.state === KEY_RESULT_STATE.FAILED">failed:
          {{ formatDate(kr.date_reviewed) }}
        </div>
        <div class="datesInfoChild" style="top: 15px;" v-if="kr.state === KEY_RESULT_STATE.COMPLETED">completed:
          {{ formatDate(kr.date_reviewed) }}
        </div>
      </div>

      <Editable v-if="editingField === 'description'" :cancel="stopEditing" :submit="update" index="description">
        <v-textarea @keydown.esc="stopEditing"
                    v-model="editingValue"
                    label="Description"
        ></v-textarea>
      </Editable>
      <div v-else>
        <v-card-text v-html="string_to_html(kr.description)" @click="startEditing('description')"/>
        <v-dialog v-model="confirmDeleteKrDialog" width="300">
          <template v-slot:activator="{ props }">
            <v-btn style="bottom: -10px; right: -10px; position: absolute;" variant="plain"
                   icon="mdi-trash-can" v-bind="props"/>
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

      <div
          v-if="kr.state === KEY_RESULT_STATE.ACTIVE && kr_parent.obj_state === OBJECTIVE_STATE.ACTIVE && kr.is_smart && !showSmart"
          class="smartMark"
          @click="showSmart = true">
        <v-icon style="vertical-align: top;" icon="mdi-check-bold"/>
        SMART
      </div>

      <Editable v-if="editingField === 'specific'" :cancel="stopEditing" :submit="update" index="specific">
        <v-text-field @keydown.enter="update('specific')" @keydown.esc="stopEditing"
                      v-model="editingValue"
                      label="Specific"
                      hint="The goal should have a clear, highly-specific endpoint. If your goal is too vague, it won’t be SMART."
        ></v-text-field>
      </Editable>
      <div v-else
           v-if="kr.state === KEY_RESULT_STATE.ACTIVE && kr_parent.obj_state === OBJECTIVE_STATE.ACTIVE && (!kr.is_smart || showSmart)"
           @click="startEditing('specific')"
           class="smart" :class="validateSmart(kr.s).toString()">
        <div class="smartLabel">Specific:</div>
        <div class="smartValue">{{ kr.s }}</div>
      </div>

      <Editable v-if="editingField === 'measurable'" :cancel="stopEditing" :submit="update" index="measurable">
        <v-text-field @keydown.enter="update('measurable')" @keydown.esc="stopEditing"
                      v-model="editingValue"
                      label="Measurable"
                      hint="You need to be able to accurately track your progress, so you can judge when a goal will be met."
        ></v-text-field>
      </Editable>
      <div v-else
           v-if="kr.state === KEY_RESULT_STATE.ACTIVE && kr_parent.obj_state === OBJECTIVE_STATE.ACTIVE && (!kr.is_smart || showSmart)"
           @click="startEditing('measurable')"
           class="smart" :class="validateSmart(kr.m).toString()">
        <div class="smartLabel">Measurable:</div>
        <div class="smartValue">{{ kr.m }}</div>
      </div>

      <Editable v-if="editingField === 'attainable'" :cancel="stopEditing" :submit="update" index="attainable">
        <v-text-field @keydown.enter="update('attainable')" @keydown.esc="stopEditing"
                      v-model="editingValue"
                      label="Attainable"
                      hint="Of course, setting a goal that’s too ambitious will see you struggle to achieve it. This will sap at your motivation, both now and in the future."
        ></v-text-field>
      </Editable>
      <div v-else
           v-if="kr.state === KEY_RESULT_STATE.ACTIVE && kr_parent.obj_state === OBJECTIVE_STATE.ACTIVE && (!kr.is_smart || showSmart)"
           @click="startEditing('attainable')"
           class="smart" :class="validateSmart(kr.a).toString()">
        <div class="smartLabel">Attainable:</div>
        <div class="smartValue">{{ kr.a }}</div>
      </div>

      <Editable v-if="editingField === 'relevant'" :cancel="stopEditing" :submit="update" index="relevant">
        <v-text-field @keydown.enter="update('relevant')" @keydown.esc="stopEditing"
                      v-model="editingValue"
                      label="Relevant"
                      hint="The goal you pick should be pertinent to your chosen field, or should benefit you directly."
        ></v-text-field>
      </Editable>
      <div v-else
           v-if="kr.state === KEY_RESULT_STATE.ACTIVE && kr_parent.obj_state === OBJECTIVE_STATE.ACTIVE && (!kr.is_smart || showSmart)"
           @click="startEditing('relevant')"
           class="smart" :class="validateSmart(kr.r).toString()">
        <div class="smartLabel">Relevant:</div>
        <div class="smartValue">{{ kr.r }}</div>
      </div>

      <Editable v-if="editingField === 'timeBound'" :cancel="stopEditing" :submit="update" index="timeBound">
        <v-text-field @keydown.enter="update('timeBound')" @keydown.esc="stopEditing"
                      v-model="editingValue"
                      label="Time-Bound"
                      hint="Finally, setting a timeframe for your goal helps quantify it further, and helps keep your focus on track."
        ></v-text-field>
      </Editable>
      <div v-else
           v-if="kr.state === KEY_RESULT_STATE.ACTIVE && kr_parent.obj_state === OBJECTIVE_STATE.ACTIVE && (!kr.is_smart || showSmart)"
           @click="startEditing('timeBound')"
           class="smart" :class="validateSmart(kr.t).toString()">
        <div class="smartLabel">Time-Bound:</div>
        <div class="smartValue">{{ kr.t }}</div>
      </div>

      <v-divider></v-divider>

      <div v-for="task in kr.tasks.slice().sort(compareTasks)" :key="task.id">
        <Editable v-if="editingTaskId === task.id" :cancel="stopEditing" :submit="updateTaskValue"
                  :index="task">
          <v-text-field @keydown.enter="updateTaskValue(task)" @keydown.esc="stopEditing"
                        v-model="editingValue"
                        label="Task"
          ></v-text-field>
        </Editable>
        <div v-else class="task"
             @mouseover="selectedTaskId = task.id"
             @mouseleave="selectedTaskId = null">
          <div :class="task.state">
            <v-icon icon="mdi-close-box-outline" large v-if="task.state === TASK_STATE.FAILED"/>
            <v-icon icon="mdi-checkbox-marked-outline" large v-if="task.state === TASK_STATE.FINISHED"/>
            <v-icon icon="mdi-checkbox-blank-outline" large v-if="task.state === TASK_STATE.ACTIVE"/>
          </div>
          <div v-html="string_to_html(task.value)" @click="startEditingTask(task)" :class="task.state"
               style="display: inline; padding-left: 3px; flex: 25;"/>

          <v-icon style="flex: 1;" icon="mdi-checkbox-blank-outline" large
                  v-if="selectedTaskId === task.id && task.state !== TASK_STATE.ACTIVE && kr.state === KEY_RESULT_STATE.ACTIVE && kr_parent.obj_state === OBJECTIVE_STATE.ACTIVE"
                  @click="updateTaskState(task, TASK_STATE.ACTIVE)"/>
          <v-icon style="flex: 1;" icon="mdi-checkbox-marked-outline" large
                  v-if="selectedTaskId === task.id && task.state !== TASK_STATE.FINISHED && kr.state === KEY_RESULT_STATE.ACTIVE && kr_parent.obj_state === OBJECTIVE_STATE.ACTIVE"
                  @click="updateTaskState(task, TASK_STATE.FINISHED)"/>
          <v-icon style="flex: 1;" icon="mdi-close-box-outline" large
                  v-if="selectedTaskId === task.id && task.state !== TASK_STATE.FAILED && kr.state === KEY_RESULT_STATE.ACTIVE && kr_parent.obj_state === OBJECTIVE_STATE.ACTIVE"
                  @click="updateTaskState(task, TASK_STATE.FAILED)"/>

          <v-dialog
              :model-value="taskPendingDeletionId === task.id"
              @update:model-value="taskPendingDeletionId = $event ? task.id : null"
              width="300"
          >
            <template v-slot:activator="{ props }">
              <v-icon style="flex: 1;" icon="mdi-delete-forever" large v-bind="props"
                      v-if="selectedTaskId === task.id && kr.state === KEY_RESULT_STATE.ACTIVE && kr_parent.obj_state === OBJECTIVE_STATE.ACTIVE"/>
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

      <Editable v-if="isAddingTask" :cancel="stopEditing" :submit="addTask">
        <v-text-field @keydown.enter="addTask" @keydown.esc="stopEditing"
                      v-model="editingValue"
                      label="Add Task"
        ></v-text-field>
      </Editable>
      <v-btn v-else v-if="kr.state === KEY_RESULT_STATE.ACTIVE && kr_parent.obj_state === OBJECTIVE_STATE.ACTIVE"
             class="dialogAdd"
             color="secondary" @click="startAddingTask">
        Add Task
      </v-btn>

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
.task {
  display: flex;
  background-color: rgb(var(--v-theme-surface));
  color: rgb(var(--v-theme-on-surface));
}

.task:hover {
  background-color: rgb(var(--v-theme-surface-variant));
}

.task > div.failed {
  color: rgba(246, 28, 28, 0.40);
  text-decoration: line-through;
}

.task > div.finished {
  color: rgba(74, 194, 6, 0.35);
  text-decoration: line-through;
}

.smart {
  display: flex;
  padding-left: 5px;
}

.smart.false {
  color: #ff0000;
}

.smart.true {

}

.smartLabel {
  min-width: 95px;
}

.smartValue {
  display: inline;
}

.smartMark {
  padding-left: 10px;
  color: #017901;
  font-weight: normal;
}

.smartMark:hover {
  font-weight: bold;
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
