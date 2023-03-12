<script setup>
import { app_state } from '@/main'
import Editable from "@/components/Editable.vue";
</script>

<script>
import {properties} from "@/properties";
import {app_state} from "@/main";

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
      kr.state = this.kr.state
      kr.id = this.kr.id
      kr.objective_id = this.kr.objective_id
      kr.name = this.values[0]
      kr.description = this.values[1]
      kr.s = this.values[2]
      kr.m = this.values[3]
      kr.a = this.values[4]
      kr.r = this.values[5]
      kr.t = this.values[6]

      const requestOptions = {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(kr)
      };

      const response = await fetch("http://" + properties.host + ":" + properties.port + "/kr/update", requestOptions)
      if (response.ok){
        this.kr.name = this.values[0]
        this.kr.description = this.values[1]
        this.kr.s = this.values[2]
        this.kr.m = this.values[3]
        this.kr.a = this.values[4]
        this.kr.r = this.values[5]
        this.kr.t = this.values[6]
        this.kr.date_reviewed = await response.json()

        this.kr_parent.name = this.kr.name
        this.kr_parent.date_reviewed = this.kr.date_reviewed

      } else {
        const error = await response.json()
        console.error(error)
        alert(error.error)

        this.values[0] = this.kr.name
        this.values[1] = this.kr.description
        this.values[2] = this.kr.s
        this.values[3] = this.kr.m
        this.values[4] = this.kr.a
        this.values[5] = this.kr.r
        this.values[6] = this.kr.t
      }
    },
    startEditing(index){
      if (this.kr.state === 'active') {
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
      if (this.kr.state === 'active') {
        this.stopEditing()
        this.editingValue = this.kr.tasks[index].value
        this.editing[8][index] = true
      }
    },
    async updateTaskValue(index){
      const task = {kr_id: this.kr.id, value: this.editingValue, id: this.kr.tasks[index].id, state: this.kr.tasks[index].state}

      const requestOptions = {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(task)
      };

      const response = await fetch("http://" + properties.host + ":" + properties.port + "/task/update", requestOptions)
      if (response.ok){
        const updatedTask = await response.json();
        this.kr.tasks[index].value = updatedTask.value
      } else {
        const error = await response.json()
        console.error(error)
        alert(error.error)
      }

      this.stopEditing()
    },
    closeDialog(){
      this.stopEditing()
      app_state.krDialogToggle = false
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
      };
      const response = await fetch("http://" + properties.host + ":" + properties.port + "/task/add", requestOptions)
      if (response.ok){
        const newTask = await response.json();
        this.kr.tasks.push(newTask)
        this.kr_parent.all_tasks_count = this.kr_parent.all_tasks_count + 1
        await this.reviewKeyResult()
      } else {
        const error = await response.json()
        console.error(error)
        alert(error.error)
      }

      this.editing[7] = false
    },
    async updateTaskState(index, state){
      const task = {kr_id: this.kr.id, value: this.kr.tasks[index].value, id: this.kr.tasks[index].id, state: state}

      const requestOptions = {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(task)
      };

      const response = await fetch("http://" + properties.host + ":" + properties.port + "/task/update", requestOptions)
      if (response.ok){
        const updatedTask = await response.json();
        if (this.kr.tasks[index].state === 'finished' && updatedTask.state !== 'finished'){
          this.kr_parent.finished_tasks_count = this.kr_parent.finished_tasks_count - 1
        }
        if (this.kr.tasks[index].state !== 'finished' && updatedTask.state === 'finished'){
          this.kr_parent.finished_tasks_count = this.kr_parent.finished_tasks_count + 1
        }
        this.kr.tasks[index].state = updatedTask.state
        await this.reviewKeyResult()
      } else {
        const error = await response.json()
        console.error(error)
        alert(error.error)
      }
    },
    async deleteTask(task, index){
      const response = await fetch("http://" + properties.host + ":" + properties.port + "/task/" + task.id, {method: "DELETE"})
      if (response.ok) {
        this.kr.tasks.splice(this.kr.tasks.indexOf(task), 1);
        this.kr_parent.all_tasks_count = this.kr_parent.all_tasks_count - 1
        if (task.state === 'finished') {
          this.kr_parent.finished_tasks_count = this.kr_parent.finished_tasks_count - 1
        }
        await this.reviewKeyResult()
      } else {
        alert(response.status);
      }

      this.confirmDeletionDialogs[index] = false
    },
    async reviewKeyResult(){
      const response = await fetch("http://" + properties.host + ":" + properties.port + "/kr/" + this.kr.id + "/review", {method: "POST"})
      if (response.ok){
        this.kr.date_reviewed = await response.json()
        this.kr_parent.date_reviewed = this.kr.date_reviewed
      } else {
        const error = await response.json()
        console.error(error)
        alert(error.error)
      }
    }
  },
}
</script>

