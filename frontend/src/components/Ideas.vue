<script setup>
import {nextTick, ref} from 'vue'
import {api} from '@/services/apiClient'
import DialogCard from '@/dialogs/DialogCard.vue'
import AddIdeaDialog from '@/dialogs/AddIdeaDialog.vue'
import Editable from '@/components/Editable.vue'

const props = defineProps({
  valueId: Number,
  subvalues: {
    type: Array,
    default: () => [],
  },
})
const emit = defineEmits(['created', 'updated', 'subvalue-updated', 'subvalue-deleted', 'deleted'])

const selectedIdeaId = ref(null)
const ideaPendingDeletionId = ref(null)
const openAddIdeaDialogId = ref(null)
const editingIdeaId = ref(null)
const editingSubvalueId = ref(null)
const subvaluePendingDeletionId = ref(null)
const draftIdea = ref({name: '', description: ''})
const ideaEditor = ref(null)
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

function ideaKey(subvalue, idea) {
  return subvalue.id + ':' + idea.id
}

async function startEditing(subvalue, idea) {
  if (isSubmitting.value || editingIdeaId.value === ideaKey(subvalue, idea)) return
  editingIdeaId.value = ideaKey(subvalue, idea)
  draftIdea.value = {name: idea.name, description: idea.description}
  await nextTick()
  ideaEditor.value?.querySelector('input')?.focus()
}

function cancelEditing() {
  editingIdeaId.value = null
}

async function saveIdea(subvalue, idea) {
  if (isSubmitting.value || editingIdeaId.value !== ideaKey(subvalue, idea)) return
  if (!draftIdea.value.name.trim()) return

  if (draftIdea.value.name === idea.name && draftIdea.value.description === idea.description) {
    cancelEditing()
    return
  }

  isSubmitting.value = true
  submissionError.value = null
  try {
    const updatedIdea = await api.put(
        '/value/' + props.valueId + '/subvalue/' + subvalue.id + '/idea/' + idea.id,
        draftIdea.value,
    )
    emit('updated', {subvalueId: subvalue.id, idea: updatedIdea})
    cancelEditing()
  } catch (error) {
    submissionError.value = error.message
  } finally {
    isSubmitting.value = false
  }
}

function saveOnUnfocus(event, subvalue, idea) {
  if (!event.currentTarget.contains(event.relatedTarget)) saveIdea(subvalue, idea)
}

async function updateSubvalue(subvalue, name) {
  if (isSubmitting.value) return false
  isSubmitting.value = true
  submissionError.value = null
  try {
    const updatedSubvalue = await api.put('/value/' + props.valueId + '/subvalue/' + subvalue.id, {name})
    emit('subvalue-updated', updatedSubvalue)
    return true
  } catch (error) {
    submissionError.value = error.message
    return false
  } finally {
    isSubmitting.value = false
  }
}

async function deleteSubvalue(subvalue) {
  if (isSubmitting.value) return
  isSubmitting.value = true
  submissionError.value = null
  try {
    await api.delete('/value/' + props.valueId + '/subvalue/' + subvalue.id)
    subvaluePendingDeletionId.value = null
    emit('subvalue-deleted', subvalue.id)
  } catch (error) {
    submissionError.value = error.message
  } finally {
    isSubmitting.value = false
  }
}

</script>

