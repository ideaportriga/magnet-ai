<script setup lang="ts">
defineOptions({ name: 'DsContextMenuShortcut' })
</script>

<template>
  <span
    class="ds-menu-shortcut"
    data-test="ds-context-menu-shortcut"
  >
    <slot />
  </span>
</template>
