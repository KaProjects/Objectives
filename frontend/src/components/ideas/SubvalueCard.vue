<script setup lang="ts">
import {nextTick, ref, watch} from 'vue'
import {api} from '@/services/apiClient'
import {useEdgeRoll} from '@/composables/useEdgeRoll'
import RawEditable from '@/components/Editable.vue'
import AddIdeaDialog from '@/dialogs/AddIdeaDialog.vue'
import DialogCard from '@/dialogs/DialogCard.vue'
import IdeaItem from '@/components/ideas/IdeaItem.vue'
import type {EntityId, Idea, Subvalue, SubvalueIdentity} from '@/types/domain'

interface IdeaSelection {
  sourceSubvalueId: EntityId
  idea: Idea
}

interface DragStartPayload {
  event: DragEvent
  idea: Idea
}

interface EditableInstance {
  startEditing: () => Promise<void>
  $slots: {
    display: (props: {startEditing: () => Promise<void>}) => unknown
  }
}

const Editable = RawEditable as typeof RawEditable & (new () => EditableInstance)

const props = withDefaults(defineProps<{
  valueId: EntityId
  subvalue: Subvalue
  dragOver?: boolean
  draggedIdea?: IdeaSelection | null
  pendingMove?: IdeaSelection | null
  disabled?: boolean
}>(), {
  dragOver: false,
  draggedIdea: null,
  pendingMove: null,
  disabled: false,
})
const emit = defineEmits<{
  (event: 'created' | 'updated' | 'create-objective' | 'move-requested', idea: Idea): void
  (event: 'deleted', ideaId: string): void
  (event: 'subvalue-updated', subvalue: SubvalueIdentity): void
  (event: 'subvalue-deleted', subvalueId: EntityId): void
  (event: 'drag-start', payload: DragStartPayload): void
  (event: 'move-here' | 'cancel-move' | 'drag-end' | 'drag-over' | 'drop'): void
}>()

const editingSubvalue = ref(false)
const confirmSubvalueDeletion = ref(false)
const openAddIdeaDialog = ref(false)
const isSubmitting = ref(false)
const submissionError = ref<string | null>(null)
const ideaListWrapper = ref<HTMLElement | null>(null)
const subvalueNameEditor = ref<EditableInstance | null>(null)
const {scheduleEdgeRoll: scheduleIdeaListRoll} = useEdgeRoll(
    () => ideaListWrapper.value?.querySelector('.subvalueIdeas'),
)

watch(() => props.subvalue.ideas, () => nextTick(scheduleIdeaListRoll), {deep: true})

async function updateSubvalue(name: string) {
  if (props.disabled || isSubmitting.value) return false
  isSubmitting.value = true
  submissionError.value = null
  try {
    const updatedSubvalue = await api.put<SubvalueIdentity, {name: string}>(
        `/value/${props.valueId}/subvalue/${props.subvalue.id}`,
        {name},
    )
    emit('subvalue-updated', updatedSubvalue)
    return true
  } catch (error) {
    submissionError.value = error instanceof Error ? error.message : String(error)
    return false
  } finally {
    isSubmitting.value = false
  }
}

async function deleteSubvalue() {
  if (props.disabled || isSubmitting.value) return
  isSubmitting.value = true
  submissionError.value = null
  try {
    await api.delete(`/value/${props.valueId}/subvalue/${props.subvalue.id}`)
    confirmSubvalueDeletion.value = false
    emit('subvalue-deleted', props.subvalue.id)
  } catch (error) {
    submissionError.value = error instanceof Error ? error.message : String(error)
  } finally {
    isSubmitting.value = false
  }
}

function isDragged(idea: Idea) {
  return props.draggedIdea?.sourceSubvalueId === props.subvalue.id && props.draggedIdea?.idea.id === idea.id
}

function isMoving(idea: Idea) {
  return props.pendingMove?.sourceSubvalueId === props.subvalue.id && props.pendingMove?.idea.id === idea.id
}
</script>

