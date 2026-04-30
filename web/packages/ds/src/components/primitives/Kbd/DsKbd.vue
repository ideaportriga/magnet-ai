<script setup lang="ts">
/**
 * Kbd — single keyboard key chip (e.g. ⌘, Shift, K).
 *
 *   <DsKbd>⌘</DsKbd>
 *   <DsKbd>K</DsKbd>
 */
</script>

<template>
  <kbd class="ds-kbd" data-test="ds-kbd">
    <slot />
  </kbd>
</template>

<style>
.ds-kbd {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--ds-space-2xs);
  pointer-events: none;
  user-select: none;
  inline-size: fit-content;
  min-inline-size: 20px;
  block-size: 20px;
  padding-inline: var(--ds-space-2xs);
  background: var(--ds-color-light);
  color: var(--ds-color-text-grey);
  border-radius: var(--ds-radius-sm);
  font-family: var(--ds-font-default);
  font-size: var(--ds-font-size-xs);
  font-weight: var(--ds-font-weight-medium);
}
.ds-kbd > svg {
  inline-size: 12px;
  block-size: 12px;
}
</style>
