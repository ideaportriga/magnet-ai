<script setup lang="ts">
</script>

<template>
  <div class="ds-drawer__footer" data-test="ds-drawer-footer">
    <slot />
  </div>
</template>

<style>
.ds-drawer__footer {
  margin-block-start: auto;
  display: flex;
  flex-direction: column;
  gap: var(--ds-space-sm);
  padding: var(--ds-space-lg);
}
</style>
