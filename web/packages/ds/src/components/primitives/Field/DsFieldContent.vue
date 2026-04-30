<script setup lang="ts">
/**
 * FieldContent — vertical stack for label + helper text adjacent to a control
 * (e.g. switch on the right, label/description on the left).
 */
</script>

<template>
  <div class="ds-field-content" data-test="ds-field-content">
    <slot />
  </div>
</template>

<style>
.ds-field-content {
  display: flex;
  flex: 1 1 auto;
  flex-direction: column;
  gap: var(--ds-space-2xs);
  line-height: var(--ds-line-height-snug);
}
</style>
