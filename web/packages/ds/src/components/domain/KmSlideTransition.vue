<script setup lang="ts">
/**
 * `<km-slide-transition>` — block-axis slide / fade transition. Replaces
 * Quasar's `<q-slide-transition>` with Vue's built-in `<Transition>`.
 */
withDefaults(
  defineProps<{
    duration?: number
  }>(),
  { duration: 250 },
)
</script>

<template>
  <Transition
    name="km-slide-transition"
    :duration="duration"
  >
    <slot />
  </Transition>
</template>

<style>
.km-slide-transition-enter-active,
.km-slide-transition-leave-active {
  transition:
    opacity var(--ds-duration-base, 250ms) var(--ds-ease-out),
    transform var(--ds-duration-base, 250ms) var(--ds-ease-out),
    max-block-size var(--ds-duration-base, 250ms) var(--ds-ease-out);
  overflow: hidden;
}
.km-slide-transition-enter-from,
.km-slide-transition-leave-to {
  opacity: 0;
  transform: translateY(-6px);
  max-block-size: 0;
}
.km-slide-transition-enter-to,
.km-slide-transition-leave-from {
  opacity: 1;
  transform: translateY(0);
  max-block-size: 1000px;
}
</style>
