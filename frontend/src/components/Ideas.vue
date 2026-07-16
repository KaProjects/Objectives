<script setup>
import {onMounted, ref} from 'vue'
import {api} from '@/services/apiClient'
import {setError} from '@/state/appState'
import DialogCard from '@/dialogs/DialogCard.vue'

const props = defineProps({
  valueId: Number,
})

const ideas = ref([])
const loading = ref(true)
const selectedIdeaId = ref(null)
const ideaPendingDeletionId = ref(null)
const isSubmitting = ref(false)
const submissionError = ref(null)

async function loadData() {
  try {
    ideas.value = await api.get('/value/' + props.valueId + '/idea')
  } catch (error) {
    setError(error)
  } finally {
    loading.value = false
  }
}

function addCreatedIdea(idea) {
  ideas.value.push(idea)
}

async function deleteIdea(idea) {
  if (isSubmitting.value) return
  isSubmitting.value = true
  submissionError.value = null
  try {
    await api.delete('/value/' + props.valueId + '/idea/' + idea.id)
    ideas.value.splice(ideas.value.indexOf(idea), 1)
    ideaPendingDeletionId.value = null
  } catch (error) {
    submissionError.value = error.message
  } finally {
    isSubmitting.value = false
  }
}

onMounted(loadData)

defineExpose({addCreatedIdea})
</script>
<template>
  <v-card width="300" elevation="3" shaped max-height="calc(100vh - 70px)" style="overflow-y:scroll;">
    <v-card-title>Ideas</v-card-title>
    <v-progress-circular v-if="loading" style="margin: 0 0 10px 30px" indeterminate
                         color="primary"></v-progress-circular>
    <div v-else>
      <v-list-item>
        <v-list-item-content v-for="idea in ideas" :key="idea.id"
                             @mouseover="selectedIdeaId = idea.id"
                             @mouseleave="selectedIdeaId = null">
          <div class="idea">
            <v-list-item>{{ idea.value }}</v-list-item>

            <v-dialog
                :model-value="ideaPendingDeletionId === idea.id"
                @update:model-value="ideaPendingDeletionId = $event ? idea.id : null"
                width="300"
            >
              <template v-slot:activator="{ props }">
                <v-icon icon="mdi-delete" large v-bind="props" v-if="selectedIdeaId === idea.id"/>
              </template>

              <DialogCard :error="submissionError">
                <v-card-title class="text-h5 grey lighten-2">
                  Delete Idea?
                </v-card-title>
                <v-card-text>
                  {{ idea.value }}
                </v-card-text>
                <v-card-actions>
                  <v-btn block :disabled="isSubmitting" @click="deleteIdea(idea)">Confirm</v-btn>
                </v-card-actions>
              </DialogCard>
            </v-dialog>

          </div>
        </v-list-item-content>
      </v-list-item>
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
