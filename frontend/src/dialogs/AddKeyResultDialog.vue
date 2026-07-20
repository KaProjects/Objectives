<script setup>
import {computed, nextTick, onBeforeUnmount, onMounted, ref, watch} from 'vue'
import {api} from '@/services/apiClient'
import DialogCard from '@/dialogs/DialogCard.vue'

const props = defineProps({
  modelValue: Boolean,
  objectiveId: {type: Number, required: true},
  initialKeyResult: {type: Object, default: null},
  showActivator: {type: Boolean, default: true},
})
const emit = defineEmits(['update:modelValue', 'created'])

const isOpen = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})
const newKeyResult = ref({name: '', description: '', s: false, m: '', a: '', r: false, t: ''})
const isSubmitting = ref(false)
const submissionError = ref(null)
const nativeDeadlinePicker = ref(null)
const validationErrors = ref({})
const isValidationBlocked = ref(false)
const dialogContent = ref(null)
const hasMoreContentBelow = ref(false)

watch(isOpen, async (isOpen) => {
  if (isOpen) {
    newKeyResult.value = {
      name: '', description: '', s: false, m: '', a: '', r: false, t: '',
      ...props.initialKeyResult,
    }
    validationErrors.value = {}
    isValidationBlocked.value = false
    await nextTick()
    updateScrollHint()
  } else {
    hasMoreContentBelow.value = false
  }
}, {immediate: true})

watch(validationErrors, async () => {
  await nextTick()
  updateScrollHint()
}, {deep: true})

onMounted(() => window.addEventListener('resize', updateScrollHint))
onBeforeUnmount(() => window.removeEventListener('resize', updateScrollHint))