<template>
  <div class="ideaLists">
    <v-card v-for="subvalue in subvalues" :key="subvalue.id" width="300" elevation="3" shaped class="subvalueList">
      <v-card-title class="subvalueListHeader">
        <Editable v-if="subvalue.id !== '0'" class="subvalueNameEditor" :value="subvalue.name" label="Name" hide-details
                  :cancel-editing="subvaluePendingDeletionId === subvalue.id"
                  :submit="(name) => updateSubvalue(subvalue, name)"
                  @editing-changed="(isEditing) => {
                    if (isEditing) editingSubvalueId = subvalue.id
                    else if (editingSubvalueId === subvalue.id) editingSubvalueId = null
                  }">
          <template #display="{ startEditing }">
            <span class="subvalueName" @click="startEditing">{{ subvalue.name }}</span>
          </template>
        </Editable>
        <span v-else/>
        <AddIdeaDialog v-if="editingSubvalueId !== subvalue.id && subvaluePendingDeletionId !== subvalue.id"
            :model-value="openAddIdeaDialogId === subvalue.id"
            :value-id="valueId"
            :subvalue-id="subvalue.id"
            @update:model-value="openAddIdeaDialogId = $event ? subvalue.id : null"
            @created="(idea) => emit('created', {subvalueId: subvalue.id, idea})"
        />
        <v-btn v-else-if="editingSubvalueId === subvalue.id" class="deleteSubvalue" variant="text"
               icon="mdi-delete" @mousedown.prevent @click="subvaluePendingDeletionId = subvalue.id"/>
        <v-dialog v-if="subvalue.id !== '0'"
            :model-value="subvaluePendingDeletionId === subvalue.id"
            @update:model-value="subvaluePendingDeletionId = $event ? subvalue.id : null"
            width="300"
        >
          <DialogCard :error="submissionError">
            <v-card-title class="text-h5">Delete “{{ subvalue.name }}”?</v-card-title>
            <v-card-text>This will permanently delete {{ subvalue.ideas.length }} idea<span v-if="subvalue.ideas.length !== 1">s</span> in this list.</v-card-text>
            <v-card-actions>
              <v-btn :disabled="isSubmitting" @click="subvaluePendingDeletionId = null">Cancel</v-btn>
              <v-btn color="error" :disabled="isSubmitting" @click="deleteSubvalue(subvalue)">Delete</v-btn>
            </v-card-actions>
          </DialogCard>
        </v-dialog>
      </v-card-title>
      <v-list class="subvalueIdeas">
        <v-list-item v-for="idea in subvalue.ideas" :key="idea.id" class="ideaItem"
                     @mouseover="selectedIdeaId = subvalue.id + ':' + idea.id"
                     @mouseleave="selectedIdeaId = null">
          <v-list-item-content>
            <div v-if="editingIdeaId !== ideaKey(subvalue, idea)" class="idea" @click="startEditing(subvalue, idea)">
              <div class="ideaName">{{ idea.name }}</div>
              <div v-if="idea.description" class="ideaDescription">{{ idea.description }}</div>

              <v-icon v-if="selectedIdeaId === subvalue.id + ':' + idea.id"
                      class="deleteIdea" icon="mdi-delete" size="18"
                      @click.stop="ideaPendingDeletionId = ideaKey(subvalue, idea)"/>
              <v-dialog
                  :model-value="ideaPendingDeletionId === ideaKey(subvalue, idea)"
                  @update:model-value="ideaPendingDeletionId = $event ? ideaKey(subvalue, idea) : null"
                  width="300"
              >
                <DialogCard :error="submissionError">
                  <v-card-title class="text-h5 grey lighten-2">Delete Idea?</v-card-title>
                  <v-card-text>{{ idea.name }}</v-card-text>
                  <v-card-actions>
                    <v-btn block :disabled="isSubmitting" @click="deleteIdea(subvalue, idea)">Confirm</v-btn>
                  </v-card-actions>
                </DialogCard>
              </v-dialog>
            </div>
            <div v-else :ref="(element) => ideaEditor = element" class="ideaEditor"
                 @focusout="saveOnUnfocus($event, subvalue, idea)">
              <v-text-field v-model="draftIdea.name" label="Name" hide-details
                            @keydown.enter.prevent="saveIdea(subvalue, idea)"
                            @keydown.esc.prevent="cancelEditing"/>
              <v-textarea v-model="draftIdea.description" label="Description" rows="1" auto-grow hide-details
                          @keydown.enter.prevent="saveIdea(subvalue, idea)"
                          @keydown.esc.prevent="cancelEditing"/>
            </div>
          </v-list-item-content>
        </v-list-item>
      </v-list>
    </v-card>
  </div>
</template>

<style scoped>
.ideaLists {
  align-items: flex-start;
  display: flex;
  gap: 12px;
  box-sizing: border-box;
  min-width: 100%;
  padding: 0 12px 12px;
  width: max-content;
}

.subvalueList {
  display: flex;
  flex-direction: column;
  max-height: calc(100vh - 82px);
}

.subvalueIdeas {
  flex: 0 1 auto;
  min-height: 0;
  overflow-y: auto;
  padding-bottom: 16px;
}

.subvalueListHeader {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.subvalueName {
  cursor: pointer;
}

.subvalueNameEditor {
  flex: 1;
  min-width: 0;
}

.subvalueNameEditor :deep(.text),
.subvalueNameEditor :deep(.v-input) {
  width: 100%;
}

.deleteSubvalue {
  color: rgb(var(--v-theme-error));
}

.idea {
  padding: 8px 0;
  position: relative;
}

.ideaItem:first-child .idea {
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.12);
}

.ideaItem .idea {
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.12);
}

.ideaName {
  cursor: pointer;
  font-size: 0.9375rem;
  font-weight: 500;
  padding-right: 28px;
}

.ideaDescription {
  cursor: pointer;
  color: rgba(var(--v-theme-on-surface), 0.72);
  font-size: 0.8125rem;
  font-weight: 400;
  margin-top: 2px;
  padding-right: 28px;
}

.ideaEditor {
  padding: 8px 0;
}

.ideaItem {
  min-height: 0 !important;
  padding-top: 0 !important;
  padding-bottom: 0 !important;
}

.deleteIdea {
  color: rgba(var(--v-theme-on-surface), 0.65);
  position: absolute;
  right: 0;
  top: 8px;
}
</style>
