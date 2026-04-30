<script setup lang="ts">
/** Card title heading (level configurable; defaults to `h3`). */

withDefaults(defineProps<{ as?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6' }>(), {
  as: 'h3',
})
</script>

<template>
  <component :is="as" class="ds-card__title">
    <slot />
  </component>
</template>

<style>
.ds-card__title {
  margin: 0;
  font-size: var(--ds-font-size-body-lg);
  font-weight: var(--ds-font-weight-semibold);
  line-height: var(--ds-line-height-none);
  color: var(--ds-color-black);
}
</style>
