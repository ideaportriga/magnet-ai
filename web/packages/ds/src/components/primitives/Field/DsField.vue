<script setup lang="ts">
/**
 * Field — grouping container for a single labelled control plus its
 * description / error. Layout switches between vertical (default), horizontal
 * (label aligned next to control), and `responsive` (vertical, then
 * horizontal at container ≥ md).
 *
 *   <DsField orientation="vertical">
 *     <DsFieldLabel for="email">Email</DsFieldLabel>
 *     <DsInput id="email" v-model="email" />
 *     <DsFieldDescription>We never share it.</DsFieldDescription>
 *   </DsField>
 */

export type DsFieldOrientation = 'vertical' | 'horizontal' | 'responsive'

withDefaults(
  defineProps<{
    orientation?: DsFieldOrientation
  }>(),
  {
    orientation: 'vertical',
  },
)
</script>

<template>
  <div
    role="group"
    class="ds-field"
    :data-orientation="orientation"
    data-test="ds-field"
  >
    <slot />
  </div>
</template>

<style>
.ds-field {
  display: flex;
  inline-size: 100%;
  gap: var(--ds-space-md);
}
.ds-field[data-invalid='true'] {
  color: var(--ds-color-error-text);
}

/* vertical (default) */
.ds-field[data-orientation='vertical'] {
  flex-direction: column;
}
.ds-field[data-orientation='vertical'] > * {
  inline-size: 100%;
}

/* horizontal */
.ds-field[data-orientation='horizontal'] {
  flex-direction: row;
  align-items: center;
}
.ds-field[data-orientation='horizontal'] > [data-test='ds-field-label'] {
  flex: 1 1 auto;
}

/* responsive */
.ds-field[data-orientation='responsive'] {
  flex-direction: column;
}
.ds-field[data-orientation='responsive'] > * {
  inline-size: 100%;
}
@container (min-width: 768px) {
  .ds-field[data-orientation='responsive'] {
    flex-direction: row;
    align-items: center;
  }
  .ds-field[data-orientation='responsive'] > * {
    inline-size: auto;
  }
  .ds-field[data-orientation='responsive'] > [data-test='ds-field-label'] {
    flex: 1 1 auto;
  }
}
</style>
