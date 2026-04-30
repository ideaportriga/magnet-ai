<script setup lang="ts">
/**
 * CommandShortcut — small right-aligned text showing keyboard shortcut hint.
 */
</script>

<template>
  <span class="ds-command__shortcut" data-test="ds-command-shortcut">
    <slot />
  </span>
</template>

<style>
.ds-command__shortcut {
  margin-inline-start: auto;
  font-size: var(--ds-font-size-xs);
  letter-spacing: 0.1em;
  color: var(--ds-color-text-grey);
}
</style>
