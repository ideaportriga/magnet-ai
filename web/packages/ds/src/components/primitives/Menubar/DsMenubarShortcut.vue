<script setup lang="ts">
defineOptions({ name: 'DsMenubarShortcut' })
</script>

<template>
  <span
    class="ds-menu-shortcut"
    data-test="ds-menubar-shortcut"
  >
    <slot />
  </span>
</template>
