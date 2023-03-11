<script setup>
import { app_state } from '@/main'

</script>
<script>
import {properties} from "@/properties";
import {app_state} from "@/main";
import Ideas from "@/components/Ideas.vue";
import KeyResultDialog from "@/components/KeyResultDialog.vue";

export default {
  name: "Value",
  data() {
    return {
      value: Object,
      newKrDialogs: [],
      newKr: {name: "", description: ""},
      selectedKr: Object,
      selectedKr_parent: Object
    }
  },
  methods: {
    async loadData() {
      const res = await fetch("http://" + properties.host + ":" + properties.port + "/value/" + app_state.value.id);
      this.value = await res.json();
      for (let i = 0; i < this.value.objectives.length; i++) {
        this.newKrDialogs[i] = false
      }

      // const res_ideas = await fetch("http://" + properties.host + ":" + properties.port + "/value/" + app_state.value.id + "/ideas");
      // this.ideas = await res_ideas.json();




    },
    async addKeyResult(objective_id, index) {
      const requestOptions = {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({name: this.newKr.name, description: this.newKr.description, objective_id: objective_id})
      };

      const response = await fetch("http://" + properties.host + ":" + properties.port + "/kr/add", requestOptions);
      if (response.ok){
        const newKr = await response.json();
        this.value.objectives[index].key_results.push(newKr)
      } else {
        const error = await response.json()
        console.error(error)
        alert(error.error)
      }

      this.newKrDialogs[index] = false
      this.newKr = {name: "", description: ""}
    },
    async openKeyResult(kr) {
      const res = await fetch("http://" + properties.host + ":" + properties.port + "/kr/" + kr.id);
      this.selectedKr = await res.json();
      this.selectedKr_parent = kr
      app_state.krDialogToggle = true
    }
  },
  components: {
    Ideas,
    KeyResultDialog,
  },
  mounted() {
    this.loadData()
  }
}
</script>

<template>
  <div>
    <v-icon icon="mdi-arrow-left" large @click="app_state.unselect_value()"/>
    <h1>{{value.name}}</h1>

    <Ideas :valueId="app_state.value.id" />

    <KeyResultDialog :kr="selectedKr" :kr_parent="selectedKr_parent" />

    <v-card class="obj"
              v-for="(objective, index) in value.objectives" :key="objective.id"
              :class="objective.state"
              width="300" elevation="3" shaped
      >
        <v-card-title>{{objective.name}}</v-card-title>
        <v-card-text>
          {{objective.description}}
        </v-card-text>
        <v-list-item v-for="key_result in objective.key_results"
                     class="kr" :class="key_result.state"
                     @click="openKeyResult(key_result)">
          <v-list-item-content>
            <v-icon icon="mdi-check-bold" v-if="key_result.state === 'success'" />
            <v-icon icon="mdi-cancel" v-if="key_result.state === 'failed'"/>
            <v-list-item-title class="inLine">{{key_result.name}}</v-list-item-title>
          </v-list-item-content>
        </v-list-item>
        <v-card-actions v-if="objective.state === 'active'">
          <v-dialog
              v-model="newKrDialogs[index]"
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
                <v-btn block @click="addKeyResult(objective.id, index)">Add</v-btn>
              </v-card-actions>
            </v-card>
          </v-dialog>

        </v-card-actions>
      </v-card>


  </div>


</template>

<style scoped>



.kr {
  border: #2c3e50;
  border-style: solid;
  border-width: 1px;
}
.kr:hover {
  border-width: 2px;
}
.kr.success {
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
}
.obj.active {
  display: inline-block;
  background: #b2d1ec;
}
.obj.failed {
  display: inline-block;
  background: #dc1a1a;
}
.obj.achieved {
  display: inline-block;
  background: #84e184;
}

</style>