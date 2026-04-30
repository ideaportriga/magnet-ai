<script setup lang="ts">
/**
 * FieldLegend — `<legend>` companion for `DsFieldSet`.
 *
 *   <DsFieldLegend variant="legend">Notifications</DsFieldLegend>
 */

export type DsFieldLegendVariant = 'legend' | 'label'

withDefaults(
  defineProps<{
    variant?: DsFieldLegendVariant
  }>(),
  {
    variant: 'legend',
  },
)
</script>

<template>
  <legend
    class="ds-field-legend"
    :data-variant="variant"
    data-test="ds-field-legend"
  >
    <slot />
  </legend>
</template>

<style>
.ds-field-legend {
  margin: 0 0 var(--ds-space-md) 0;
  padding: 0;
  font-family: var(--ds-font-default);
  font-weight: var(--ds-font-weight-medium);
  color: var(--ds-color-black);
}
.ds-field-legend[data-variant='legend'] {
  font-size: var(--ds-font-size-body);
}
.ds-field-legend[data-variant='label'] {
  font-size: var(--ds-font-size-label);
}
</style>
