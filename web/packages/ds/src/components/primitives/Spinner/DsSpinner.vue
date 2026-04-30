<script setup lang="ts">
/**
 * Spinner — circular activity indicator. Pure CSS so it has no icon-library
 * dependency. Size via the `size` prop or by overriding `font-size`.
 *
 *   <DsSpinner />
 *   <DsSpinner size="lg" />
 *   <DsButton :disabled="loading"><DsSpinner v-if="loading" size="sm" /> Save</DsButton>
 */

withDefaults(defineProps<{ size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; label?: string }>(), {
  size: 'md',
  label: 'Loading',
})
</script>

<template>
  <span
    class="ds-spinner"
    role="status"
    :data-size="size"
    :aria-label="label"
    data-test="ds-spinner"
  />
</template>

<style>
.ds-spinner {
  display: inline-block;
  flex: none;
  inline-size: 1em;
  block-size: 1em;
  border: 2px solid currentcolor;
  border-block-end-color: transparent;
  border-radius: 50%;
  animation: ds-spin 0.7s var(--ds-ease-linear) infinite;
}

.ds-spinner[data-size='xs'] { font-size: var(--ds-loader-size-xs); border-width: 1.5px; }
.ds-spinner[data-size='sm'] { font-size: 14px; border-width: 1.5px; }
.ds-spinner[data-size='md'] { font-size: 16px; }
.ds-spinner[data-size='lg'] { font-size: var(--ds-loader-size-sm); }
.ds-spinner[data-size='xl'] { font-size: var(--ds-loader-size-md); }

@media (prefers-reduced-motion: reduce) {
  .ds-spinner { animation-duration: 2s; }
}
</style>
