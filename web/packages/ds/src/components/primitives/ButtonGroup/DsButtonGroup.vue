<script setup lang="ts">
/**
 * ButtonGroup — visually attaches buttons (and other controls) into a single
 * cluster. Pair with `DsButtonGroupSeparator` and `DsButtonGroupText`.
 *
 *   <DsButtonGroup orientation="horizontal">
 *     <DsButton variant="outline">Left</DsButton>
 *     <DsButton variant="outline">Middle</DsButton>
 *     <DsButton variant="outline">Right</DsButton>
 *   </DsButtonGroup>
 */

import { Primitive, type PrimitiveProps } from 'reka-ui'

export type DsButtonGroupOrientation = 'horizontal' | 'vertical'

withDefaults(
  defineProps<
    PrimitiveProps & {
      orientation?: DsButtonGroupOrientation
    }
  >(),
  {
    as: 'div',
    orientation: 'horizontal',
  },
)
</script>

<template>
  <Primitive
    role="group"
    class="ds-button-group"
    :as="as"
    :as-child="asChild"
    :data-orientation="orientation"
    data-test="ds-button-group"
  >
    <slot />
  </Primitive>
</template>

<style>
.ds-button-group {
  display: flex;
  inline-size: fit-content;
  align-items: stretch;
}
.ds-button-group[data-orientation='horizontal'] {
  flex-direction: row;
}
.ds-button-group[data-orientation='vertical'] {
  flex-direction: column;
}

.ds-button-group[data-orientation='horizontal'] > *:not(:first-child) {
  border-start-start-radius: 0;
  border-end-start-radius: 0;
  border-inline-start-width: 0;
}
.ds-button-group[data-orientation='horizontal'] > *:not(:last-child) {
  border-start-end-radius: 0;
  border-end-end-radius: 0;
}

.ds-button-group[data-orientation='vertical'] > *:not(:first-child) {
  border-start-start-radius: 0;
  border-start-end-radius: 0;
  border-block-start-width: 0;
}
.ds-button-group[data-orientation='vertical'] > *:not(:last-child) {
  border-end-start-radius: 0;
  border-end-end-radius: 0;
}

.ds-button-group > *:focus-visible {
  position: relative;
  z-index: var(--ds-z-raised);
}
</style>
