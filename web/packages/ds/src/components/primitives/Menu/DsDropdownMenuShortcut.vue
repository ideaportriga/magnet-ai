<script setup lang="ts">
defineProps<{ class?: string }>()
</script>

<template>
  <span
    class="ds-menu-shortcut"
    data-test="ds-dropdown-menu-shortcut"
  >
    <slot />
  </span>
</template>
