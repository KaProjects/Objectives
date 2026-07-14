<script setup>
import {ref, watch} from 'vue'
import Editable from '@/components/Editable.vue'
import {string_to_html} from '@/utils'
import {api} from '@/services/apiClient'

const props = defineProps({kr: Object, kr_parent: Object, delete: Function})
const emit = defineEmits(['close'])
const kr = ref(null)
const kr_parent = ref(null)
const values = ref([null, null, null, null, null, null, null, ''])
const editing = ref([false, false, false, false, false, false, false, false, []])
const editingValue = ref('')
const selectedTask = ref(-1)
const confirmDeletionDialogs = ref([])
const confirmStateDialogs = ref([false, false, false])
const showSmart = ref(false)
const confirmDeleteKrDialog = ref(false)

watch(() => props.kr, (value) => {
  kr.value = value; kr_parent.value = props.kr_parent
  if (!value) return
  values.value.splice(0, 7, value.name, value.description, value.s, value.m, value.a, value.r, value.t)
}, {immediate: true})

function stopEditing() { editing.value = [false, false, false, false, false, false, false, false, []] }
function canEdit() { return kr.value.state === 'active' && kr_parent.value.obj_state === 'active' }
function validateSmart(value) { return value !== null && value !== undefined && value.length > 0 && !value.startsWith('[!!!]') }
function compareTasks(a, b) { if (a.state === 'active' && b.state !== 'active') return -1; if (a.state !== 'active' && b.state === 'active') return 1; return a.id - b.id }
async function updateKeyResult() {
  const updated = {name: values.value[0], description: values.value[1], s: values.value[2], m: values.value[3], a: values.value[4], r: values.value[5], t: values.value[6]}
  const body = await api.put('/key_result/' + kr.value.id, updated)
  Object.assign(kr.value, updated, {date_reviewed: body}); Object.assign(kr_parent.value, {name: kr.value.name, date_reviewed: body})
  kr.value.is_smart = [kr.value.s, kr.value.m, kr.value.a, kr.value.r, kr.value.t].every(validateSmart); kr_parent.value.is_smart = kr.value.is_smart
}
function startEditing(index) { if (!canEdit()) return; stopEditing(); editingValue.value = values.value[index]; editing.value[index] = true }
function update(index) { values.value[index] = editingValue.value; editing.value[index] = false; updateKeyResult() }
function startEditingTask(task) { if (!canEdit()) return; stopEditing(); editingValue.value = task.value; editing.value[8][kr.value.tasks.slice().sort(compareTasks).indexOf(task)] = true }
async function retrieveKeyResultReviewDate() { const body = await api.get('/key_result/' + kr.value.id); kr.value.date_reviewed = body.date_reviewed; kr_parent.value.date_reviewed = body.date_reviewed }
async function updateTaskValue(task) { const body = await api.put('/task/' + task.id, {kr_id: kr.value.id, value: editingValue.value, state: task.state}); task.value = body.value; await retrieveKeyResultReviewDate(); stopEditing() }
function closeDialog() { stopEditing(); showSmart.value = false; emit('close') }
async function addTask() { const body = await api.post('/task', {kr_id: kr.value.id, value: editingValue.value}); kr.value.tasks.push(body); kr_parent.value.all_tasks_count += 1; await retrieveKeyResultReviewDate(); editing.value[7] = false }
async function updateTaskState(task, state) { const body = await api.put('/task/' + task.id, {kr_id: kr.value.id, value: task.value, state}); if (task.state === 'active' && body.state !== 'active') kr_parent.value.resolved_tasks_count += 1; if (task.state !== 'active' && body.state === 'active') kr_parent.value.resolved_tasks_count -= 1; task.state = body.state; await retrieveKeyResultReviewDate() }
async function deleteTask(task) { await api.delete('/task/' + task.id); confirmDeletionDialogs.value[kr.value.tasks.slice().sort(compareTasks).indexOf(task)] = false; kr.value.tasks.splice(kr.value.tasks.indexOf(task), 1); kr_parent.value.all_tasks_count -= 1; if (task.state !== 'active') kr_parent.value.resolved_tasks_count -= 1; await retrieveKeyResultReviewDate() }
async function updateKeyResultState(index) { const body = await api.put('/key_result/' + kr.value.id + '/state', {state: ['failed', 'completed', 'active'][index]}); kr.value.state = body; kr_parent.value.state = body; await retrieveKeyResultReviewDate(); confirmStateDialogs.value[index] = false }
function deleteKeyResult() { props.delete(kr_parent.value); confirmDeleteKrDialog.value = false; closeDialog() }
</script>

