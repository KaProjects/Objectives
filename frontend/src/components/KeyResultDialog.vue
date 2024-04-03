<script setup>
import Editable from "@/components/Editable.vue";
</script>

<script>
import {backend_fetch, string_to_html} from "@/utils";

export default {
  name: "KeyResultDialog",
  props: ["kr", "kr_parent"],
  data() {
    return {
      values: [null, null, null, null, null, null, null, ""],
      editing: [false, false, false, false, false, false, false, false, []],
      editingValue: "",
      selectedTask: -1,
      confirmDeletionDialogs: [],
      confirmStateDialogs: [false, false, false],
      showSmart: false
    }
  },
  watch: {
    kr(){
      this.values[0] = this.kr.name
      this.values[1] = this.kr.description
      this.values[2] = this.kr.s
      this.values[3] = this.kr.m
      this.values[4] = this.kr.a
      this.values[5] = this.kr.r
      this.values[6] = this.kr.t
    }
  },
  methods: {
    async updateKeyResult(){
      let kr = {}
      kr.name = this.values[0]
      kr.description = this.values[1]
      kr.s = this.values[2]
      kr.m = this.values[3]
      kr.a = this.values[4]
      kr.r = this.values[5]
      kr.t = this.values[6]

      const requestOptions = {
        method: "PUT",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(kr)
      }
      await backend_fetch("/key_result/" + this.kr.id, requestOptions)
        .then(async response => {
          const body = await response.text();
          if (response.ok) {
            this.kr.name = this.values[0]
            this.kr.description = this.values[1]
            this.kr.s = this.values[2]
            this.kr.m = this.values[3]
            this.kr.a = this.values[4]
            this.kr.r = this.values[5]
            this.kr.t = this.values[6]
            this.kr.date_reviewed = body

            this.kr_parent.name = this.kr.name
            this.kr_parent.date_reviewed = this.kr.date_reviewed
            this.kr.is_smart = this.validateSmart(this.kr.s) && this.validateSmart(this.kr.m)
                && this.validateSmart(this.kr.a) && this.validateSmart(this.kr.r) && this.validateSmart(this.kr.t)
            this.kr_parent.is_smart = this.kr.is_smart
          } else {
            this.handleUpdateKeyResultError(body)
          }})
        .catch(error => this.handleUpdateKeyResultError(error))
    },
    handleUpdateKeyResultError(error){
      console.error(error)
      alert(error)

      this.values[0] = this.kr.name
      this.values[1] = this.kr.description
      this.values[2] = this.kr.s
      this.values[3] = this.kr.m
      this.values[4] = this.kr.a
      this.values[5] = this.kr.r
      this.values[6] = this.kr.t
    },
    startEditing(index){
      if (this.kr.state === 'active' && this.kr_parent.obj_state === 'active') {
        this.stopEditing()
        this.editingValue = this.values[index]
        this.editing[index] = true
      }
    },
    update(index){
      this.values[index] = this.editingValue
      this.editing[index] = false
      this.updateKeyResult()
    },
    startEditingTask(index){
      if (this.kr.state === 'active' && this.kr_parent.obj_state === 'active') {
        this.stopEditing()
        this.editingValue = this.kr.tasks[index].value
        this.editing[8][index] = true
      }
    },
    async updateTaskValue(index){
      const task = {kr_id: this.kr.id, value: this.editingValue, state: this.kr.tasks[index].state}

      const requestOptions = {
        method: "PUT",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(task)
      }
      await backend_fetch("/task/" + this.kr.tasks[index].id, requestOptions)
        .then(async response => {
          if (response.ok){
            const body = await response.json();
            this.kr.tasks[index].value = body.value
            await this.retrieveKeyResultReviewDate()
          } else {
            this.handleFetchError(await response.text())
          }})
        .catch(error => this.handleFetchError(error))



      this.stopEditing()
    },
    closeDialog(){
      this.stopEditing()
      this.showSmart = false
      this.$emit('close')
    },
    stopEditing(){
      this.editing = [false, false, false, false, false, false, false, false, []]
    },
    async addTask(){
      const task = {kr_id: this.kr.id, value: this.editingValue}

      const requestOptions = {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(task)
      }
      await backend_fetch("/task", requestOptions)
        .then(async response => {
          if (response.ok){
            this.kr.tasks.push(await response.json())
            this.kr_parent.all_tasks_count = this.kr_parent.all_tasks_count + 1
            await this.retrieveKeyResultReviewDate()
          } else {
            this.handleFetchError(await response.text())
          }})
        .catch(error => this.handleFetchError(error))

      this.editing[7] = false
    },
    handleFetchError(error){
      console.error(error)
      alert(error)
    },
    async updateTaskState(index, state){
      const task = {kr_id: this.kr.id, value: this.kr.tasks[index].value, state: state}

      const requestOptions = {
        method: "PUT",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(task)
      }
      await backend_fetch("/task/" + this.kr.tasks[index].id, requestOptions)
        .then(async response => {
          if (response.ok){
            const body = await response.json();
            if (this.kr.tasks[index].state === 'active' && body.state !== 'active'){
              this.kr_parent.resolved_tasks_count += 1
            }
            if (this.kr.tasks[index].state !== 'active' && body.state === 'active'){
              this.kr_parent.resolved_tasks_count -= 1
            }
            this.kr.tasks[index].state = body.state
            await this.retrieveKeyResultReviewDate()
          } else {
            this.handleFetchError(await response.text())
          }})
        .catch(error => this.handleFetchError(error))
    },
    async deleteTask(task, index){
      await backend_fetch("/task/" + task.id, {method: "DELETE"})
        .then(async response => {
          if (response.ok) {
            this.kr.tasks.splice(this.kr.tasks.indexOf(task), 1);
            this.kr_parent.all_tasks_count = this.kr_parent.all_tasks_count - 1
            if (task.state !== 'active') {
              this.kr_parent.resolved_tasks_count -= 1
            }
            await this.retrieveKeyResultReviewDate()
          } else {
            this.handleFetchError(await response.text())
          }})
        .catch(error => this.handleFetchError(error))

      this.confirmDeletionDialogs[index] = false
    },
    async retrieveKeyResultReviewDate(){
      await backend_fetch("/key_result/" + this.kr.id)
        .then(async response => {
          if (response.ok){
            const body = await response.json();
            this.kr.date_reviewed = body.date_reviewed
            this.kr_parent.date_reviewed = this.kr.date_reviewed
          } else {
            this.handleFetchError(await response.text())
          }})
        .catch(error => this.handleFetchError(error))
    },
    async updateKeyResultState(index){
      let state = null
      if (index===0) state = "failed"
      if (index===1) state = "completed"
      if (index===2) state = "active"
      if (state===null) {
        console.log("invalid index " + index)
        alert("invalid index " + index)
        return
      }

      const requestOptions = {
        method: "PUT",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({"state": state})
      }
      await backend_fetch("/key_result/" + this.kr.id + "/state", requestOptions)
        .then(async response => {
          const body = await response.text();
          if (response.ok){
            this.kr.state = body
            this.kr_parent.state = body
            await this.retrieveKeyResultReviewDate()
            this.confirmStateDialogs[index] = false
          } else {
            this.handleFetchError(body)
          }})
        .catch(error => this.handleFetchError(error))
    },
    string_to_html,
    validateSmart(value){
      return value !== null && value !== undefined && value.length > 0 && !value.startsWith("[!!!]")
    }
  },
}
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
      <v-card-text v-else v-html="string_to_html(kr.description)" @click="startEditing(1)"/>

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

      <div v-for="(task, index) in kr.tasks">
        <Editable v-if="editing[8][index]" :cancel="stopEditing" :submit="updateTaskValue" :index=index>
          <v-text-field @keydown.enter="updateTaskValue(index)" @keydown.esc="stopEditing"
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
          <div v-html="string_to_html(task.value)" @click="startEditingTask(index)" :class="task.state" style="display: inline; padding-left: 3px; flex: 25;"/>

          <v-icon style="flex: 1;" icon="mdi-checkbox-blank-outline" large
                  v-if="selectedTask === index && task.state !== 'active' && kr.state === 'active' && kr_parent.obj_state === 'active'"
                  @click="updateTaskState(index, 'active')"/>
          <v-icon style="flex: 1;" icon="mdi-checkbox-marked-outline" large
                  v-if="selectedTask === index && task.state !== 'finished' && kr.state === 'active' && kr_parent.obj_state === 'active'"
                  @click="updateTaskState(index, 'finished')"/>
          <v-icon style="flex: 1;" icon="mdi-close-box-outline" large
                  v-if="selectedTask === index && task.state !== 'failed' && kr.state === 'active' && kr_parent.obj_state === 'active'"
                  @click="updateTaskState(index, 'failed')"/>

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