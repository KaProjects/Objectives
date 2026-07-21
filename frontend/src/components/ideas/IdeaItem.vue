<script setup lang="ts">
import {nextTick, ref, watch} from 'vue'
import {api} from '@/services/apiClient'
import DialogCard from '@/dialogs/DialogCard.vue'
import type {EntityId, Idea} from '@/types/domain'

type IdeaDraft = Pick<Idea, 'name' | 'description'>

const props = withDefaults(defineProps<{
  valueId: EntityId
  subvalueId: EntityId
  idea: Idea
  disabled?: boolean
  dragging?: boolean
  moving?: boolean
}>(), {
  disabled: false,
  dragging: false,
  moving: false,
})
const emit = defineEmits<{
  (event: 'updated', idea: Idea): void
  (event: 'deleted', ideaId: string): void
  (event: 'create-objective' | 'move-requested', idea: Idea): void
  (event: 'drag-start', payload: {event: DragEvent; idea: Idea}): void
  (event: 'drag-end' | 'resized'): void
}>()

const isEditing = ref(false)
const draftIdea = ref<IdeaDraft>({name: '', description: ''})
const ideaEditor = ref<HTMLElement | null>(null)
const confirmDeletion = ref(false)
const actionsMenuOpen = ref(false)
const isSubmitting = ref(false)
const submissionError = ref<string | null>(null)

async function startEditing() {
  if (props.disabled || isSubmitting.value || isEditing.value) return
  draftIdea.value = {name: props.idea.name, description: props.idea.description}
  isEditing.value = true
  await nextTick()
  ideaEditor.value?.querySelector('input')?.focus()
  emit('resized')
}

function cancelEditing() {
  isEditing.value = false
  nextTick(() => emit('resized'))
}

async function saveIdea() {
  if (props.disabled || isSubmitting.value || !isEditing.value) return
  if (!draftIdea.value.name.trim()) return

  if (draftIdea.value.name === props.idea.name && draftIdea.value.description === props.idea.description) {
    cancelEditing()
    return
  }

  isSubmitting.value = true
  submissionError.value = null
  try {
    const updatedIdea = await api.put<Idea, IdeaDraft>(
        `/value/${props.valueId}/subvalue/${props.subvalueId}/idea/${props.idea.id}`,
        draftIdea.value,
    )
    emit('updated', updatedIdea)
    cancelEditing()
  } catch (error) {
    submissionError.value = error instanceof Error ? error.message : String(error)
  } finally {
    isSubmitting.value = false
  }
}

function saveOnUnfocus(event: FocusEvent) {
  const editor = event.currentTarget as HTMLElement
  if (!editor.contains(event.relatedTarget as Node | null)) saveIdea()
}

async function deleteIdea() {
  if (props.disabled || isSubmitting.value) return
  isSubmitting.value = true
  submissionError.value = null
  try {
    await api.delete(`/value/${props.valueId}/subvalue/${props.subvalueId}/idea/${props.idea.id}`)
    confirmDeletion.value = false
    emit('deleted', props.idea.id)
  } catch (error) {
    submissionError.value = error instanceof Error ? error.message : String(error)
  } finally {
    isSubmitting.value = false
  }
}

function closeActionsMenu() {
  actionsMenuOpen.value = false
}

function createObjective() {
  closeActionsMenu()
  emit('create-objective', props.idea)
}

function requestMove() {
  closeActionsMenu()
  emit('move-requested', props.idea)
}

function requestDeletion() {
  closeActionsMenu()
  confirmDeletion.value = true
}

function startDragging(event: DragEvent) {
  if (props.disabled || isSubmitting.value) {
    event.preventDefault()
    return
  }
  emit('drag-start', {event, idea: props.idea})
}

watch(() => draftIdea.value.description, () => nextTick(() => emit('resized')))
</script>

