<script setup>
import { app_state } from '@/main'
import Editable from "@/components/Editable.vue";
</script>

<script>
import {backend_fetch} from "@/properties";
import {app_state} from "@/main";

export default {
  name: "ObjectiveDialog",
  props: ["obj"],
  data() {
    return {
      values: [null, null],
      editing: [false, false],
      editingValue: "",
      confirmStateDialogs: [false, false, false],
    }
  },
  watch: {
    obj() {
      this.values[0] = this.obj.name
      this.values[1] = this.obj.description
    }
  },
  methods: {
    startEditing(index){
      if (this.obj.state === 'active') {
        this.stopEditing()
        this.editingValue = this.values[index]
        this.editing[index] = true
      }
    },
    async updateObjective(index){
      this.values[index] = this.editingValue
      this.editing[index] = false

      let obj = {}
      obj.name = this.values[0]
      obj.description = this.values[1]

      const requestOptions = {
        method: "PUT",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(obj)
      }

      await backend_fetch("/objective/" + this.obj.id, requestOptions)
        .then(async response => {
          const body = await response.text();
          if (response.ok) {
            this.obj.name = this.values[0]
            this.obj.description = this.values[1]
          } else {
            this.handleUpdateObjectiveError(body)
          }})
        .catch(error => this.handleUpdateObjectiveError(error))
    },
    handleUpdateObjectiveError(error){
      console.error(error)
      alert(error)

      this.values[0] = this.obj.name
      this.values[1] = this.obj.description
    },
    closeDialog(){
      this.stopEditing()
      app_state.objDialogToggle = false
    },
    stopEditing(){
      this.editing = [false, false]
    },
    async updateObjectiveState(index) {
      let state = null
      if (index === 0) state = "failed"
      if (index === 1) state = "achieved"
      if (index === 2) state = "active"
      if (state === null) {
        console.log("invalid index " + index)
        alert("invalid index " + index)
        return
      }

      const requestOptions = {
        method: "PUT",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(state)
      }
      await backend_fetch("/objective/" + this.obj.id + "/state", requestOptions)
        .then(async response => {
          if (response.ok) {
            const body = await response.json();
            this.obj.state = body.state
            this.obj.date_finished = body.date

            this.confirmStateDialogs[index] = false
          } else {
            const error = await response.text();
            console.error(error)
            alert(error)
          }})
        .catch(error => {
          console.error(error)
          alert(error)
        })
    },
  }
}
</script>

<template>
  <v-dialog v-model="app_state.objDialogToggle" persistent width="600">
    <v-card>
      <Editable v-if="editing[0]" :cancel="stopEditing" :submit="updateObjective" :index=0>
        <v-text-field @keydown.enter="updateObjective(0)" @keydown.esc="stopEditing"
                      v-model="editingValue"
                      label="Name"
        ></v-text-field>
      </Editable>
      <div v-else class="datesInfo">
        <v-card-title @click="startEditing(0)" class="text-h5 grey lighten-2">
          {{obj.name}}
        </v-card-title>
        <div class="datesInfoChild" style="top: 0;">created: {{obj.date_created}}</div>
        <div class="datesInfoChild" style="top: 15px;" v-if="obj.state==='achieved'">achieved: {{obj.date_finished}}</div>
        <div class="datesInfoChild" style="top: 15px;" v-if="obj.state==='failed'">failed: {{obj.date_finished}}</div>
      </div>

      <Editable v-if="editing[1]" :cancel="stopEditing" :submit="updateObjective" :index=1>
        <v-text-field @keydown.enter="updateObjective(1)" @keydown.esc="stopEditing"
                      v-model="editingValue"
                      label="Description"
        ></v-text-field>
      </Editable>
      <v-card-text v-else @click="startEditing(1)">
        {{obj.description}}
      </v-card-text>

    </v-card>

    <div>
      <v-dialog v-model="confirmStateDialogs[0]" width="300" v-if="obj.state === 'active'">
        <template v-slot:activator="{ props }">
          <v-btn style="width: 50%;" color="red" v-bind="props">fail</v-btn>
        </template>
        <v-card>
          <v-card-title class="text-h5 grey lighten-2">
            Fail?
          </v-card-title>
          <v-card-actions>
            <v-btn block @click="updateObjectiveState(0)">Confirm</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
      <v-dialog v-model="confirmStateDialogs[1]" width="300" v-if="obj.state === 'active'">
        <template v-slot:activator="{ props }">
          <v-btn style="width: 50%;" color="green" v-bind="props">achieve</v-btn>
        </template>
        <v-card>
          <v-card-title class="text-h5 grey lighten-2">
            Achieve?
          </v-card-title>
          <v-card-actions>
            <v-btn block @click="updateObjectiveState(1)">Confirm</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
      <v-dialog v-model="confirmStateDialogs[2]" width="300" v-if="obj.state !== 'active'">
        <template v-slot:activator="{ props }">
          <v-btn style="width: 100%;" color="blue" v-bind="props">activate</v-btn>
        </template>
        <v-card>
          <v-card-title class="text-h5 grey lighten-2">
            Activate?
          </v-card-title>
          <v-card-actions>
            <v-btn block @click="updateObjectiveState(2)">Confirm</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </div>

    <v-btn color="primary" @click="closeDialog">Close</v-btn>

  </v-dialog>
</template>

<style scoped>
.datesInfo {
  position: relative;
}
.datesInfoChild {
  font-size: 12px;
  position: absolute;
  right: 5px;
}
</style>