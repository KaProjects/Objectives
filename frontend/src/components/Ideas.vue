<script>
import {properties} from "@/properties";

export default {
  name: "Ideas",
  props: {
    ideas: Object,
    valueId: Number
  },
  data() {
    return {
      newIdeaDialog: false,
      newIdea: "",
      selectedIdea: -1,
      confirmDeletionDialogs: [],
    }
  },
  methods: {
    async addIdea() {
      const requestOptions = {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({value_id: this.valueId, idea: this.newIdea})
      };

      const res = await fetch("http://" + properties.host + ":" + properties.port + "/idea/add", requestOptions);
      const newIdea = await res.json();

      this.ideas.push({id: newIdea.new_id, value: newIdea.idea})

      this.newIdeaDialog = false
      this.newIdea = ""
    },
    async deleteIdea(idea, index){
      const requestOptions = {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({value_id: this.valueId, idea_id: idea.id})
      };

      const res = await fetch("http://" + properties.host + ":" + properties.port + "/idea/del", requestOptions);
      if (res.ok)
        this.ideas.splice(this.ideas.indexOf(idea), 1);
      else
        alert(res.status);

      this.confirmDeletionDialogs[index] = false
    },
  }
}
</script>
<template>
  <v-card class="obj" width="300" elevation="3" shaped>
    <v-card-title>Ideas</v-card-title>
    <v-list-item>
      <v-list-item-content v-for="(idea, index) in ideas"
                           @mouseover="selectedIdea = index"
                           @mouseleave="selectedIdea = -1">
        <div class="idea">
          <v-list-item class="inLine">{{idea.value}}</v-list-item>

          <v-dialog
              v-model="confirmDeletionDialogs[index]"
              width="300"
          >
            <template v-slot:activator="{ props }">
              <v-icon icon="mdi-delete" large v-bind="props" v-if="selectedIdea === index"/>
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
              label="Idea"
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
.inLine {
  display: inline-block;
}
</style>