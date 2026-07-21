<script setup>
import {nextTick, onBeforeUnmount, onMounted, ref, watch} from 'vue'
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

const ideaPendingDeletionId = ref(null)
const openAddIdeaDialogId = ref(null)
const editingIdeaId = ref(null)
const editingSubvalueId = ref(null)
const subvaluePendingDeletionId = ref(null)
const draggedIdea = ref(null)
const dragOverSubvalueId = ref(null)
const pendingMove = ref(null)
const openIdeaActionsMenuId = ref(null)
const ideaLists = ref(null)
const ideaListElements = new Map()
const dirtyIdeaListIds = new Set()
const rollingIdeaItems = new Map()
const activeSubvalueIndex = ref(0)
const draftIdea = ref({name: '', description: ''})
const ideaEditor = ref(null)
const isSubmitting = ref(false)
const submissionError = ref(null)
let ideaListsResizeObserver
let ideaListsAnimationFrame = null

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

function updateActiveSubvalueIndex() {
  const carousel = ideaLists.value
  if (!carousel || carousel.clientWidth === 0) return
  activeSubvalueIndex.value = Math.min(
      props.subvalues.length - 1,
      Math.max(0, Math.round(carousel.scrollLeft / carousel.clientWidth)),
  )
}

function registerIdeaList(subvalueId, wrapper) {
  const previousList = ideaListElements.get(subvalueId)
  const list = wrapper?.querySelector('.subvalueIdeas') ?? null
  if (previousList === list) return

  if (previousList) ideaListsResizeObserver?.unobserve(previousList)

  if (!list) {
    clearIdeaListRoll(subvalueId)
    dirtyIdeaListIds.delete(subvalueId)
    ideaListElements.delete(subvalueId)
    return
  }

  ideaListElements.set(subvalueId, list)
  ideaListsResizeObserver?.observe(list)
  nextTick(() => scheduleIdeaListRoll(subvalueId))
}

function clearRollingIdeaItem(item, className) {
  if (!item) return

  item.classList.remove(className)
  item.style.removeProperty('--roll-angle')
}

function setRollingIdeaItem(subvalueId, edge, item, angle) {
  const className = edge === 'top' ? 'rollingTop' : 'rollingBottom'
  const state = rollingIdeaItems.get(subvalueId) ?? {top: null, bottom: null}
  const previousItem = state[edge]

  if (previousItem !== item) clearRollingIdeaItem(previousItem, className)
  if (item) {
    item.classList.add(className)
    item.style.setProperty('--roll-angle', `${angle}deg`)
  }

  state[edge] = item
  rollingIdeaItems.set(subvalueId, state)
}

function clearIdeaListRoll(subvalueId) {
  const state = rollingIdeaItems.get(subvalueId)
  clearRollingIdeaItem(state?.top, 'rollingTop')
  clearRollingIdeaItem(state?.bottom, 'rollingBottom')
  rollingIdeaItems.delete(subvalueId)
}

function updateIdeaListRoll(subvalueId) {
  const list = ideaListElements.get(subvalueId)
  if (!list) return

  const viewportTop = list.scrollTop
  const viewportBottom = viewportTop + list.clientHeight
  let topItem = null
  let topAngle = 0
  let bottomItem = null
  let bottomAngle = 0

  for (const item of list.children) {
    const itemHeight = item.offsetHeight
    if (itemHeight <= 0) continue

    const itemTop = item.offsetTop
    const itemBottom = itemTop + itemHeight

    if (!topItem && itemTop < viewportTop && itemBottom > viewportTop) {
      const progress = Math.min((viewportTop - itemTop) / itemHeight, 1)
      topItem = item
      topAngle = progress * 68
    }

    if (itemTop < viewportBottom && itemBottom > viewportBottom) {
      const visiblePart = viewportBottom - itemTop
      const progress = 1 - Math.min(Math.max(visiblePart / itemHeight, 0), 1)
      bottomItem = item
      bottomAngle = progress * -68
      break
    }

    if (itemTop >= viewportBottom) break
  }

  setRollingIdeaItem(subvalueId, 'top', topItem, topAngle)
  setRollingIdeaItem(subvalueId, 'bottom', bottomItem === topItem ? null : bottomItem, bottomAngle)
}

function scheduleIdeaListRoll(subvalueId) {
  dirtyIdeaListIds.add(subvalueId)
  if (ideaListsAnimationFrame !== null) return
  if (typeof requestAnimationFrame === 'undefined') {
    flushIdeaListRolls()
    return
  }

  ideaListsAnimationFrame = requestAnimationFrame(flushIdeaListRolls)
}

function flushIdeaListRolls() {
  ideaListsAnimationFrame = null
  const subvalueIds = [...dirtyIdeaListIds]
  dirtyIdeaListIds.clear()
  subvalueIds.forEach(updateIdeaListRoll)
}

function updateAllIdeaListRolls() {
  props.subvalues.forEach((subvalue) => scheduleIdeaListRoll(subvalue.id))
}

onMounted(() => {
  nextTick(() => {
    updateAllIdeaListRolls()
    if (typeof ResizeObserver === 'undefined') return
    ideaListsResizeObserver = new ResizeObserver(updateAllIdeaListRolls)
    ideaListElements.forEach((list) => ideaListsResizeObserver.observe(list))
  })
})

onBeforeUnmount(() => {
  ideaListsResizeObserver?.disconnect()
  if (ideaListsAnimationFrame !== null) cancelAnimationFrame(ideaListsAnimationFrame)
  rollingIdeaItems.forEach((_, subvalueId) => clearIdeaListRoll(subvalueId))
})

