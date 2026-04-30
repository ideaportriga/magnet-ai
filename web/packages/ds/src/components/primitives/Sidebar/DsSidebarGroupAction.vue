<script setup lang="ts">
import { Primitive, type PrimitiveProps } from 'reka-ui'

withDefaults(defineProps<PrimitiveProps>(), {
  as: 'button',
})
</script>

<template>
  <Primitive
    class="ds-sidebar__group-action"
    data-sidebar="group-action"
    data-test="ds-sidebar-group-action"
    :as="as"
    :as-child="asChild"
  >
    <slot />
  </Primitive>
</template>

<style>
.ds-sidebar__group-action {
  position: absolute;
  inset-block-start: 14px;
  inset-inline-end: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  aspect-ratio: 1;
  inline-size: 20px;
  padding: 0;
  background: transparent;
  color: var(--ds-color-text-grey);
  border: 0;
  border-radius: var(--ds-radius-sm);
  outline: none;
  cursor: pointer;
  transition: background var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-sidebar__group-action:hover {
  background: var(--ds-color-light);
  color: var(--ds-color-black);
}
.ds-sidebar__group-action > svg {
  inline-size: 16px;
  block-size: 16px;
  flex: none;
}
[data-collapsible='icon'] .ds-sidebar__group-action {
  display: none;
}
</style>
