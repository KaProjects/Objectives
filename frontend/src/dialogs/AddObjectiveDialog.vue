<script setup>
import {computed, ref, watch} from 'vue'
import {api} from '@/services/apiClient'
import DialogCard from '@/dialogs/DialogCard.vue'

const props = defineProps({
  modelValue: Boolean,
  valueId: Number,
})
const emit = defineEmits(['update:modelValue', 'created'])

const isOpen = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})
const newObjective = ref({name: '', description: ''})
const isSubmitting = ref(false)
const submissionError = ref(null)

watch(isOpen, (isOpen) => {
  if (isOpen) newObjective.value = {name: '', description: ''}
})

async function addObjective() {
  if (isSubmitting.value) return
  isSubmitting.value = true
  submissionError.value = null
  try {
    const objective = await api.post('/objective', {
      ...newObjective.value,
      value_id: props.valueId,
    })
    emit('created', objective)
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
      <v-btn v-bind="props" variant="tonal" rounded="lg">
        <v-icon icon="mdi-plus"/>
      </v-btn>
    </template>
    <DialogCard :error="submissionError">
      <v-text-field label="Name" v-model="newObjective.name"/>
      <v-text-field label="Description" v-model="newObjective.description"/>
      <v-card-actions>
        <v-btn block @click="addObjective" :disabled="isSubmitting || !newObjective.name">Add</v-btn>
      </v-card-actions>
    </DialogCard>
  </v-dialog>
</template>
