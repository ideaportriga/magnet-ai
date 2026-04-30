<script setup lang="ts">
/**
 * TableBody — semantic <tbody>.
 */
</script>

<template>
  <tbody class="ds-table__body" data-test="ds-table-body">
    <slot />
  </tbody>
</template>

<style>
.ds-table__body tr:last-child {
  border: 0;
}
</style>
