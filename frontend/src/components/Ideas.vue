<script setup>
import {ref} from 'vue'
import {api} from '@/services/apiClient'
import DialogCard from '@/dialogs/DialogCard.vue'

const props = defineProps({
  valueId: Number,
  subvalues: {
    type: Array,
    default: () => [],
  },
})
const emit = defineEmits(['deleted'])

const selectedIdeaId = ref(null)
const ideaPendingDeletionId = ref(null)
const isSubmitting = ref(false)
const submissionError = ref(null)

async function deleteIdea(subvalue, idea) {
  if (isSubmitting.value) return
  isSubmitting.value = true
  submissionError.value = null
  try {
    await api.delete('/value/' + props.valueId + '/subvalue/' + subvalue.id + '/idea/' + idea.id)
    ideaPendingDeletionId.value = null
    emit('deleted', {subvalueId: subvalue.id, ideaId: idea.id})
  } catch (error) {
    submissionError.value = error.message
  } finally {
    isSubmitting.value = false
  }
}

</script>

<template>
  <div class="ideaLists">
    <v-card v-for="subvalue in subvalues" :key="subvalue.id" width="300" elevation="3" shaped
            max-height="calc(100vh - 70px)" class="subvalueList">
      <v-card-title>{{ subvalue.name }}</v-card-title>
      <v-list-item v-for="idea in subvalue.ideas" :key="idea.id" class="ideaItem"
                   @mouseover="selectedIdeaId = subvalue.id + ':' + idea.id"
                   @mouseleave="selectedIdeaId = null">
        <v-list-item-content>
          <div class="idea">
            {{ idea.name }}

            <v-dialog
                :model-value="ideaPendingDeletionId === subvalue.id + ':' + idea.id"
                @update:model-value="ideaPendingDeletionId = $event ? subvalue.id + ':' + idea.id : null"
                width="300"
            >
              <template v-slot:activator="{ props }">
                <v-icon class="deleteIdea" icon="mdi-delete" large v-bind="props"
                        v-if="selectedIdeaId === subvalue.id + ':' + idea.id"/>
              </template>

              <DialogCard :error="submissionError">
                <v-card-title class="text-h5 grey lighten-2">Delete Idea?</v-card-title>
                <v-card-text>{{ idea.name }}</v-card-text>
                <v-card-actions>
                  <v-btn block :disabled="isSubmitting" @click="deleteIdea(subvalue, idea)">Confirm</v-btn>
                </v-card-actions>
              </DialogCard>
            </v-dialog>
          </div>
        </v-list-item-content>
      </v-list-item>
    </v-card>
  </div>
</template>

<style scoped>
.ideaLists {
  display: flex;
  gap: 12px;
}

.subvalueList {
  overflow-y: auto;
}

.idea {
  border: 1px #d9e0e1 solid;
  padding: 1px 5px;
}

.ideaItem {
  min-height: 0 !important;
  padding-top: 5px !important;
  padding-bottom: 0 !important;
}

.deleteIdea {
  position: absolute;
  right: 0;
}
</style>
