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
const selectedIdeaId = ref(null)
const ideaPendingDeletionId = ref(null)
const isSubmitting = ref(false)

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
  if (isSubmitting.value) return
  isSubmitting.value = true
  try {
    const body = await api.post('/value/' + props.valueId + '/idea', {idea: newIdea.value})
    ideas.value.push({id: body.new_id, value: body.idea})
    newIdeaDialog.value = false
    newIdea.value = ''
  } catch (error) {
    setError(error)
  } finally {
    isSubmitting.value = false
  }
}

async function deleteIdea(idea) {
  if (isSubmitting.value) return
  isSubmitting.value = true
  try {
    await api.delete('/value/' + props.valueId + '/idea/' + idea.id)
    ideas.value.splice(ideas.value.indexOf(idea), 1)
    ideaPendingDeletionId.value = null
  } catch (error) {
    setError(error)
  } finally {
    isSubmitting.value = false
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
        <v-list-item-content v-for="idea in ideas" :key="idea.id"
                             @mouseover="selectedIdeaId = idea.id"
                             @mouseleave="selectedIdeaId = null">
          <div class="idea">
            <v-list-item>{{idea.value}}</v-list-item>

            <v-dialog
                :model-value="ideaPendingDeletionId === idea.id"
                @update:model-value="ideaPendingDeletionId = $event ? idea.id : null"
                width="300"
            >
              <template v-slot:activator="{ props }">
                <v-icon icon="mdi-delete" large v-bind="props" v-if="selectedIdeaId === idea.id"/>
              </template>

              <v-card>
                <v-card-title class="text-h5 grey lighten-2">
                  Delete Idea?
                </v-card-title>
                <v-card-text>
                  {{ idea.value }}
                </v-card-text>
                <v-card-actions>
                  <v-btn block :disabled="isSubmitting" @click="deleteIdea(idea)">Confirm</v-btn>
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
              <v-btn block :disabled="isSubmitting || !newIdea" @click="addIdea">Add</v-btn>
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
