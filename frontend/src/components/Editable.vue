<script setup>
import {nextTick, onBeforeUnmount, onMounted, ref, watch} from 'vue'

const props = defineProps({
  value: {type: String, default: ''},
  submit: {type: Function, required: true},
  editable: {type: Boolean, default: true},
  label: {type: String, required: true},
  textarea: {type: Boolean, default: false},
  datePicker: {type: Boolean, default: false},
  hideDetails: {type: Boolean, default: false},
  inputProps: {type: Object, default: () => ({})},
  cancelEditing: {type: Boolean, default: false},
})
const emit = defineEmits(['editing-changed'])

const isEditing = ref(false)
const draftValue = ref('')
const editor = ref(null)
const nativeDatePicker = ref(null)
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
    stopEditing()
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
  emit('editing-changed', true)
  await nextTick()
  editor.value?.querySelector('input, textarea')?.focus()
  isStartingEdit.value = false
}

function stopEditing() {
  if (!isEditing.value) return
  isEditing.value = false
  emit('editing-changed', false)
}

function setValue(value) {
  draftValue.value = value
}

function openDatePicker() {
  const input = nativeDatePicker.value

  if (input?.showPicker) {
    input.showPicker()
  } else {
    input?.focus()
  }
}

async function selectDate(value) {
  setValue(value)
  await save()
}

async function save({deferClose = false} = {}) {
  if (draftValue.value !== props.value) {
    const saved = await props.submit(draftValue.value)
    if (saved === false) return false
  }

  if (deferClose && pointerClickPending.value) {
    closeAfterClick = true
  } else {
    stopEditing()
  }

  return true
}

function cancel() {
  stopEditing()
}

watch(() => props.cancelEditing, (cancelEditing) => {
  if (cancelEditing) stopEditing()
})

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
                    @keydown.enter="save" @keydown.esc="cancel" :label="label" :hide-details="hideDetails"
                    :prepend-inner-icon="datePicker ? 'mdi-calendar' : undefined"
                    @click:prepend-inner="openDatePicker" v-bind="inputProps"/>
      <input v-if="isEditing && datePicker" ref="nativeDatePicker" class="nativeDatePicker"
             type="date" :value="draftValue" @change="selectDate($event.target.value)">
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
  min-width: 0;
}

.edit.compact :deep(.v-input__details) {
  display: none;
}

.nativeDatePicker {
  height: 1px;
  opacity: 0;
  pointer-events: none;
  position: absolute;
  width: 1px;
}

</style>
