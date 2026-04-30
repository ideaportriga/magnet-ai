<script setup lang="ts">
/**
 * TableCaption — semantic <caption> rendered below the table by default.
 */
</script>

<template>
  <caption class="ds-table__caption" data-test="ds-table-caption">
    <slot />
  </caption>
</template>

<style>
.ds-table__caption {
  margin-block-start: var(--ds-space-md);
  color: var(--ds-color-text-grey);
  font-size: var(--ds-font-size-label);
}
</style>
