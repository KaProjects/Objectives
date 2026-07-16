<script setup>
import {computed, ref, watch} from 'vue'
import {api} from '@/services/apiClient'
import DialogCard from '@/dialogs/DialogCard.vue'

const props = defineProps({
  modelValue: Boolean,
  objectiveId: {type: Number, required: true},
})
const emit = defineEmits(['update:modelValue', 'created'])

const isOpen = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})
const newKeyResult = ref({name: '', description: ''})
const isSubmitting = ref(false)
const submissionError = ref(null)

watch(isOpen, (isOpen) => {
  if (isOpen) newKeyResult.value = {name: '', description: ''}
})

async function addKeyResult() {
  if (isSubmitting.value) return
  isSubmitting.value = true
  submissionError.value = null
  try {
    const keyResult = await api.post('/key_result', {
      ...newKeyResult.value,
      objective_id: props.objectiveId,
    })
    emit('created', keyResult)
    isOpen.value = false
  } catch (error) {
    submissionError.value = error.message
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <v-dialog v-model="isOpen" width="300">
    <template v-slot:activator="{ props }">
      <v-btn color="primary" v-bind="props">
        <v-icon icon="mdi-plus" large/>
      </v-btn>
    </template>
    <DialogCard :error="submissionError">
      <v-text-field label="Name" v-model="newKeyResult.name"/>
      <v-text-field label="Description" v-model="newKeyResult.description"/>
      <v-card-actions>
        <v-btn block @click="addKeyResult" :disabled="isSubmitting || !newKeyResult.name">Add</v-btn>
      </v-card-actions>
    </DialogCard>
  </v-dialog>
</template>
