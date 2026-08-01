<script setup>
import {computed, ref, watch} from 'vue'
import {api} from '@/services/apiClient'
import DialogCard from '@/dialogs/DialogCard.vue'

const props = defineProps({
  modelValue: Boolean,
  keyResultId: {type: Number, required: true},
})
const emit = defineEmits(['update:modelValue', 'created'])

const isOpen = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})
const task = ref({value: '', repetitive: false, daily: false, count: 2, fromDate: '', toDate: ''})
const isSubmitting = ref(false)
const submissionError = ref(null)
const maxTasksPerRequest = 40
const millisecondsPerDay = 24 * 60 * 60 * 1000

watch(isOpen, (open) => {
  if (!open) return
  task.value = {value: '', repetitive: false, daily: false, count: 2, fromDate: '', toDate: ''}
  submissionError.value = null
})

function validate() {
  if (!task.value.daily && !task.value.value.trim()) return 'Task value is required.'
  if (task.value.repetitive
      && (!Number.isInteger(Number(task.value.count)) || task.value.count < 1 || task.value.count > maxTasksPerRequest)) {
    return `Task count must be a whole number from 1 to ${maxTasksPerRequest}.`
  }
  if (task.value.daily && (!task.value.fromDate || !task.value.toDate)) return 'Both dates are required.'
  if (task.value.daily) {
    const start = Date.parse(`${task.value.fromDate}T00:00:00Z`)
    const end = Date.parse(`${task.value.toDate}T00:00:00Z`)
    if (end < start) return 'The end date cannot be before the start date.'
    const count = Math.round((end - start) / millisecondsPerDay) + 1
    if (count > maxTasksPerRequest) return `A daily task range cannot exceed ${maxTasksPerRequest} days.`
  }
  return null
}

function taskRequest() {
  if (task.value.repetitive) {
    return api.post('/task/bulk', {kr_id: props.keyResultId, value: task.value.value, count: Number(task.value.count)})
  }
  if (task.value.daily) {
    return api.post('/task/daily', {
      kr_id: props.keyResultId,
      value: task.value.value,
      from_date: task.value.fromDate,
      to_date: task.value.toDate,
    })
  }
  return api.post('/task', {kr_id: props.keyResultId, value: task.value.value})
}

async function addTasks() {
  const validationError = validate()
  if (validationError) {
    submissionError.value = validationError
    return
  }

  isSubmitting.value = true
  submissionError.value = null
  try {
    const result = await taskRequest()
    emit('created', Array.isArray(result) ? result : [result])
    isOpen.value = false
  } catch (error) {
    submissionError.value = error.message
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <v-dialog v-model="isOpen" width="420">
    <DialogCard :error="submissionError">
      <v-card-title class="text-h5">Add Task</v-card-title>
      <v-card-text>
        <v-text-field v-model="task.value" :label="task.daily ? 'Task (optional)' : 'Task'"/>

        <v-checkbox v-model="task.repetitive" label="Repetitive task" v-if="!task.daily"/>
        <v-text-field v-if="task.repetitive" v-model.number="task.count" label="Number of tasks" type="number"
                      min="1" :max="maxTasksPerRequest" :hint="`From 1 to ${maxTasksPerRequest}`" persistent-hint/>

        <v-checkbox v-model="task.daily" label="Daily task" v-if="!task.repetitive"/>
        <template v-if="task.daily">
          <v-text-field v-model="task.fromDate" label="From" type="date"/>
          <v-text-field v-model="task.toDate" label="To" type="date"/>
        </template>
      </v-card-text>
      <v-card-actions>
        <v-btn block :disabled="isSubmitting" @click="addTasks">Add</v-btn>
      </v-card-actions>
    </DialogCard>
  </v-dialog>
</template>
