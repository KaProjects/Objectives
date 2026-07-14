<script setup>
import {onMounted, ref} from 'vue'
import {api} from '@/services/apiClient'
import {setError} from '@/state/appState'

const props = defineProps({
  valueId: Number,
})

const ideas = ref([])
const loading = ref(true)
const newIdeaDialog = ref(false)
const newIdea = ref('')
const selectedIdea = ref(-1)
const confirmDeletionDialogs = ref([])

async function loadData() {
  try {
    ideas.value = await api.get('/value/' + props.valueId + '/idea')
  } catch (error) {
    setError(error)
  } finally {
    loading.value = false
  }
}

async function addIdea() {
  try {
    const body = await api.post('/value/' + props.valueId + '/idea', {idea: newIdea.value})
    ideas.value.push({id: body.new_id, value: body.idea})
    newIdeaDialog.value = false
    newIdea.value = ''
  } catch (error) {
    setError(error)
  }
}

async function deleteIdea(idea, index) {
  try {
    await api.delete('/value/' + props.valueId + '/idea/' + idea.id)
    ideas.value.splice(ideas.value.indexOf(idea), 1)
    confirmDeletionDialogs.value[index] = false
  } catch (error) {
    setError(error)
  }
}

onMounted(loadData)
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
