<script setup lang="ts">
/** Card description — short paragraph under the title. */
</script>

<template>
  <p class="ds-card__description">
    <slot />
  </p>
</template>

<style>
.ds-card__description {
  margin: 0;
  font-size: var(--ds-font-size-label);
  color: var(--ds-color-text-grey);
}
</style>