async function addKeyResult() {
  if (isSubmitting.value || isValidationBlocked.value || !validateKeyResult()) return
  isSubmitting.value = true
  submissionError.value = null
  try {
    const keyResult = await api.post('/key_result', {
      ...newKeyResult.value,
      s: newKeyResult.value.s ? 'true' : '',
      r: newKeyResult.value.r ? 'true' : '',
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

function validateKeyResult() {
  const errors = {}

  if (!newKeyResult.value.name.trim()) errors.name = 'Name is required.'
  if (!newKeyResult.value.s) errors.s = 'Specific must be confirmed.'
  if (!newKeyResult.value.r) errors.r = 'Relevant must be confirmed.'
  if (!newKeyResult.value.a.trim()) errors.a = 'Attainable risks are required.'
  if (!newKeyResult.value.m.trim()) errors.m = 'Acceptance criteria are required.'
  if (!newKeyResult.value.t) errors.t = 'Deadline is required.'

  validationErrors.value = errors
  isValidationBlocked.value = Object.keys(errors).length > 0
  return !isValidationBlocked.value
}

function clearValidationError(field) {
  if (!validationErrors.value[field]) return

  const {[field]: ignored, ...remainingErrors} = validationErrors.value
  validationErrors.value = remainingErrors
  isValidationBlocked.value = false
}

function openDeadlinePicker() {
  const input = nativeDeadlinePicker.value

  if (input?.showPicker) {
    input.showPicker()
  } else {
    input?.focus()
  }
}

function updateScrollHint() {
  const content = dialogContent.value
  if (!content) return

  hasMoreContentBelow.value = content.scrollTop + content.clientHeight < content.scrollHeight - 1
}

</script>

<template>
  <v-dialog v-model="isOpen" width="600">
    <template v-if="showActivator" v-slot:activator="{ props }">
      <v-btn color="primary" v-bind="props">
        <v-icon icon="mdi-plus" large style="color: #000000"/>
      </v-btn>
    </template>
    <DialogCard :error="submissionError" class="createKeyResultDialog">
      <v-card-title class="dialogTitle">Create Key Result</v-card-title>
      <div ref="dialogContent" class="dialogContent" @scroll="updateScrollHint">
        <v-text-field
            v-model="newKeyResult.name"
            label="Name"
            :error-messages="validationErrors.name"
            @update:model-value="clearValidationError('name')"
        />
        <v-text-field
            v-model="newKeyResult.description"
            label="Description"
        />
        <div class="checkboxField">
          <div class="checkboxHint">
            The goal should have a clear, highly-specific endpoint. If your goal is too vague, it won’t be SMART.
          </div>
          <v-checkbox
              v-model="newKeyResult.s"
              class="smartCheckbox"
              label="Is it specific?"
              :error-messages="validationErrors.s"
              @update:model-value="clearValidationError('s')"
          />
        </div>
        <div class="checkboxField">
          <div class="checkboxHint">
            The goal you pick should be pertinent to your chosen field, or should benefit you directly.
          </div>
          <v-checkbox
              v-model="newKeyResult.r"
              class="smartCheckbox"
              label="Is it relevant?"
              :error-messages="validationErrors.r"
              @update:model-value="clearValidationError('r')"
          />
        </div>
        <div class="checkboxField">
          <div class="checkboxHint">
            Of course, setting a goal that’s too ambitious will see you struggle to achieve it. This will sap at your motivation, both now and in the future.
          </div>
          <v-text-field
              v-model="newKeyResult.a"
              label="Attainable, but risks are..."
              :error-messages="validationErrors.a"
              @update:model-value="clearValidationError('a')"
          />
        </div>
        <div class="checkboxField">
          <div class="checkboxHint">
            You need to be able to accurately track your progress, so you can judge when a goal will be met.
          </div>
          <v-text-field
              v-model="newKeyResult.m"
              label="Acceptance criteria are..."
              :error-messages="validationErrors.m"
              @update:model-value="clearValidationError('m')"
          />
        </div>
        <div class="checkboxField">
          <div class="checkboxHint">
            Finally, setting a timeframe for your goal helps quantify it further, and helps keep your focus on track.
          </div>
          <v-text-field
              v-model="newKeyResult.t"
              label="Deadline"
              prepend-inner-icon="mdi-calendar"
              :error-messages="validationErrors.t"
              @click:prepend-inner="openDeadlinePicker"
              @update:model-value="clearValidationError('t')"
          />
          <input
              ref="nativeDeadlinePicker"
              v-model="newKeyResult.t"
              class="nativeDeadlinePicker"
              type="date"
              @change="clearValidationError('t')"
          >
        </div>
      </div>
      <v-card-actions class="dialogActions">
        <div v-if="hasMoreContentBelow" class="scrollHint" aria-hidden="true">
          <v-icon icon="mdi-chevron-down"/>
        </div>
        <v-btn block @click="addKeyResult" :disabled="isSubmitting || isValidationBlocked">Add</v-btn>
      </v-card-actions>
    </DialogCard>
  </v-dialog>
</template>

<style scoped>
.dialogTitle {
  flex: 0 0 auto;
  padding: 10px 20px;
  text-align: center;
}

.createKeyResultDialog {
  display: flex;
  flex-direction: column;
  max-height: calc(100vh - 48px);
}

.dialogContent {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  padding: 10px 20px;
}

.dialogActions {
  flex: 0 0 auto;
  padding: 10px 20px;
  position: relative;
}

.scrollHint {
  align-items: end;
  background: linear-gradient(to bottom, transparent, rgb(var(--v-theme-surface)) 60%);
  bottom: 100%;
  display: flex;
  height: 56px;
  justify-content: center;
  left: 0;
  opacity: var(--v-medium-emphasis-opacity);
  pointer-events: none;
  position: absolute;
  right: 0;
}

.checkboxField {
  margin: 1px 10px;
}

.checkboxHint {
  font-size: 1rem;
  letter-spacing: 0.009375em;
  margin-inline: 5px;
  opacity: var(--v-medium-emphasis-opacity);
}

.smartCheckbox :deep(.v-selection-control) {
  min-height: 40px;
}

.smartCheckbox {
  margin-inline: 10px;
}

.smartCheckbox :deep(.v-input__details) {
  min-height: 16px;
  padding-top: 0;
}

.nativeDeadlinePicker {
  height: 1px;
  opacity: 0;
  pointer-events: none;
  position: absolute;
  width: 1px;
}

</style>
