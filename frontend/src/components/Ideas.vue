<script>
import {backend_fetch} from "@/utils";

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
      await backend_fetch("/value/" + this.valueId + "/idea")
        .then(async response => {
          if (response.ok){
            this.ideas = await response.json()
            this.loading = false
          } else {
            this.handleFetchError(await response.text())
          }})
        .catch(error => this.handleFetchError(error))
    },
    async addIdea() {
      const requestOptions = {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({idea: this.newIdea})
      }
      await backend_fetch("/value/" + this.valueId + "/idea", requestOptions)
        .then(async response => {
          if (response.ok){
            const body = await response.json()
            this.ideas.push({id: body.new_id, value: body.idea})
            this.newIdeaDialog = false
            this.newIdea = ""
          } else {
            this.handleFetchError(await response.text())
          }})
        .catch(error => this.handleFetchError(error))
    },
    handleFetchError(error){
      console.error(error)
      alert(error)
    },
    async deleteIdea(idea, index){
      await backend_fetch("/value/" + this.valueId + "/idea/" + idea.id, {method: "DELETE"})
        .then(async response => {
          if (response.ok){
            this.ideas.splice(this.ideas.indexOf(idea), 1);
            this.confirmDeletionDialogs[index] = false
          } else {
            this.handleFetchError(await response.text())
          }})
        .catch(error => this.handleFetchError(error))
    },
  },
  mounted() {
    this.loadData()
  }
}
</script>
<template>
  <v-card width="300" elevation="3" shaped max-height="calc(100vh - 70px)" style="overflow-y:scroll;">
    <v-card-title>Ideas</v-card-title>
    <v-progress-circular v-if="loading" style="margin: 0 0 10px 30px" indeterminate color="primary"></v-progress-circular>
    <div v-else>
      <v-list-item>
        <v-list-item-content v-for="(idea, index) in ideas"
                             @mouseover="selectedIdea = index"
                             @mouseleave="selectedIdea = -1">
          <div class="idea">
            <v-list-item>{{idea.value}}</v-list-item>

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

</style>