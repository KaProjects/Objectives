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
const name = ref('')
const isSubmitting = ref(false)
const submissionError = ref(null)

watch(isOpen, (open) => {
  if (open) name.value = ''
})

async function addSubvalue() {
  if (isSubmitting.value) return
  isSubmitting.value = true
  submissionError.value = null
  try {
    const subvalue = await api.post('/value/' + props.valueId + '/subvalue', {name: name.value})
    emit('created', subvalue)
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
      <v-text-field label="Name" v-model="name"/>
      <v-card-actions>
        <v-btn block @click="addSubvalue" :disabled="isSubmitting || !name">Add</v-btn>
      </v-card-actions>
    </DialogCard>
  </v-dialog>
</template>
