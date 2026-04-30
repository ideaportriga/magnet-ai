<script setup lang="ts">
/** Alert description — supporting paragraph(s). */
</script>

<template>
  <div class="ds-alert__description">
    <slot />
  </div>
</template>

<style>
.ds-alert__description {
  grid-column-start: 2;
  font-size: var(--ds-font-size-label);
  color: var(--ds-color-text-grey);
}
.ds-alert__description :where(p) { line-height: var(--ds-line-height-relaxed); }
</style>
