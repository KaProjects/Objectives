<script setup>

</script>
<script>
import {backend_fetch, compare_dates, string_to_html} from "@/utils";
import KeyResultDialog from "@/components/KeyResultDialog.vue";
import ObjectiveDialog from "@/components/ObjectiveDialog.vue";

export default {
  name: "Value",
  props: ["objective", "selectTab"],
  data() {
    return {
      focused: false,
      openObjDialog: false,
      openAddKrDialog: false,
      newKr: {name: "", description: ""},
      selectedKr: Object,
      selectedKr_parent: Object,
      selectedObj: Object,
      openKrDialog: false,
    }
  },
  watch: {
    openAddKrDialog(flag) {if (flag) {this.newKr = {name: "", description: ""}}}
  },
  methods: {
    string_to_html,
    compareKeyResults(a, b) {
      let comparison
      if (a.state === "active") {
        if (b.state === "completed" || b.state === "failed"){
          comparison = -1
        } else { // both active
          comparison = compare_dates(a.date_reviewed, b.date_reviewed)
        }
      } else {
        if (b.state === "active") {
          comparison = 1
        } else { // both inactive
          comparison = -1 * compare_dates(a.date_reviewed, b.date_reviewed)
        }
      }
      if (comparison !== 0) {
        return comparison
      } else {
        return b.id - a.id
      }
    },
    async openKeyResult(kr, obj_state) {
      this.selectedKr = await backend_fetch("/key_result/" + kr.id)
      this.selectedKr_parent = kr
      this.selectedKr_parent.obj_state = obj_state
      this.openKrDialog = true
    },
    openObjective() {
      this.selectedObj = this.objective
      this.openObjDialog = true
    },
    async addKeyResult() {
      const requestOptions = {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({name: this.newKr.name, description: this.newKr.description, objective_id: this.objective.id})
      }
      const body = await backend_fetch("/key_result", requestOptions)
      this.objective.key_results.push(body)
      this.openAddKrDialog = false
    },
  },
  components: {
    KeyResultDialog,
    ObjectiveDialog,
  }
}
</script>
<template>
  <v-card class="obj" :class="objective.state" width="300" elevation="3" shaped :key="objective.id"
          @mouseover="focused = true"
          @mouseleave="focused = false"
  >
    <ObjectiveDialog :obj="selectedObj" v-model="openObjDialog" v-on:close="this.openObjDialog=false" v-on:selectTab="selectTab"/>
    <KeyResultDialog :kr="selectedKr" :kr_parent="selectedKr_parent" v-model="openKrDialog" v-on:close="this.openKrDialog=false" />

    <v-card-title>{{objective.name}}</v-card-title>
    <v-card-text v-html="string_to_html(objective.description)"/>

    <v-icon class="objEdit" icon="mdi-pencil-circle-outline" large
            v-if="focused"
            @click="openObjective()"/>

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
      <v-dialog v-model="openAddKrDialog" width="300">
        <template v-slot:activator="{ props }">
          <v-btn color="primary" v-bind="props">
            <v-icon icon="mdi-plus" large/>
          </v-btn>
        </template>
        <v-card>
          <v-text-field label="Name" v-model="newKr.name"/>
          <v-text-field label="Description" v-model="newKr.description"/>
          <v-card-actions>
            <v-btn block @click="addKeyResult" :disabled="!newKr.name">Add</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>

    </v-card-actions>
  </v-card>
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
</style>