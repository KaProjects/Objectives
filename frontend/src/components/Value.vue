<script setup>
import { app_state } from '@/main'

</script>
<script>
import {properties} from "@/properties";
import {app_state} from "@/main";

export default {
  name: "Value",
  data() {
    return {
      value: Object,
      newIdeaDialog: false,
      newIdea: "",
      selectedIdea: -1,
    }
  },
  methods: {
    async loadData() {
      const res = await fetch("http://" + properties.host + ":" + properties.port + "/value/" + app_state.value.id);
      this.value = await res.json();
    },
    addKeyResult() {
      alert('add KR')
    },
    async addIdea() {
      const requestOptions = {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({value_id: this.value.id, idea: this.newIdea})
      };

      const res = await fetch("http://" + properties.host + ":" + properties.port + "/idea/add", requestOptions);
      const newIdea = await res.json();

      this.value.ideas.push({id: newIdea.new_id, value: newIdea.idea})

      this.newIdeaDialog = false
      this.newIdea = ""
    },
    async deleteIdea(idea){
      const requestOptions = {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({value_id: this.value.id, idea_id: idea.id})
      };

      const res = await fetch("http://" + properties.host + ":" + properties.port + "/idea/del", requestOptions);
      if (res.ok)
        this.value.ideas.splice(this.value.ideas.indexOf(idea), 1);
      else
        alert(res.status);


    }
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

      <v-card class="obj" width="300" elevation="3" shaped>
        <v-card-title>Ideas</v-card-title>
        <v-list-item>
          <v-list-item-content v-for="(idea, index) in value.ideas"
                               @mouseover="selectedIdea = index"
                               @mouseleave="selectedIdea = -1">
            <div class="idea">
              <v-list-item class="inLine">{{idea.value}}</v-list-item>
              <v-icon v-if="selectedIdea === index"
                     @click="deleteIdea(idea)"
                      icon="mdi-delete">
              </v-icon>
            </div>
          </v-list-item-content>
        </v-list-item>
        <v-card-actions>
          <v-dialog
              v-model="newIdeaDialog"
              width="300"
          >
            <template v-slot:activator="{ props }">
              <v-btn color="primary" v-bind="props">
                <v-icon icon="mdi-plus" large/>
              </v-btn>
            </template>

            <v-card>
              <v-text-field
                  label="Idea*"
                  v-model="newIdea"
                  required
              ></v-text-field>
              <v-card-actions>
                <v-btn block @click="addIdea">Add</v-btn>
              </v-card-actions>
            </v-card>
          </v-dialog>
        </v-card-actions>
      </v-card>

      <v-card class="obj"
              v-for="objective in value.objectives" :key="objective.id"
              :class="objective.state"
              width="300" elevation="3" shaped
      >
        <v-card-title>{{objective.name}}</v-card-title>
        <v-card-text>
          {{objective.description}}
        </v-card-text>
        <v-list-item v-for="key_result in objective.key_results"
                     class="kr" :class="key_result.state">
          <v-list-item-content >
            <v-icon icon="mdi-check-bold" v-if="key_result.state === 'success'" />
            <v-icon icon="mdi-cancel" v-if="key_result.state === 'failed'"/>
            <v-list-item-title class="inLine">{{key_result.name}}</v-list-item-title>
          </v-list-item-content>
        </v-list-item>
        <v-card-actions v-if="objective.state === 'active'">
          <v-btn outlined rounded color="primary">
            <v-icon icon="mdi-plus" large @click="addKeyResult"/>
          </v-btn>
        </v-card-actions>
      </v-card>


  </div>


</template>

<style scoped>

.idea {
  border: 1px #d9e0e1 solid;
}
.idea:hover {
  border: 2px #d9e0e1 solid;
}
.idea > .v-icon {
  position: absolute;
  right: 0px;
}

.kr {
  border: #2c3e50;
  border-style: solid;
}
.kr:hover {
  border-width: 3px;
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