<template>
  <v-dialog persistent width="600">
    <v-card>

      <Editable v-if="editing[0]" :cancel="stopEditing" :submit="update" :index=0>
        <v-text-field @keydown.enter="update(0)" @keydown.esc="stopEditing"
                      v-model="editingValue"
                      label="Name"
        ></v-text-field>
      </Editable>
      <div v-else class="datesInfo">
        <v-card-title @click="startEditing(0)" class="text-h5 grey lighten-2">
          {{kr.name}}
        </v-card-title>
        <div class="datesInfoChild" style="top: 0;">created: {{kr.date_created}}</div>
        <div class="datesInfoChild" style="top: 15px;" v-if="kr.state==='active'">reviewed: {{kr.date_reviewed}}</div>
        <div class="datesInfoChild" style="top: 15px;" v-if="kr.state==='failed'">failed: {{kr.date_reviewed}}</div>
        <div class="datesInfoChild" style="top: 15px;" v-if="kr.state==='completed'">completed: {{kr.date_reviewed}}</div>
      </div>

      <Editable v-if="editing[1]" :cancel="stopEditing" :submit="update" :index=1>
        <v-textarea @keydown.esc="stopEditing"
                    v-model="editingValue"
                    label="Description"
        ></v-textarea>
      </Editable>
      <div v-else>
        <v-card-text v-html="string_to_html(kr.description)" @click="startEditing(1)"/>
        <v-dialog v-model="confirmDeleteKrDialog" width="300">
          <template v-slot:activator="{ props }">
            <v-btn style="bottom: -10px; right: -10px; position: absolute;" variant="plain" icon="mdi-trash-can" v-bind="props"/>
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

      <div v-if="kr.state === 'active' && kr_parent.obj_state === 'active' && kr.is_smart && !showSmart"
           class="smartMark"
           @click="showSmart = true">
        <v-icon style="vertical-align: top;" icon="mdi-check-bold" />
        SMART
      </div>

      <Editable v-if="editing[2]" :cancel="stopEditing" :submit="update" :index=2>
        <v-text-field @keydown.enter="update(2)" @keydown.esc="stopEditing"
                      v-model="editingValue"
                      label="Specific"
                      hint="The goal should have a clear, highly-specific endpoint. If your goal is too vague, it won’t be SMART."
        ></v-text-field>
      </Editable>
      <div v-else v-if="kr.state === 'active' && kr_parent.obj_state === 'active' && (!kr.is_smart || showSmart)"
           @click="startEditing(2)"
           class="smart" :class="validateSmart(kr.s).toString()">
        <div class="smartLabel">Specific:</div>
        <div class="smartValue">{{kr.s}}</div>
      </div>

      <Editable v-if="editing[3]" :cancel="stopEditing" :submit="update" :index=3>
        <v-text-field @keydown.enter="update(3)" @keydown.esc="stopEditing"
                      v-model="editingValue"
                      label="Measurable"
                      hint="You need to be able to accurately track your progress, so you can judge when a goal will be met."
        ></v-text-field>
      </Editable>
      <div v-else v-if="kr.state === 'active' && kr_parent.obj_state === 'active' && (!kr.is_smart || showSmart)"
           @click="startEditing(3)"
           class="smart" :class="validateSmart(kr.m).toString()">
        <div class="smartLabel">Measurable:</div>
        <div class="smartValue">{{kr.m}}</div>
      </div>

      <Editable v-if="editing[4]" :cancel="stopEditing" :submit="update" :index=4>
        <v-text-field @keydown.enter="update(4)" @keydown.esc="stopEditing"
                      v-model="editingValue"
                      label="Attainable"
                      hint="Of course, setting a goal that’s too ambitious will see you struggle to achieve it. This will sap at your motivation, both now and in the future."
        ></v-text-field>
      </Editable>
      <div v-else v-if="kr.state === 'active' && kr_parent.obj_state === 'active' && (!kr.is_smart || showSmart)"
           @click="startEditing(4)"
           class="smart" :class="validateSmart(kr.a).toString()">
        <div class="smartLabel">Attainable:</div>
        <div class="smartValue">{{kr.a}}</div>
      </div>

      <Editable v-if="editing[5]" :cancel="stopEditing" :submit="update" :index=5>
        <v-text-field @keydown.enter="update(5)" @keydown.esc="stopEditing"
                      v-model="editingValue"
                      label="Relevant"
                      hint="The goal you pick should be pertinent to your chosen field, or should benefit you directly."
        ></v-text-field>
      </Editable>
      <div v-else v-if="kr.state === 'active' && kr_parent.obj_state === 'active' && (!kr.is_smart || showSmart)"
           @click="startEditing(5)"
           class="smart" :class="validateSmart(kr.r).toString()">
        <div class="smartLabel">Relevant:</div>
        <div class="smartValue">{{kr.r}}</div>
      </div>

      <Editable v-if="editing[6]" :cancel="stopEditing" :submit="update" :index=6>
        <v-text-field @keydown.enter="update(6)" @keydown.esc="stopEditing"
                      v-model="editingValue"
                      label="Time-Bound"
                      hint="Finally, setting a timeframe for your goal helps quantify it further, and helps keep your focus on track."
        ></v-text-field>
      </Editable>
      <div v-else v-if="kr.state === 'active' && kr_parent.obj_state === 'active' && (!kr.is_smart || showSmart)"
           @click="startEditing(6)"
           class="smart" :class="validateSmart(kr.t).toString()">
        <div class="smartLabel">Time-Bound:</div>
        <div class="smartValue">{{kr.t}}</div>
      </div>

      <v-divider></v-divider>

      <div v-for="(task, index) in kr.tasks.slice().sort(compareTasks)">
        <Editable v-if="editing[8][index]" :cancel="stopEditing" :submit="updateTaskValue" :index=task>
          <v-text-field @keydown.enter="updateTaskValue(task)" @keydown.esc="stopEditing"
                        v-model="editingValue"
                        label="Task"
          ></v-text-field>
        </Editable>
        <div v-else class="task"
             @mouseover="selectedTask = index"
             @mouseleave="selectedTask = -1">
          <div :class="task.state">
            <v-icon icon="mdi-close-box-outline" large v-if="task.state === 'failed'"/>
            <v-icon icon="mdi-checkbox-marked-outline" large v-if="task.state === 'finished'"/>
            <v-icon icon="mdi-checkbox-blank-outline" large v-if="task.state === 'active'"/>
          </div>
          <div v-html="string_to_html(task.value)" @click="startEditingTask(task)" :class="task.state" style="display: inline; padding-left: 3px; flex: 25;"/>

          <v-icon style="flex: 1;" icon="mdi-checkbox-blank-outline" large
                  v-if="selectedTask === index && task.state !== 'active' && kr.state === 'active' && kr_parent.obj_state === 'active'"
                  @click="updateTaskState(task, 'active')"/>
          <v-icon style="flex: 1;" icon="mdi-checkbox-marked-outline" large
                  v-if="selectedTask === index && task.state !== 'finished' && kr.state === 'active' && kr_parent.obj_state === 'active'"
                  @click="updateTaskState(task, 'finished')"/>
          <v-icon style="flex: 1;" icon="mdi-close-box-outline" large
                  v-if="selectedTask === index && task.state !== 'failed' && kr.state === 'active' && kr_parent.obj_state === 'active'"
                  @click="updateTaskState(task, 'failed')"/>

          <v-dialog
              v-model="confirmDeletionDialogs[index]"
              width="300"
          >
            <template v-slot:activator="{ props }">
              <v-icon style="flex: 1;" icon="mdi-delete-forever" large v-bind="props" v-if="selectedTask === index && kr.state === 'active' && kr_parent.obj_state === 'active'"/>
            </template>

            <v-card>
              <v-card-title class="text-h5 grey lighten-2">
                Delete Task?
              </v-card-title>
              <v-card-text>
                {{ task.value }}
              </v-card-text>
              <v-card-actions>
                <v-btn block @click="deleteTask(task, index)">Confirm</v-btn>
              </v-card-actions>
            </v-card>
          </v-dialog>
        </div>
      </div>

      <Editable v-if="editing[7]" :cancel="stopEditing" :submit="addTask">
        <v-text-field @keydown.enter="addTask" @keydown.esc="stopEditing"
                      v-model="editingValue"
                      label="Add Task"
        ></v-text-field>
      </Editable>
      <v-btn v-else v-if="kr.state === 'active' && kr_parent.obj_state === 'active'" color="secondary" @click="startEditing(7)">
        Add Task
      </v-btn>

    </v-card>

    <div>
      <v-dialog v-model="confirmStateDialogs[0]" width="300" v-if="kr.state === 'active' && kr_parent.obj_state === 'active'">
        <template v-slot:activator="{ props }">
          <v-btn style="width: 50%;" color="red" v-bind="props">fail</v-btn>
        </template>
        <v-card>
          <v-card-title class="text-h5 grey lighten-2">
            Fail?
          </v-card-title>
          <v-card-actions>
            <v-btn block @click="updateKeyResultState(0)">Confirm</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
      <v-dialog v-model="confirmStateDialogs[1]" width="300" v-if="kr.state === 'active' && kr_parent.obj_state === 'active'">
        <template v-slot:activator="{ props }">
          <v-btn style="width: 50%;" color="green" v-bind="props">complete</v-btn>
        </template>
        <v-card>
          <v-card-title class="text-h5 grey lighten-2">
            Complete?
          </v-card-title>
          <v-card-actions>
            <v-btn block @click="updateKeyResultState(1)">Confirm</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
      <v-dialog v-model="confirmStateDialogs[2]" width="300" v-if="kr.state !== 'active' && kr_parent.obj_state === 'active'">
        <template v-slot:activator="{ props }">
          <v-btn style="width: 100%;" color="blue" v-bind="props">activate</v-btn>
        </template>
        <v-card>
          <v-card-title class="text-h5 grey lighten-2">
            Activate?
          </v-card-title>
          <v-card-actions>
            <v-btn block @click="updateKeyResultState(2)">Confirm</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </div>

    <v-btn color="primary" @click="closeDialog">Close</v-btn>

  </v-dialog>
</template>

<style scoped>
.task {
  display: flex;
  background: white;
}
.task:hover {
  background: #f5f5f5;
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
