<script setup lang="ts">
/**
 * TableHeader — semantic <thead>.
 */
</script>

<template>
  <thead class="ds-table__header" data-test="ds-table-header">
    <slot />
  </thead>
</template>

<style>
.ds-table__header tr {
  border-block-end: 1px solid var(--ds-color-border);
}
</style>
