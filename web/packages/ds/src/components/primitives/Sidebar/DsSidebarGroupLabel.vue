<script setup lang="ts">
import { Primitive, type PrimitiveProps } from 'reka-ui'

defineProps<PrimitiveProps>()
</script>

<template>
  <Primitive
    class="ds-sidebar__group-label"
    data-sidebar="group-label"
    data-test="ds-sidebar-group-label"
    :as="as"
    :as-child="asChild"
  >
    <slot />
  </Primitive>
</template>

<style>
.ds-sidebar__group-label {
  display: flex;
  align-items: center;
  flex: none;
  block-size: 32px;
  padding-inline: var(--ds-space-sm);
  border-radius: var(--ds-radius-sm);
  font-size: var(--ds-font-size-xs);
  font-weight: var(--ds-font-weight-medium);
  color: var(--ds-color-text-grey);
  outline: none;
  transition:
    margin var(--ds-duration-base) var(--ds-ease-linear),
    opacity var(--ds-duration-base) var(--ds-ease-linear);
}
.ds-sidebar__group-label > svg {
  inline-size: 16px;
  block-size: 16px;
  flex: none;
}
[data-collapsible='icon'] .ds-sidebar__group-label {
  margin-block-start: -32px;
  opacity: 0;
}
</style>
