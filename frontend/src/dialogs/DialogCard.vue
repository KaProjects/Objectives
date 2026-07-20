<script setup>
defineProps({
  error: {
    type: String,
    default: null,
  },
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
