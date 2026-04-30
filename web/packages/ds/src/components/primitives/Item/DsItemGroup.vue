<script setup lang="ts">
/**
 * ItemGroup — list container for `DsItem` rows.
 */
</script>

<template>
  <div
    role="list"
    class="ds-item-group"
    data-test="ds-item-group"
  >
    <slot />
  </div>
</template>

<style>
.ds-item-group {
  display: flex;
  flex-direction: column;
}
</style>
