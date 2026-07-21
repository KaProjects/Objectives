<script setup>
defineProps({
  count: {type: Number, required: true},
  activeIndex: {type: Number, required: true},
  label: {type: String, required: true},
})
</script>

<template>
  <div v-if="count > 1" class="carouselPager" :aria-label="label">
    <span v-for="index in count" :key="index" class="carouselPagerDot"
          :class="{active: index - 1 === activeIndex}"/>
  </div>
</template>

<style scoped>
.carouselPager {
  align-items: center;
  background: color-mix(in srgb, var(--v-theme-surface) 82%, transparent);
  border-radius: 999px;
  bottom: 24px;
  display: none;
  gap: 5px;
  left: 50%;
  padding: 5px 8px;
  pointer-events: none;
  position: absolute;
  transform: translateX(-50%);
  z-index: 2;
}

.carouselPagerDot {
  background: color-mix(in srgb, var(--v-theme-on-surface) 35%, transparent);
  border-radius: 999px;
  height: 6px;
  transition: background 160ms ease, width 160ms ease;
  width: 6px;
}

.carouselPagerDot.active {
  background: var(--v-theme-primary);
  width: 16px;
}

@media (max-width: 600px) {
  .carouselPager {
    bottom: calc(14px + env(safe-area-inset-bottom));
    display: flex;
  }
}
</style>
