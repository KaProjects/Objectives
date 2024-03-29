<script setup>
import { app_state } from '@/main'

</script>
<script>
import {backend_fetch, string_to_html} from "@/utils";
import {app_state} from "@/main";
import Ideas from "@/components/Ideas.vue";
import KeyResultDialog from "@/components/KeyResultDialog.vue";
import ObjectiveDialog from "@/components/ObjectiveDialog.vue";

export default {
  name: "Value",
  data() {
    return {
      value: Object,
      newKrDialogs: [],
      newKr: {name: "", description: ""},
      selectedKr: Object,
      selectedKr_parent: Object,
      tab: "active",
      newObjDialog: false,
      newObj: {name: "", description: ""},
      selectedObjective_index: -1,
      selectedObjective: Object,
    }
  },
  methods: {
    async loadData() {
      await backend_fetch("/value/" + app_state.value.id)
        .then(async response => {
          if (response.ok){
            this.value = await response.json()
            for (let i = 0; i < this.value.objectives.length; i++) {
              this.newKrDialogs[i] = false
            }
          } else {
            this.handleFetchError(await response.text())
          }})
        .catch(error => this.handleFetchError(error))
    },
    async addKeyResult(objective) {
      const requestOptions = {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({name: this.newKr.name, description: this.newKr.description, objective_id: objective.id})
      }
      await backend_fetch("/key_result", requestOptions)
        .then(async response => {
          if (response.ok){
            const body = await response.json()
            objective.key_results.push(body)
            this.newKrDialogs[objective.id] = false
            this.newKr = {name: "", description: ""}
          } else {
            this.handleFetchError(await response.text())
          }})
        .catch(error => this.handleFetchError(error))
    },
    handleFetchError(error){
      console.error(error)
      alert(error)
    },
    async openKeyResult(kr, obj_state) {
      await backend_fetch("/key_result/" + kr.id)
        .then(async response => {
          if (response.ok){
            this.selectedKr = await response.json()
            this.selectedKr_parent = kr
            this.selectedKr_parent.obj_state = obj_state
            app_state.krDialogToggle = true
          } else {
            this.handleFetchError(await response.text())
          }})
        .catch(error => this.handleFetchError(error))
    },
    compareDates(a, b){
      let dateA = a.split("/")
      let dateB = b.split("/")
      if (dateA[2] !== dateB[2]){
        return parseInt(dateA[2]) - parseInt(dateB[2])
      } else {
        if (dateA[1] !== dateB[1]) {
          return parseInt(dateA[1]) - parseInt(dateB[1])
        } else {
          if (dateA[0] !== dateB[0]) {
            return parseInt(dateA[0]) - parseInt(dateB[0])
          } else {
            return 0
          }
        }
      }
    },
    compareKeyResults(a, b) {
      let comparison
      if (a.state === "active") {
        if (b.state === "completed" || b.state === "failed"){
          comparison = -1
        } else { // both active
          comparison = this.compareDates(a.date_reviewed, b.date_reviewed)
        }
      } else {
        if (b.state === "active") {
          comparison = 1
        } else { // both inactive
          comparison = -1 * this.compareDates(a.date_reviewed, b.date_reviewed)
        }
      }
      if (comparison !== 0) {
        return comparison
      } else {
        return b.id - a.id
      }
    },
    compareObjectives(a, b) {
      let comparison
      if (a.state !== "active" &&  b.state !== "active") {
        comparison = - this.compareDates(a.date_finished, b.date_finished)
      } else {
        comparison = - this.compareDates(a.date_created, b.date_created)
      }
      if (comparison !== 0) {
        return comparison
      } else {
        return b.id - a.id
      }
    },
    filterObjectives(objs, isActive){
      if (typeof objs === "undefined") return objs;
      return objs.filter(obj => isActive ? obj.state === 'active' : obj.state !== 'active').slice().sort(this.compareObjectives);
    },
    async addObjective(){
      const requestOptions = {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({name: this.newObj.name, description: this.newObj.description, value_id: this.value.id})
      }
      await backend_fetch("/objective", requestOptions)
        .then(async response => {
          if (response.ok){
            const body = await response.json()
            this.value.objectives.push(body)
            this.newObjDialog = false
            this.newObj = {name: "", description: ""}
            this.tab = "active"
          } else {
            this.handleFetchError(await response.text())
          }})
        .catch(error => this.handleFetchError(error))
    },
    openObjectiveDialog(objective) {
      this.selectedObjective = objective
      app_state.objDialogToggle = true
    },
    selectTab(state) {
      if (state === "active") {
        this.tab = "active"
      } else {
        this.tab = "inactive"
      }
    },
    string_to_html
  },
  components: {
    Ideas,
    KeyResultDialog,
    ObjectiveDialog,
  },
  mounted() {
    this.loadData()
  }
}
</script>

