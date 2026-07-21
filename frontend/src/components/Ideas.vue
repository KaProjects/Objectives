<script setup>
import {ref} from 'vue'
import {api} from '@/services/apiClient'
import SubvalueCard from '@/components/ideas/SubvalueCard.vue'

const props = defineProps({
  valueId: [String, Number],
  subvalues: {
    type: Array,
    default: () => [],
  },
})
const emit = defineEmits(['created', 'updated', 'moved', 'subvalue-updated', 'subvalue-deleted', 'create-objective', 'deleted'])

const ideaLists = ref(null)
const activeSubvalueIndex = ref(0)
const draggedIdea = ref(null)
const dragOverSubvalueId = ref(null)
const pendingMove = ref(null)
const isSubmitting = ref(false)
const submissionError = ref(null)

function updateActiveSubvalueIndex() {
  const carousel = ideaLists.value
  if (!carousel || carousel.clientWidth === 0) return
  activeSubvalueIndex.value = Math.min(
      props.subvalues.length - 1,
      Math.max(0, Math.round(carousel.scrollLeft / carousel.clientWidth)),
  )
}

function startDragging({event, idea}, subvalue) {
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
  await moveIdea(dragged, targetSubvalue)
}

function startMove(subvalue, idea) {
  if (isSubmitting.value) return
  pendingMove.value = {sourceSubvalueId: subvalue.id, idea}
}

function cancelMove() {
  pendingMove.value = null
}

async function movePendingIdea(targetSubvalue) {
  const pending = pendingMove.value
  if (!pending) return
  if (pending.sourceSubvalueId === targetSubvalue.id) {
    cancelMove()
    return
  }
  if (await moveIdea(pending, targetSubvalue)) cancelMove()
}

async function moveIdea(source, targetSubvalue) {
  if (isSubmitting.value) return false
  isSubmitting.value = true
  submissionError.value = null
  try {
    const movedIdea = await api.put(
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
    submissionError.value = error.message
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

    <div v-if="subvalues.length > 1" class="carouselPager" aria-label="Subvalue card position">
      <span v-for="(_, index) in subvalues" :key="index" class="carouselPagerDot"
            :class="{active: index === activeSubvalueIndex}"/>
    </div>
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

.carouselPager {
  align-items: center;
  background: color-mix(in srgb, var(--v-theme-surface) 82%, transparent);
  border-radius: 999px;
  bottom: 24px;
  display: none;
  gap: 5px;
  left: 50%;
  padding: 5px 8px;
  pointer-events: none;
  position: absolute;
  transform: translateX(-50%);
  z-index: 2;
}

.carouselPagerDot {
  background: color-mix(in srgb, var(--v-theme-on-surface) 35%, transparent);
  border-radius: 999px;
  height: 6px;
  transition: background 160ms ease, width 160ms ease;
  width: 6px;
}

.carouselPagerDot.active {
  background: var(--v-theme-primary);
  width: 16px;
}

@media (max-width: 600px) {
  .carouselPager {
    bottom: calc(14px + env(safe-area-inset-bottom));
    display: flex;
  }
}
</style>
