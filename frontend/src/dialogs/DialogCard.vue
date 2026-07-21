<script setup lang="ts">
withDefaults(defineProps<{
  error?: string | null
}>(), {
  error: null,
})
</script>

<template>
  <v-card>
    <v-alert v-if="error" title="Request failed" type="error">
      {{ error }}
    </v-alert>
    <slot/>
  </v-card>
</template>
