<script setup>
import { app_state } from '@/main'
import Objective from "@/components/Objective.vue";

</script>
<script>
import {backend_fetch, compare_dates} from "@/utils";
import {app_state} from "@/main";
import Ideas from "@/components/Ideas.vue";

export default {
  name: "Value",
  data() {
    return {
      value: Object,
      tab: "active",
      openAddObjDialog: false,
      newObj: {name: "", description: ""},
      showIdeas: false,
    }
  },
  watch: {
    openAddObjDialog(flag) {if (flag) {this.newObj = {name: "", description: ""}}}
  },
  methods: {
    async loadData() {
      this.value = await backend_fetch("/value/" + app_state.value.id)
    },
    compareObjectives(a, b) {
      let comparison
      if (a.state !== "active" &&  b.state !== "active") {
        comparison = - compare_dates(a.date_finished, b.date_finished)
      } else {
        comparison = - compare_dates(a.date_created, b.date_created)
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
      const body = await backend_fetch("/objective", requestOptions)
      this.value.objectives.push(body)
      this.openAddObjDialog = false
      this.tab = "active"
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
    async deleteObjective(obj) {
      await backend_fetch("/objective/" + obj.id, {method: "DELETE"})
      this.value.objectives.splice(this.value.objectives.indexOf(obj), 1);
    }
  },
  components: {
    Ideas,
  },
  mounted() {
    this.loadData()
  }
}
</script>

<template>
  <div>

    <div class="appbar">
      <v-btn class="button" icon="mdi-arrow-left" @click="app_state.unselect_value()"/>
      <h1 class="title">{{value.name}}</h1>

      <v-tabs v-model="tab" bg-color="primary">
        <v-tab value="active">Active</v-tab>
        <v-tab value="inactive">Done</v-tab>
      </v-tabs>

      <v-btn class="button" icon="mdi-lightbulb" @click.stop="showIdeas = false" v-if="showIdeas"/>
      <v-btn class="button" icon="mdi-lightbulb-outline" @click.stop="showIdeas = true" v-else/>

      <v-dialog v-model="openAddObjDialog" width="300">
        <template v-slot:activator="{ props }">
          <v-btn v-bind="props" class="button" icon="mdi-plus"/>
        </template>
        <v-card>
          <v-text-field label="Name" v-model="newObj.name"/>
          <v-text-field label="Description" v-model="newObj.description"/>
          <v-card-actions>
            <v-btn block @click="addObjective" :disabled="!newObj.name">Add</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </div>

    <div style="display: flex; overflow-x:scroll;">
      <Ideas class="obj" :valueId="app_state.value.id" v-if="showIdeas"/>
      <Objective v-for="(objective) in filterObjectives(value.objectives, tab === 'active')"
                 :objective="objective" :selectTab="selectTab" :delete="deleteObjective"/>
    </div>
  </div>
</template>

<style scoped>
.appbar {
  display: inline-flex;
}
.title {
  width: 300px;
}
.button {
  margin-left: 10px;
  margin-right: 10px;
  background: #181818;
  color: darkgrey
}
.button:hover {
  background: #2f2f2f;
}
</style>