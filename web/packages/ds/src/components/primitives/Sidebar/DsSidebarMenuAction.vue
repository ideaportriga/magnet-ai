<script setup lang="ts">
import { Primitive, type PrimitiveProps } from 'reka-ui'

withDefaults(
  defineProps<PrimitiveProps & {
    showOnHover?: boolean
  }>(),
  {
    as: 'button',
  },
)
</script>

<template>
  <Primitive
    class="ds-sidebar__menu-action"
    :data-show-on-hover="showOnHover ? 'true' : 'false'"
    data-sidebar="menu-action"
    data-test="ds-sidebar-menu-action"
    :as="as"
    :as-child="asChild"
  >
    <slot />
  </Primitive>
</template>

<style>
.ds-sidebar__menu-action {
  position: absolute;
  inset-block-start: 6px;
  inset-inline-end: 4px;
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
}
.ds-sidebar__menu-action:hover {
  background: var(--ds-color-light);
  color: var(--ds-color-black);
}
.ds-sidebar__menu-action > svg {
  inline-size: 16px;
  block-size: 16px;
  flex: none;
}
.ds-sidebar__menu-action[data-show-on-hover='true'] {
  opacity: 0;
  transition: opacity var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-sidebar__menu-item:hover .ds-sidebar__menu-action[data-show-on-hover='true'],
.ds-sidebar__menu-item:focus-within .ds-sidebar__menu-action[data-show-on-hover='true'],
.ds-sidebar__menu-action[data-show-on-hover='true'][data-state='open'] {
  opacity: 1;
}
[data-collapsible='icon'] .ds-sidebar__menu-action {
  display: none;
}
</style>
