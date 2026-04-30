<script setup lang="ts">
/**
 * KbdGroup — cluster of `DsKbd` chips for multi-key shortcuts (⌘+K, etc).
 */
</script>

<template>
  <kbd class="ds-kbd-group" data-test="ds-kbd-group">
    <slot />
  </kbd>
</template>

<style>
.ds-kbd-group {
  display: inline-flex;
  align-items: center;
  gap: var(--ds-space-2xs);
}
</style>
