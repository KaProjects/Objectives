<script setup>
import {nextTick, ref} from 'vue'
import {api} from '@/services/apiClient'
import DialogCard from '@/dialogs/DialogCard.vue'
import AddIdeaDialog from '@/dialogs/AddIdeaDialog.vue'
import Editable from '@/components/Editable.vue'

const props = defineProps({
  valueId: [String, Number],
  subvalues: {
    type: Array,
    default: () => [],
  },
})
const emit = defineEmits(['created', 'updated', 'moved', 'subvalue-updated', 'subvalue-deleted', 'create-objective', 'deleted'])

const selectedIdeaId = ref(null)
const ideaPendingDeletionId = ref(null)
const openAddIdeaDialogId = ref(null)
const editingIdeaId = ref(null)
const editingSubvalueId = ref(null)
const subvaluePendingDeletionId = ref(null)
const draggedIdea = ref(null)
const dragOverSubvalueId = ref(null)
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

function startDragging(event, subvalue, idea) {
  if (isSubmitting.value) {
    event.preventDefault()
    return
  }
  draggedIdea.value = {sourceSubvalueId: subvalue.id, idea}
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/plain', idea.id)
}

function endDragging() {
  draggedIdea.value = null
  dragOverSubvalueId.value = null
}

function markDragOver(subvalue) {
  if (draggedIdea.value?.sourceSubvalueId !== subvalue.id) {
    dragOverSubvalueId.value = subvalue.id
  }
}

async function moveDraggedIdea(targetSubvalue) {
  const dragged = draggedIdea.value
  endDragging()
  if (!dragged || dragged.sourceSubvalueId === targetSubvalue.id) return

  isSubmitting.value = true
  submissionError.value = null
  try {
    const movedIdea = await api.put(
        '/value/' + props.valueId + '/subvalue/' + dragged.sourceSubvalueId + '/idea/' + dragged.idea.id + '/move',
        {target_subvalue_id: targetSubvalue.id},
    )
    emit('moved', {
      sourceSubvalueId: dragged.sourceSubvalueId,
      targetSubvalueId: targetSubvalue.id,
      idea: movedIdea,
    })
  } catch (error) {
    submissionError.value = error.message
  } finally {
    isSubmitting.value = false
  }
}

</script>

<template>
  <div class="ideaLists">
    <v-card v-for="subvalue in subvalues" :key="subvalue.id" width="300" elevation="3" shaped class="subvalueList"
            :class="{dragOver: dragOverSubvalueId === subvalue.id}"
            @dragover.prevent="markDragOver(subvalue)"
            @drop.prevent="moveDraggedIdea(subvalue)">
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
            <div v-if="editingIdeaId !== ideaKey(subvalue, idea)" class="idea"
                 :class="{shortIdea: !idea.description, draggingIdea: draggedIdea?.idea.id === idea.id && draggedIdea?.sourceSubvalueId === subvalue.id}"
                 :draggable="!isSubmitting"
                 @dragstart="startDragging($event, subvalue, idea)"
                 @dragend="endDragging"
                 @click="startEditing(subvalue, idea)">
              <div class="ideaContent">
                <div class="ideaName">{{ idea.name }}</div>
                <div v-if="idea.description" class="ideaDescription">{{ idea.description }}</div>
              </div>

              <div v-if="selectedIdeaId === subvalue.id + ':' + idea.id" class="ideaActions">
                <v-icon class="createObjectiveFromIdea" icon="mdi-flag-plus-outline" size="18"
                        @click.stop="emit('create-objective', {subvalueId: subvalue.id, idea})"/>
                <v-icon class="deleteIdea" icon="mdi-delete" size="18"
                        @click.stop="ideaPendingDeletionId = ideaKey(subvalue, idea)"/>
              </div>
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
  flex: 0 0 300px;
  flex-direction: column;
  max-height: calc(100vh - 82px);
  transition: box-shadow 160ms ease, transform 160ms ease;
}

.subvalueList.dragOver {
  box-shadow: 0 0 0 2px rgb(var(--v-theme-primary));
  transform: translateY(-2px);
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
  align-items: flex-start;
  display: flex;
  padding: 8px 0;
  position: relative;
  transition: opacity 160ms ease, transform 160ms ease;
}

.idea.draggingIdea {
  opacity: 0.45;
  transform: scale(0.98);
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
}

.ideaDescription {
  cursor: pointer;
  color: rgba(var(--v-theme-on-surface), 0.72);
  font-size: 0.8125rem;
  font-weight: 400;
  margin-top: 2px;
}

.ideaContent {
  flex: 1;
  min-width: 0;
}

.ideaActions {
  display: flex;
  flex-direction: column;
  flex: 0 0 18px;
  gap: 4px;
  margin-left: 8px;
}

.shortIdea .ideaActions {
  flex-basis: 40px;
  flex-direction: row;
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
}

.createObjectiveFromIdea {
  color: rgba(var(--v-theme-on-surface), 0.65);
}
</style>