<template>
  <v-dialog v-model="app_state.krDialogToggle" persistent width="600">
    <v-card>

      <Editable v-if="editing[0]" :cancel="stopEditing" :submit="update" :index=0>
        <v-text-field @keydown.enter="update(0)" @keydown.esc="stopEditing"
                      v-model="editingValue"
                      label="Name"
        ></v-text-field>
      </Editable>
      <v-card-title v-else @click="startEditing(0)" class="text-h5 grey lighten-2">
        {{kr.name}}
      </v-card-title>


      <Editable v-if="editing[1]" :cancel="stopEditing" :submit="update" :index=1>
        <v-text-field @keydown.enter="update(1)" @keydown.esc="stopEditing"
                      v-model="editingValue"
                      label="Description"
        ></v-text-field>
      </Editable>
      <v-card-text v-else @click="startEditing(1)">
        {{kr.description}}
      </v-card-text>

      <v-divider></v-divider>

      <Editable v-if="editing[2]" :cancel="stopEditing" :submit="update" :index=2>
        <v-text-field @keydown.enter="update(2)" @keydown.esc="stopEditing"
                      v-model="editingValue"
                      label="Specific"
                      hint="The goal should have a clear, highly-specific endpoint. If your goal is too vague, it won’t be SMART."
        ></v-text-field>
      </Editable>
      <div v-else v-if="kr.state === 'active'" @click="startEditing(2)">
        Specific: {{kr.s}}
      </div>

      <Editable v-if="editing[3]" :cancel="stopEditing" :submit="update" :index=3>
        <v-text-field @keydown.enter="update(3)" @keydown.esc="stopEditing"
                      v-model="editingValue"
                      label="Measurable"
                      hint="You need to be able to accurately track your progress, so you can judge when a goal will be met."
        ></v-text-field>
      </Editable>
      <div v-else v-if="kr.state === 'active'" @click="startEditing(3)">
        Measurable: {{kr.m}}
      </div>

      <Editable v-if="editing[4]" :cancel="stopEditing" :submit="update" :index=4>
        <v-text-field @keydown.enter="update(4)" @keydown.esc="stopEditing"
                      v-model="editingValue"
                      label="Attainable"
                      hint="Of course, setting a goal that’s too ambitious will see you struggle to achieve it. This will sap at your motivation, both now and in the future."
        ></v-text-field>
      </Editable>
      <div v-else v-if="kr.state === 'active'" @click="startEditing(4)">
        Attainable: {{kr.a}}
      </div>

      <Editable v-if="editing[5]" :cancel="stopEditing" :submit="update" :index=5>
        <v-text-field @keydown.enter="update(5)" @keydown.esc="stopEditing"
                      v-model="editingValue"
                      label="Relevant"
                      hint="The goal you pick should be pertinent to your chosen field, or should benefit you directly."
        ></v-text-field>
      </Editable>
      <div v-else v-if="kr.state === 'active'" @click="startEditing(5)">
        Relevant: {{kr.r}}
      </div>

      <Editable v-if="editing[6]" :cancel="stopEditing" :submit="update" :index=6>
        <v-text-field @keydown.enter="update(6)" @keydown.esc="stopEditing"
                      v-model="editingValue"
                      label="Time-Bound"
                      hint="Finally, setting a timeframe for your goal helps quantify it further, and helps keep your focus on track."
        ></v-text-field>
      </Editable>
      <div v-else v-if="kr.state === 'active'" @click="startEditing(6)">
        Time-Bound: {{kr.t}}
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
          <div style="flex: 25;" @click="startEditingTask(index)">
            <v-icon icon="mdi-close-box-outline" large v-if="task.state === 'failed'"/>
            <v-icon icon="mdi-checkbox-marked-outline" large v-if="task.state === 'finished'"/>
            <v-icon icon="mdi-checkbox-blank-outline" large v-if="task.state === 'active'"/>
            {{task.value}}
          </div>
          <v-icon style="flex: 1;" icon="mdi-checkbox-blank-outline" large
                  v-if="selectedTask === index && task.state !== 'active' && kr.state === 'active'"
                  @click="updateTaskState(index, 'active')"/>
          <v-icon style="flex: 1;" icon="mdi-checkbox-marked-outline" large
                  v-if="selectedTask === index && task.state !== 'finished' && kr.state === 'active'"
                  @click="updateTaskState(index, 'finished')"/>
          <v-icon style="flex: 1;" icon="mdi-close-box-outline" large
                  v-if="selectedTask === index && task.state !== 'failed' && kr.state === 'active'"
                  @click="updateTaskState(index, 'failed')"/>

          <v-dialog
              v-model="confirmDeletionDialogs[index]"
              width="300"
          >
            <template v-slot:activator="{ props }">
              <v-icon style="flex: 1;" icon="mdi-delete-forever" large v-bind="props" v-if="selectedTask === index && kr.state === 'active'"/>
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
      <v-btn v-else v-if="kr.state === 'active'" color="primary" @click="startEditing(7)">
        Add Task
      </v-btn>



    </v-card>

    <v-btn color="red" @click="closeDialog">Close</v-btn>



  </v-dialog>
</template>

<style scoped>
.task {
  display: flex;
  background: white;
}
.task:hover {
  display: flex;
  background: #f5f5f5;
}
</style>