<script setup lang="ts">
import {computed, ref} from 'vue'
import {api} from '@/services/apiClient'
import SubvalueCard from '@/components/ideas/SubvalueCard.vue'
import CarouselPager from '@/components/CarouselPager.vue'
import {useHorizontalCarousel} from '@/composables/useHorizontalCarousel'
import type {EntityId, Idea, Subvalue, SubvalueIdentity} from '@/types/domain'

interface IdeaSelection {
  sourceSubvalueId: EntityId
  idea: Idea
}

interface IdeaEvent {
  subvalueId: EntityId
  idea: Idea
}

const props = withDefaults(defineProps<{
  valueId: EntityId
  subvalues?: Subvalue[]
}>(), {
  subvalues: () => [],
})
const emit = defineEmits<{
  (event: 'created' | 'updated' | 'create-objective', payload: IdeaEvent): void
  (event: 'moved', payload: {sourceSubvalueId: EntityId; targetSubvalueId: EntityId; idea: Idea}): void
  (event: 'subvalue-updated', subvalue: SubvalueIdentity): void
  (event: 'subvalue-deleted', subvalueId: EntityId): void
  (event: 'deleted', payload: {subvalueId: EntityId; ideaId: string}): void
}>()

const subvalueCount = computed(() => props.subvalues.length)
const {
  carousel: ideaLists,
  activeIndex: activeSubvalueIndex,
  updateActiveIndex: updateActiveSubvalueIndex,
} = useHorizontalCarousel(subvalueCount)
const draggedIdea = ref<IdeaSelection | null>(null)
const dragOverSubvalueId = ref<EntityId | null>(null)
const pendingMove = ref<IdeaSelection | null>(null)
const isSubmitting = ref(false)
const submissionError = ref<string | null>(null)

function startDragging({event, idea}: {event: DragEvent; idea: Idea}, subvalue: Subvalue) {
  draggedIdea.value = {sourceSubvalueId: subvalue.id, idea}
  if (!event.dataTransfer) return
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/plain', idea.id)
}

function endDragging() {
  draggedIdea.value = null
  dragOverSubvalueId.value = null
}

function markDragOver(subvalue: Subvalue) {
  if (draggedIdea.value?.sourceSubvalueId !== subvalue.id) {
    dragOverSubvalueId.value = subvalue.id
  }
}

async function moveDraggedIdea(targetSubvalue: Subvalue) {
  const dragged = draggedIdea.value
  endDragging()
  if (!dragged || dragged.sourceSubvalueId === targetSubvalue.id) return
  await moveIdea(dragged, targetSubvalue)
}

function startMove(subvalue: Subvalue, idea: Idea) {
  if (isSubmitting.value) return
  pendingMove.value = {sourceSubvalueId: subvalue.id, idea}
}

function cancelMove() {
  pendingMove.value = null
}

async function movePendingIdea(targetSubvalue: Subvalue) {
  const pending = pendingMove.value
  if (!pending) return
  if (pending.sourceSubvalueId === targetSubvalue.id) {
    cancelMove()
    return
  }
  if (await moveIdea(pending, targetSubvalue)) cancelMove()
}

async function moveIdea(source: IdeaSelection, targetSubvalue: Subvalue) {
  if (isSubmitting.value) return false
  isSubmitting.value = true
  submissionError.value = null
  try {
    const movedIdea = await api.put<Idea, {target_subvalue_id: EntityId}>(
        `/value/${props.valueId}/subvalue/${source.sourceSubvalueId}/idea/${source.idea.id}/move`,
        {target_subvalue_id: targetSubvalue.id},
    )
    emit('moved', {
      sourceSubvalueId: source.sourceSubvalueId,
      targetSubvalueId: targetSubvalue.id,
      idea: movedIdea,
    })
    return true
  } catch (error) {
    submissionError.value = error instanceof Error ? error.message : String(error)
    return false
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="ideaCarousel">
    <div ref="ideaLists" class="ideaLists" @scroll="updateActiveSubvalueIndex">
      <SubvalueCard v-for="subvalue in subvalues"
                    :key="subvalue.id"
                    :value-id="valueId"
                    :subvalue="subvalue"
                    :drag-over="dragOverSubvalueId === subvalue.id"
                    :dragged-idea="draggedIdea"
                    :pending-move="pendingMove"
                    :disabled="isSubmitting"
                    @created="emit('created', {subvalueId: subvalue.id, idea: $event})"
                    @updated="emit('updated', {subvalueId: subvalue.id, idea: $event})"
                    @deleted="emit('deleted', {subvalueId: subvalue.id, ideaId: $event})"
                    @subvalue-updated="emit('subvalue-updated', $event)"
                    @subvalue-deleted="emit('subvalue-deleted', $event)"
                    @create-objective="emit('create-objective', {subvalueId: subvalue.id, idea: $event})"
                    @move-requested="startMove(subvalue, $event)"
                    @move-here="movePendingIdea(subvalue)"
                    @cancel-move="cancelMove"
                    @drag-start="startDragging($event, subvalue)"
                    @drag-end="endDragging"
                    @drag-over="markDragOver(subvalue)"
                    @drop="moveDraggedIdea(subvalue)"/>
    </div>

    <CarouselPager :count="subvalues.length" :active-index="activeSubvalueIndex" label="Subvalue card position"/>
  </div>
</template>

<style scoped>
.ideaLists {
  align-items: flex-start;
  box-sizing: border-box;
  display: flex;
  gap: 4px;
  min-width: 100%;
  padding: 3px 12px 12px;
  width: max-content;
}

.ideaCarousel {
  position: relative;
}

</style>
