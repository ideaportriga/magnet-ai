<script setup lang="ts">
/**
 * Alert — inline status message. Compose with `DsAlertTitle` /
 * `DsAlertDescription`. An optional leading SVG (passed in the default slot)
 * is laid out in its own grid column.
 *
 *   <DsAlert variant="destructive">
 *     <svg>…</svg>
 *     <DsAlertTitle>Something went wrong</DsAlertTitle>
 *     <DsAlertDescription>Try again in a moment.</DsAlertDescription>
 *   </DsAlert>
 */

export type DsAlertVariant = 'default' | 'destructive'

withDefaults(defineProps<{ variant?: DsAlertVariant }>(), {
  variant: 'default',
})
</script>

<template>
  <div
    class="ds-alert"
    role="alert"
    :data-variant="variant"
    data-test="ds-alert"
  >
    <slot />
  </div>
</template>

<style>
.ds-alert {
  display: grid;
  grid-template-columns: 0 1fr;
  align-items: start;
  gap: 2px var(--ds-space-md);
  inline-size: 100%;
  padding: var(--ds-space-md) var(--ds-space-lg);
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-lg);
  background: var(--ds-color-message-bg);
  color: var(--ds-color-black);
  font-family: var(--ds-font-default);
  font-size: var(--ds-font-size-label);
}

/* When a leading icon is present, give it its own column. */
.ds-alert:has(> svg) { grid-template-columns: 1rem 1fr; }

.ds-alert > svg {
  inline-size: 1rem;
  block-size: 1rem;
  translate: 0 2px;
  color: currentcolor;
}

.ds-alert[data-variant='destructive'] {
  color: var(--ds-color-error-text);
  border-color: var(--ds-color-error-bg);
  background: var(--ds-color-error-bg);
}
.ds-alert[data-variant='destructive'] .ds-alert__description {
  color: color-mix(in srgb, var(--ds-color-error-text) 90%, transparent);
}
</style>
