<script setup lang="ts">
/**
 * ItemSeparator — horizontal divider between `DsItem` rows.
 */

import DsSeparator from '../Separator/DsSeparator.vue'
</script>

<template>
  <DsSeparator
    class="ds-item__separator"
    orientation="horizontal"
    data-test="ds-item-separator"
  />
</template>

<style>
.ds-item__separator {
  margin: 0;
}
</style>
