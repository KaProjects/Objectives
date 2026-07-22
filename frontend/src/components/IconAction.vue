<script setup lang="ts">
withDefaults(defineProps<{
  label: string
  icon: string
  size?: string | number
  disabled?: boolean
}>(), {
  size: 24,
  disabled: false,
})

const emit = defineEmits<{
  (event: 'click', mouseEvent: MouseEvent): void
}>()

function handleClick(event: MouseEvent) {
  event.stopPropagation()
  emit('click', event)
}
</script>

<template>
  <button class="iconAction" type="button" :aria-label="label" :disabled="disabled" @click="handleClick">
    <v-icon :icon="icon" :size="size" aria-hidden="true"/>
  </button>
</template>

<style scoped>
.iconAction {
  align-items: center;
  appearance: none;
  background: transparent;
  border: 0;
  color: inherit;
  cursor: pointer;
  display: inline-flex;
  justify-content: center;
  line-height: 1;
  margin: 0;
  padding: 0;
}

.iconAction:focus-visible {
  border-radius: 3px;
  outline: 2px solid rgb(var(--v-theme-primary));
  outline-offset: 2px;
}

.iconAction:disabled {
  cursor: default;
  opacity: 0.5;
}
</style>
