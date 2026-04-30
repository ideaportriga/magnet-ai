<script setup lang="ts">
/**
 * `<km-drawer-resize-handle>` — exposed for callers that build a custom
 * drawer layout and need just the handle. Mirrors the legacy
 * DrawerResizeHandle component.
 */

defineEmits<{
  mousedown: [event: MouseEvent]
}>()
</script>

<template>
  <span
    class="km-drawer-resize-handle"
    role="separator"
    aria-orientation="vertical"
    aria-label="Resize drawer"
    tabindex="0"
    data-test="km-drawer-resize-handle"
    @mousedown="(e) => $emit('mousedown', e)"
  />
</template>

<style>
.km-drawer-resize-handle {
  position: absolute;
  inset-block: 0;
  inset-inline-start: -3px;
  inline-size: 6px;
  cursor: col-resize;
  z-index: var(--ds-z-raised);
}
.km-drawer-resize-handle:hover { background: var(--ds-color-primary-bg); }
</style>