<template>
  <v-card width="300" elevation="3" shaped class="subvalueList" :class="{dragOver}"
          @dragover.prevent="emit('drag-over')" @drop.prevent="emit('drop')">
    <v-card-title class="subvalueListHeader">
      <Editable v-if="subvalue.id !== '0'" ref="subvalueNameEditor" class="subvalueNameEditor"
                :value="subvalue.name" label="Name" hide-details
                :cancel-editing="confirmSubvalueDeletion" :submit="updateSubvalue"
                @editing-changed="editingSubvalue = $event">
        <!-- @vue-ignore Legacy Vue 3.2 does not expose scoped-slot types to vue-tsc. -->
        <template #display>
          <span class="subvalueName" @click="subvalueNameEditor?.startEditing()">{{ subvalue.name }}</span>
        </template>
      </Editable>
      <span v-else/>

      <AddIdeaDialog v-if="!editingSubvalue && !confirmSubvalueDeletion"
                     v-model="openAddIdeaDialog"
                     :value-id="valueId"
                     :subvalue-id="subvalue.id"
                     @created="emit('created', $event)"/>
      <v-btn v-else-if="editingSubvalue" class="deleteSubvalue" variant="text" icon="mdi-delete"
             @mousedown.prevent @click="confirmSubvalueDeletion = true"/>

      <v-dialog v-if="subvalue.id !== '0'" v-model="confirmSubvalueDeletion" width="300">
        <DialogCard :error="submissionError">
          <v-card-title class="text-h5">Delete “{{ subvalue.name }}”?</v-card-title>
          <v-card-text>
            This will permanently delete {{ subvalue.ideas.length }} idea<span v-if="subvalue.ideas.length !== 1">s</span> in this list.
          </v-card-text>
          <v-card-actions>
            <v-btn :disabled="isSubmitting" @click="confirmSubvalueDeletion = false">Cancel</v-btn>
            <v-btn color="error" :disabled="isSubmitting" @click="deleteSubvalue">Delete</v-btn>
          </v-card-actions>
        </DialogCard>
      </v-dialog>
    </v-card-title>

    <v-btn v-if="pendingMove && pendingMove.sourceSubvalueId !== subvalue.id" class="moveIdeaHere"
           variant="tonal" size="small" @click="emit('move-here')">
      Move here
    </v-btn>
    <v-btn v-else-if="pendingMove" class="cancelIdeaMove" variant="text" size="small" @click="emit('cancel-move')">
      Cancel move
    </v-btn>

    <div ref="ideaListWrapper" class="subvalueIdeasWrapper">
      <v-list class="subvalueIdeas" @scroll="scheduleIdeaListRoll">
        <IdeaItem v-for="idea in subvalue.ideas"
                  :key="idea.id"
                  :value-id="valueId"
                  :subvalue-id="subvalue.id"
                  :idea="idea"
                  :disabled="disabled || isSubmitting"
                  :dragging="isDragged(idea)"
                  :moving="isMoving(idea)"
                  @updated="emit('updated', $event)"
                  @deleted="emit('deleted', $event)"
                  @create-objective="emit('create-objective', $event)"
                  @move-requested="emit('move-requested', $event)"
                  @drag-start="emit('drag-start', $event)"
                  @drag-end="emit('drag-end')"
                  @resized="scheduleIdeaListRoll"/>
      </v-list>
    </div>
  </v-card>
</template>

<style scoped>
.subvalueList {
  border: 1px solid rgba(var(--v-theme-on-surface), 0.24);
  border-radius: 10px !important;
  box-shadow: 0 2px 4px rgba(16, 24, 40, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.4);
  box-sizing: border-box;
  display: flex;
  flex: 0 0 300px;
  flex-direction: column;
  max-height: calc(100vh - 82px);
  overflow: hidden;
  transition: box-shadow 160ms ease, transform 160ms ease;
}

.subvalueList.dragOver {
  box-shadow: 0 0 0 2px rgb(var(--v-theme-primary));
  transform: translateY(-2px);
}

.subvalueIdeas {
  display: flex;
  flex: 1 1 auto;
  flex-direction: column;
  gap: 1px;
  min-height: 0;
  overflow-y: auto;
  overscroll-behavior-y: contain;
  padding: 2px;
  perspective: 380px;
  perspective-origin: center;
  position: relative;
  z-index: 1;
}

.subvalueIdeasWrapper {
  border: 1px solid transparent;
  border-radius: 7px;
  display: flex;
  flex: 1 1 auto;
  margin: 4px;
  min-height: 0;
  overflow: hidden;
  position: relative;
}

.subvalueIdeasWrapper::after {
  border: 1px solid rgba(var(--v-theme-on-surface), 0.18);
  border-radius: inherit;
  content: '';
  inset: 0;
  pointer-events: none;
  position: absolute;
  z-index: 2;
}

.subvalueListHeader {
  align-items: center;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.16);
  box-shadow: 0 1px 2px rgba(16, 24, 40, 0.08);
  display: flex;
  flex: 0 0 auto;
  justify-content: space-between;
  padding-bottom: 4px;
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

.moveIdeaHere,
.cancelIdeaMove {
  display: none;
}

@media (max-width: 600px) {
  .subvalueIdeasWrapper {
    margin-bottom: 40px;
  }

  .moveIdeaHere,
  .cancelIdeaMove {
    display: inline-flex;
  }
}
</style>
