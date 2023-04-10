<script>
import {backend_fetch} from "@/properties";

export default {
  name: "Ideas",
  props: {
    valueId: Number
  },
  data() {
    return {
      ideas: Object,
      loading: true,
      newIdeaDialog: false,
      newIdea: "",
      selectedIdea: -1,
      confirmDeletionDialogs: [],
    }
  },
  methods: {
    async loadData() {
      const response = await backend_fetch("/value/" + this.valueId + "/ideas")
      if (response.ok){
        this.ideas = await response.json()
        this.loading = false
      } else {
        const body = await response.text()
        console.error(body)
        // alert(body)
      }
    },
    async addIdea() {
      const requestOptions = {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({value_id: this.valueId, idea: this.newIdea})
      }
      const response = await backend_fetch("/idea", requestOptions);
      const body = await response.json();
      if (response.ok){
        this.ideas.push({id: body.new_id, value: body.idea})
        this.newIdeaDialog = false
        this.newIdea = ""
      } else {
        console.error(body)
        alert(body)
      }
    },
    async deleteIdea(idea, index){
      const requestOptions = {
        method: "DELETE",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({value_id: this.valueId, idea_id: idea.id})
      }
      const response = await backend_fetch("/idea", requestOptions);
      const body = await response.json();
      if (response.ok){
        this.ideas.splice(this.ideas.indexOf(idea), 1);
        this.confirmDeletionDialogs[index] = false
      } else {
        console.error(body)
        alert(body)
      }
    },
  },
  mounted() {
    this.loadData()
  }
}
</script>
<template>
  <v-card class="obj" width="300" elevation="3" shaped>
    <v-card-title>Ideas</v-card-title>
    <v-progress-circular v-if="loading" style="margin: 0 0 10px 30px" indeterminate color="primary"></v-progress-circular>
    <div v-else>
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
    </div>
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