watch(() => props.subvalues, () => nextTick(updateAllIdeaListRolls), {deep: true})
watch([editingIdeaId, () => draftIdea.value.description], () => nextTick(updateAllIdeaListRolls))

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

  await moveIdea(dragged, targetSubvalue)
}

function startMove(subvalue, idea) {
  if (isSubmitting.value) return
  pendingMove.value = {sourceSubvalueId: subvalue.id, idea}
}

function cancelMove() {
  pendingMove.value = null
}

function closeIdeaActionsMenu() {
  openIdeaActionsMenuId.value = null
}

function createObjectiveFromIdea(subvalue, idea) {
  closeIdeaActionsMenu()
  emit('create-objective', {subvalueId: subvalue.id, idea})
}

function selectIdeaForMove(subvalue, idea) {
  closeIdeaActionsMenu()
  startMove(subvalue, idea)
}

function requestIdeaDeletion(subvalue, idea) {
  closeIdeaActionsMenu()
  ideaPendingDeletionId.value = ideaKey(subvalue, idea)
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
        '/value/' + props.valueId + '/subvalue/' + source.sourceSubvalueId + '/idea/' + source.idea.id + '/move',
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
      <v-btn v-if="pendingMove && pendingMove.sourceSubvalueId !== subvalue.id" class="moveIdeaHere"
             variant="tonal" size="small" @click="movePendingIdea(subvalue)">
        Move here
      </v-btn>
      <v-btn v-else-if="pendingMove" class="cancelIdeaMove" variant="text" size="small" @click="cancelMove">
        Cancel move
      </v-btn>
      <div :ref="(element) => registerIdeaList(subvalue.id, element)" class="subvalueIdeasWrapper">
      <v-list class="subvalueIdeas" @scroll="scheduleIdeaListRoll(subvalue.id)">
        <v-list-item v-for="idea in subvalue.ideas" :key="idea.id" class="ideaItem">
          <v-list-item-content>
            <div v-if="editingIdeaId !== ideaKey(subvalue, idea)" class="idea"
                 :class="{
                   shortIdea: !idea.description,
                   draggingIdea: draggedIdea?.idea.id === idea.id && draggedIdea?.sourceSubvalueId === subvalue.id,
                   movingIdea: pendingMove?.idea.id === idea.id && pendingMove?.sourceSubvalueId === subvalue.id,
                 }"
                 :draggable="!isSubmitting"
                 @dragstart="startDragging($event, subvalue, idea)"
                 @dragend="endDragging"
                 @click="startEditing(subvalue, idea)">
              <div class="ideaContent">
                <div class="ideaName">{{ idea.name }}</div>
                <div v-if="idea.description" class="ideaDescription">{{ idea.description }}</div>
              </div>

              <div class="ideaActions">
                <div class="desktopIdeaActions">
                  <v-icon class="createObjectiveFromIdea" icon="mdi-flag-plus-outline" size="18"
                          @click.stop="emit('create-objective', {subvalueId: subvalue.id, idea})"/>
                  <v-icon class="moveIdea" icon="mdi-arrow-right-bold-circle-outline" size="18"
                          @click.stop="startMove(subvalue, idea)"/>
                  <v-icon class="deleteIdea" icon="mdi-delete" size="18"
                          @click.stop="ideaPendingDeletionId = ideaKey(subvalue, idea)"/>
                </div>
                <v-menu
                    :model-value="openIdeaActionsMenuId === ideaKey(subvalue, idea)"
                    @update:model-value="openIdeaActionsMenuId = $event ? ideaKey(subvalue, idea) : null"
                >
                  <template #activator="{props: menuProps}">
                    <v-icon class="mobileIdeaActionsTrigger" icon="mdi-dots-vertical" v-bind="menuProps"/>
                  </template>
                  <v-list class="mobileIdeaActionsMenu" density="compact">
                    <v-list-item prepend-icon="mdi-flag-plus-outline" title="Create Objective"
                                 @click="createObjectiveFromIdea(subvalue, idea)"/>
                    <v-list-item prepend-icon="mdi-arrow-right-bold-circle-outline" title="Move to…"
                                 @click="selectIdeaForMove(subvalue, idea)"/>
                    <v-list-item class="deleteIdeaMenuItem" prepend-icon="mdi-delete" title="Delete"
                                 @click="requestIdeaDeletion(subvalue, idea)"/>
                  </v-list>
                </v-menu>
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
      </div>
      </v-card>
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
  display: flex;
  gap: 4px;
  box-sizing: border-box;
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

.subvalueList {
  border: 1px solid rgba(var(--v-theme-on-surface), 0.24);
  border-radius: 10px !important;
  box-sizing: border-box;
  box-shadow:
    0 2px 4px rgba(16, 24, 40, 0.18),
    inset 0 1px 0 rgba(255, 255, 255, 0.4);
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

.moveIdeaHere,
.cancelIdeaMove,
.moveIdea {
  display: none;
}

@media (max-width: 600px) {
  .subvalueIdeasWrapper {
    margin-bottom: 40px;
  }

  .carouselPager {
    bottom: calc(14px + env(safe-area-inset-bottom));
    display: flex;
  }

  .moveIdeaHere,
  .cancelIdeaMove {
    display: inline-flex;
  }
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
  padding-top: 0 !important;
  padding-bottom: 0 !important;
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

.deleteIdea {
  color: rgba(var(--v-theme-on-surface), 0.65);
}

.createObjectiveFromIdea {
  color: rgba(var(--v-theme-on-surface), 0.65);
}

@media (prefers-reduced-motion: reduce) {
  .ideaItem.rollingTop,
  .ideaItem.rollingBottom {
    transform: none;
  }
}
</style>
