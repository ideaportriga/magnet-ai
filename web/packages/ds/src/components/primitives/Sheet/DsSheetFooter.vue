<script setup lang="ts">
/**
 * SheetFooter — bottom-anchored action area inside a Sheet.
 */
</script>

<template>
  <div class="ds-sheet__footer" data-test="ds-sheet-footer">
    <slot />
  </div>
</template>

<style>
.ds-sheet__footer {
  margin-block-start: auto;
  display: flex;
  flex-direction: column;
  gap: var(--ds-space-xs);
  padding: var(--ds-space-md);
}
</style>
