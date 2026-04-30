<script setup lang="ts">
/**
 * SheetHeader — top region of a Sheet wrapping title + description.
 */
</script>

<template>
  <div class="ds-sheet__header" data-test="ds-sheet-header">
    <slot />
  </div>
</template>

<style>
.ds-sheet__header {
  display: flex;
  flex-direction: column;
  gap: var(--ds-space-2xs);
  padding: var(--ds-space-md);
}
</style>
