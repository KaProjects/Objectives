<script setup>
import {app_state} from '@/main'
import Editable from "@/components/Editable.vue";</script>

<script>
import {backend_fetch, string_to_html} from "@/utils";
import {app_state} from "@/main";

export default {
  name: "ObjectiveDialog",
  props: ["obj"],
  data() {
    return {
      values: [null, null, ""],
      editing: [false, false, false, []],
      editingValue: "",
      confirmStateDialogs: [false, false, false],
      selectedIdea: -1,
      ideas: [],
      confirmDeletionDialogs: [],
    }
  },
  watch: {
    obj() {
      this.values[0] = this.obj.name
      this.values[1] = this.obj.description
      this.loadIdeas()
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
      this.handleFetchError(error)
      this.values[0] = this.obj.name
      this.values[1] = this.obj.description
    },
    handleFetchError(error){
      console.error(error)
      alert(error)
    },
    closeDialog(){
      this.stopEditing()
      app_state.objDialogToggle = false
    },
    stopEditing(){
      this.editing = [false, false, false, []]
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
        body: JSON.stringify({"state": state})
      }
      await backend_fetch("/objective/" + this.obj.id + "/state", requestOptions)
        .then(async response => {
          if (response.ok) {
            const body = await response.json();
            this.obj.state = body.state
            this.obj.date_finished = body.date
            this.confirmStateDialogs[index] = false
            this.closeDialog()
            this.$emit('selectTab', body.state)
          } else {
            this.handleFetchError(await response.text())
          }})
        .catch(error => this.handleFetchError(error))
    },
    string_to_html,
    async loadIdeas() {
      await backend_fetch("/objective/" + this.obj.id + "/idea")
          .then(async response => {
            if (response.ok){
              this.ideas = await response.json()
            } else {
              this.handleFetchError(await response.text())
            }})
          .catch(error => this.handleFetchError(error))
    },
    startEditingIdea(index){
      if (this.obj.state === 'active') {
        this.stopEditing()
        this.editingValue = this.ideas[index].value
        this.editing[3][index] = true
      }
    },
    async updateIdeaValue(index){
      const idea = {value: this.editingValue}

      const requestOptions = {
        method: "PUT",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(idea)
      }
      await backend_fetch("/objective/" + this.obj.id + "/idea/" + this.ideas[index].id, requestOptions)
          .then(async response => {
            if (response.ok){
              const body = await response.json();
              this.ideas[index].value = body.value
            } else {
              this.handleFetchError(await response.text())
            }})
          .catch(error => this.handleFetchError(error))

      this.stopEditing()
    },
    async addIdea(){
      const idea = {value: this.editingValue}

      const requestOptions = {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(idea)
      }
      await backend_fetch("/objective/" + this.obj.id + "/idea", requestOptions)
          .then(async response => {
            if (response.ok){
              this.ideas.push(await response.json())
              this.obj.ideas_count = this.obj.ideas_count + 1
            } else {
              this.handleFetchError(await response.text())
            }})
          .catch(error => this.handleFetchError(error))

      this.editing[2] = false
    },
    async deleteIdea(idea, index){
      await backend_fetch("/objective/" + this.obj.id + "/idea/" + idea.id, {method: "DELETE"})
          .then(async response => {
            if (response.ok) {
              this.ideas.splice(this.ideas.indexOf(idea), 1);
              this.obj.ideas_count = this.obj.ideas_count - 1
            } else {
              this.handleFetchError(await response.text())
            }})
          .catch(error => this.handleFetchError(error))

      this.confirmDeletionDialogs[index] = false
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
        <v-textarea @keydown.esc="stopEditing"
                    v-model="editingValue"
                    label="Description"
        ></v-textarea>
      </Editable>
      <v-card-text v-else v-html="string_to_html(obj.description)" @click="startEditing(1)"/>

      <v-divider></v-divider>

      <div v-for="(idea, index) in ideas">
        <Editable v-if="editing[3][index]" :cancel="stopEditing" :submit="updateIdeaValue" :index=index>
          <v-text-field @keydown.enter="updateIdeaValue(index)" @keydown.esc="stopEditing"
                        v-model="editingValue"
                        label="Idea"
          ></v-text-field>
        </Editable>
        <div v-else class="idea"
             @mouseover="selectedIdea = index"
             @mouseleave="selectedIdea = -1">
          <div v-if="idea.value === ''">|</div>
          <div v-html="string_to_html(idea.value)" @click="startEditingIdea(index)" style="margin-left: 5px; flex: 25;"/>

          <v-dialog
              v-model="confirmDeletionDialogs[index]"
              width="300"
          >
            <template v-slot:activator="{ props }">
              <v-icon style="flex: 1;" icon="mdi-delete-forever" large v-bind="props" v-if="selectedIdea === index && obj.state === 'active'"/>
            </template>

            <v-card>
              <v-card-title class="text-h5 grey lighten-2">
                Delete Idea?
              </v-card-title>
              <v-card-text>
                {{ idea.value }}
              </v-card-text>
              <v-card-actions>
                <v-btn block @click="deleteIdea(idea, index)">Confirm</v-btn>
              </v-card-actions>
            </v-card>
          </v-dialog>
        </div>
      </div>

      <Editable v-if="editing[2]" :cancel="stopEditing" :submit="addIdea">
        <v-text-field @keydown.enter="addIdea" @keydown.esc="stopEditing"
                      v-model="editingValue"
                      label="Add Idea"
        ></v-text-field>
      </Editable>
      <v-btn v-else v-if="obj.state === 'active'" color="secondary" @click="startEditing(2)">
        Add Idea
      </v-btn>

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
.idea {
  display: flex;
  background: white;
}
.idea:hover {
  background: #f5f5f5;
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
