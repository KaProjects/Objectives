<script setup>
import {computed, ref, watch} from 'vue'
import {api} from '@/services/apiClient'
import DialogCard from '@/dialogs/DialogCard.vue'

const props = defineProps({
  modelValue: Boolean,
  valueId: [String, Number],
  subvalueId: [String, Number],
})
const emit = defineEmits(['update:modelValue', 'created'])

const isOpen = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})
const newIdea = ref({name: '', description: ''})
const isSubmitting = ref(false)
const submissionError = ref(null)

watch(isOpen, (open) => {
  if (open) newIdea.value = {name: '', description: ''}
})

async function addIdea() {
  if (isSubmitting.value) return
  isSubmitting.value = true
  submissionError.value = null
  try {
    const idea = await api.post(
        '/value/' + props.valueId + '/subvalue/' + props.subvalueId + '/idea',
        newIdea.value,
    )
    emit('created', idea)
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
      <v-btn v-bind="props" class="addIdeaButton" variant="text" icon="mdi-plus" @click="isOpen = true"/>
    </template>

    <DialogCard :error="submissionError">
      <v-text-field label="Name" v-model="newIdea.name" required/>
      <v-text-field label="Description" v-model="newIdea.description" required/>
      <v-card-actions>
        <v-btn block :disabled="isSubmitting || !newIdea.name" @click="addIdea">Add</v-btn>
      </v-card-actions>
    </DialogCard>
  </v-dialog>
</template>