<template>
  <div>

    <div>
      <v-btn class="backBtn" >
        <v-icon icon="mdi-arrow-left" size="25" @click="app_state.unselect_value()"/>
      </v-btn>

      <h1 class="inLine" style="width: 300px;" >{{value.name}}</h1>

      <v-tabs class="inLine" v-model="tab" bg-color="primary">
        <v-tab value="active">Active</v-tab>
        <v-tab value="inactive">Done</v-tab>
      </v-tabs>

      <v-dialog v-model="newObjDialog" width="300">
        <template v-slot:activator="{ props }">
          <v-btn v-bind="props" class="addObj">ADD</v-btn>
        </template>
        <v-card>
          <v-text-field
              label="Name"
              v-model="newObj.name"
              required
          ></v-text-field>
          <v-text-field
              label="Description"
              v-model="newObj.description"
              required
          ></v-text-field>
          <v-card-actions>
            <v-btn block @click="addObjective">Add</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>

    </div>

    <KeyResultDialog :kr="selectedKr" :kr_parent="selectedKr_parent" />

    <ObjectiveDialog :obj="selectedObjective" v-on:selectTab="selectTab" />

    <div style="display: flex;">
      <Ideas :valueId="app_state.value.id" class="obj"  />

      <div style="display: flex; overflow-x:scroll;">
        <v-card class="obj" :class="objective.state" width="300" elevation="3" shaped
              v-for="(objective, index) in filterObjectives(value.objectives, tab === 'active')" :key="objective.id"
              @mouseover="selectedObjective_index = index"
              @mouseleave="selectedObjective_index = -1"
        >
          <v-card-title>{{objective.name}}</v-card-title>
          <v-card-text v-html="string_to_html(objective.description)"/>

          <v-icon class="objEdit" icon="mdi-pencil-circle-outline" large
                  v-if="selectedObjective_index === index"
                  @click="openObjectiveDialog(objective)"/>

          <div class="objIdeas" v-if="objective.ideas_count > 0">
            <v-icon icon="mdi-lightbulb-variant-outline" size="15" style="margin: 0 auto;"/>
            <div style="margin: -5px auto;">{{objective.ideas_count}}</div>
          </div>

          <div style="display: grid; overflow-x:scroll; max-height: 650px">
            <v-list-item v-for="key_result in objective.key_results.slice().sort(compareKeyResults)"
                         class="kr" :class="key_result.state"
                         @click="openKeyResult(key_result, objective.state)">
              <v-list-item-content>

                <v-list-item-title class="inLine">{{key_result.name}}</v-list-item-title>
                <v-icon style="vertical-align: top;" icon="mdi-check-bold" v-if="key_result.state === 'completed'" />
                <v-icon style="vertical-align: top;" icon="mdi-close-thick" v-if="key_result.state === 'failed'"/>

                <div class="krInfo" v-if="key_result.state === 'active'">
                  <div class="krInfoChild" style="right: 0;">{{key_result.date_reviewed}}</div>
                  <div class="krInfoChild" style="right: 50%; color: #ff0000; font-weight: bold;" v-if="!key_result.is_smart">
                    !SMART
                  </div>
                  <div class="krInfoChild" style="left: 0;">{{key_result.resolved_tasks_count}}/{{key_result.all_tasks_count}}</div>
                </div>

              </v-list-item-content>
            </v-list-item>
          </div>

          <v-card-actions v-if="objective.state === 'active'">
            <v-dialog
                v-model="newKrDialogs[objective.id]"
                width="300"
            >
              <template v-slot:activator="{ props }">
                <v-btn color="primary" v-bind="props">
                  <v-icon icon="mdi-plus" large/>
                </v-btn>
              </template>

              <v-card>
                <v-text-field
                    label="Name"
                    v-model="newKr.name"
                    required
                ></v-text-field>
                <v-text-field
                    label="Description"
                    v-model="newKr.description"
                    required
                ></v-text-field>
                <v-card-actions>
                  <v-btn block @click="addKeyResult(objective)">Add</v-btn>
                </v-card-actions>
              </v-card>
            </v-dialog>

          </v-card-actions>
        </v-card>
      </div>
    </div>

  </div>


</template>

<style scoped>
.kr {
  border: 1px solid #2c3e50;
}
.kr:hover {
  border-width: 2px;
}
.kr.completed {
  color: #017901;
}
.kr.failed {
  color: #ab0000;
}
.kr.active {
  color: #000000;
}
.inLine {
  display: inline-block;
}
.obj {
  display: inline-block;
  min-width: 300px;
  vertical-align:top;
  margin-bottom: auto;
  margin-left: 1px;
}
.obj.active {
  background: #b2d1ec;
}
.obj.failed {
  background: #dc1a1a;
}
.obj.achieved {
  background: #84e184;
}
.obj.failed > div > .kr {
  color: #262626;
}
.obj.achieved > div > .kr {
  color: #262626;
}
.objEdit {
  position: absolute;
  right: 0;
  top: 0;
}
.objIdeas {
  display: grid;
  position: absolute;
  right: 5px;
  top: 30px;
}
.krInfo {
  margin-top: 20px;
  margin-bottom: 10px;
  position: relative;
}
.krInfoChild {
  font-size: 10px;
  position: absolute;
  bottom: 0;
}
.addObj {
  background: #181818;
  color: darkgrey;
  margin-top: -40px
}
.addObj:hover {
  background: grey;
}
.backBtn {
  width: 80px;
  margin-top: -10px;
  background: #181818;
  color: darkgrey
}
.backBtn:hover {
  background: #2f2f2f;
}
</style>