<template>
  <v-list-item class="ideaItem">
    <v-list-item-content>
      <div v-if="!isEditing"
           class="idea"
           :class="{shortIdea: !idea.description, draggingIdea: dragging, movingIdea: moving}"
           :draggable="!disabled && !isSubmitting"
           @dragstart="startDragging"
           @dragend="emit('drag-end')"
           @click="startEditing">
        <div class="ideaContent">
          <div class="ideaName">{{ idea.name }}</div>
          <div v-if="idea.description" class="ideaDescription">{{ idea.description }}</div>
        </div>

        <div class="ideaActions">
          <div class="desktopIdeaActions">
            <v-icon class="createObjectiveFromIdea" icon="mdi-flag-plus-outline" size="18"
                    @click.stop="emit('create-objective', idea)"/>
            <v-icon class="moveIdea" icon="mdi-arrow-right-bold-circle-outline" size="18"
                    @click.stop="emit('move-requested', idea)"/>
            <v-icon class="deleteIdea" icon="mdi-delete" size="18"
                    @click.stop="confirmDeletion = true"/>
          </div>
          <v-menu v-model="actionsMenuOpen">
            <template #activator="{props: menuProps}">
              <v-icon class="mobileIdeaActionsTrigger" icon="mdi-dots-vertical" v-bind="menuProps"/>
            </template>
            <v-list class="mobileIdeaActionsMenu" density="compact">
              <v-list-item prepend-icon="mdi-flag-plus-outline" title="Create Objective" @click="createObjective"/>
              <v-list-item prepend-icon="mdi-arrow-right-bold-circle-outline" title="Move to…" @click="requestMove"/>
              <v-list-item class="deleteIdeaMenuItem" prepend-icon="mdi-delete" title="Delete" @click="requestDeletion"/>
            </v-list>
          </v-menu>
        </div>

        <v-dialog v-model="confirmDeletion" width="300">
          <DialogCard :error="submissionError">
            <v-card-title class="text-h5 grey lighten-2">Delete Idea?</v-card-title>
            <v-card-text>{{ idea.name }}</v-card-text>
            <v-card-actions>
              <v-btn block :disabled="isSubmitting" @click="deleteIdea">Confirm</v-btn>
            </v-card-actions>
          </DialogCard>
        </v-dialog>
      </div>

      <div v-else ref="ideaEditor" class="ideaEditor" @focusout="saveOnUnfocus">
        <v-text-field v-model="draftIdea.name" label="Name" hide-details
                      @keydown.enter.prevent="saveIdea" @keydown.esc.prevent="cancelEditing"/>
        <v-textarea v-model="draftIdea.description" label="Description" rows="1" auto-grow hide-details
                    @keydown.enter.prevent="saveIdea" @keydown.esc.prevent="cancelEditing"/>
      </div>
    </v-list-item-content>
  </v-list-item>
</template>

<style scoped>
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

.idea.movingIdea {
  background: rgba(var(--v-theme-primary), 0.12);
}

.ideaName {
  cursor: pointer;
  font-size: 0.9375rem;
  font-weight: 500;
}

.ideaDescription {
  color: rgba(var(--v-theme-on-surface), 0.72);
  cursor: pointer;
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
  position: absolute;
  right: 0;
  top: 4px;
  visibility: hidden;
}

.desktopIdeaActions {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.mobileIdeaActionsTrigger {
  display: none;
}

.deleteIdeaMenuItem {
  color: rgb(var(--v-theme-error));
}

.moveIdea {
  display: none;
}

.idea:hover .ideaActions {
  visibility: visible;
}

.shortIdea .ideaActions {
  top: 8px;
}

.shortIdea .desktopIdeaActions {
  flex-direction: row;
}

.ideaEditor {
  padding: 8px 0;
}

.ideaItem {
  backface-visibility: hidden;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.18);
  border-radius: 9px;
  box-sizing: border-box;
  min-height: 0 !important;
  overflow: hidden;
  padding-bottom: 0 !important;
  padding-top: 0 !important;
  transform-style: preserve-3d;
}

.ideaItem.rollingTop {
  transform: rotateX(var(--roll-angle));
  transform-origin: center bottom;
  will-change: transform;
}

.ideaItem.rollingBottom {
  transform: rotateX(var(--roll-angle));
  transform-origin: center top;
  will-change: transform;
}

.deleteIdea,
.createObjectiveFromIdea {
  color: rgba(var(--v-theme-on-surface), 0.65);
}

@media (max-width: 600px) {
  .ideaActions {
    visibility: visible;
  }

  .desktopIdeaActions {
    display: none;
  }

  .mobileIdeaActionsTrigger {
    display: inline-flex;
    font-size: 26px !important;
    height: 36px;
    transform: translateY(-5px);
    width: 36px;
  }

  .shortIdea .ideaActions {
    flex-basis: 36px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .ideaItem.rollingTop,
  .ideaItem.rollingBottom {
    transform: none;
  }
}
</style>
