<script setup>
import {nextTick, onBeforeUnmount, onMounted, ref} from 'vue'

const props = defineProps({
  value: {type: String, default: ''},
  submit: {type: Function, required: true},
  editable: {type: Boolean, default: true},
  label: {type: String, required: true},
  textarea: {type: Boolean, default: false},
  hideDetails: {type: Boolean, default: false},
  inputProps: {type: Object, default: () => ({})},
})

const isEditing = ref(false)
const draftValue = ref('')
const editor = ref(null)
const pointerClickPending = ref(false)
const isStartingEdit = ref(false)
let closeAfterClick = false

function handlePointerDown() {
  pointerClickPending.value = true
}

function handleWindowClick() {
  pointerClickPending.value = false
  if (closeAfterClick) {
    closeAfterClick = false
    isEditing.value = false
  }
}

onMounted(() => {
  window.addEventListener('pointerdown', handlePointerDown, true)
  window.addEventListener('click', handleWindowClick)
})

onBeforeUnmount(() => {
  window.removeEventListener('pointerdown', handlePointerDown, true)
  window.removeEventListener('click', handleWindowClick)
})

async function startEditing() {
  if (!props.editable) return
  draftValue.value = props.value
  isStartingEdit.value = true
  isEditing.value = true
  await nextTick()
  editor.value?.querySelector('input, textarea')?.focus()
  isStartingEdit.value = false
}

function setValue(value) {
  draftValue.value = value
}

async function save({deferClose = false} = {}) {
  if (draftValue.value !== props.value) {
    const saved = await props.submit(draftValue.value)
    if (saved === false) return false
  }

  if (deferClose && pointerClickPending.value) {
    closeAfterClick = true
  } else {
    isEditing.value = false
  }

  return true
}

function cancel() {
  isEditing.value = false
}

function handleFocusOut(event) {
  if (!isStartingEdit.value && isEditing.value && !event.currentTarget.contains(event.relatedTarget)) {
    save({deferClose: true})
  }
}
</script>

<template>
  <div ref="editor" class="edit" :class="{compact: hideDetails}" @focusout="handleFocusOut">
    <div class="text">
      <v-textarea v-if="isEditing && textarea" :model-value="draftValue" @update:model-value="setValue"
                  @keydown.ctrl.enter.prevent="save" @keydown.meta.enter.prevent="save" @keydown.esc="cancel"
                  :label="label" :hide-details="hideDetails" v-bind="inputProps"/>
      <v-text-field v-else-if="isEditing" :model-value="draftValue" @update:model-value="setValue"
                    @keydown.enter="save" @keydown.esc="cancel" :label="label" :hide-details="hideDetails" v-bind="inputProps"/>
      <slot v-else name="display" :start-editing="startEditing"/>
    </div>
  </div>
</template>

<style scoped>
.edit {
  display: flex;
}

.text {
  flex: 15;
}

.edit.compact :deep(.v-input__details) {
  display: none;
}

</style>
