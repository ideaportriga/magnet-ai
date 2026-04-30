<script setup lang="ts">
import { Primitive, type PrimitiveProps } from 'reka-ui'

withDefaults(
  defineProps<PrimitiveProps & {
    size?: 'sm' | 'md'
    isActive?: boolean
  }>(),
  {
    as: 'a',
    size: 'md',
  },
)
</script>

<template>
  <Primitive
    class="ds-sidebar__menu-sub-button"
    :data-size="size"
    :data-active="isActive ? 'true' : undefined"
    data-sidebar="menu-sub-button"
    data-test="ds-sidebar-menu-sub-button"
    :as="as"
    :as-child="asChild"
  >
    <slot />
  </Primitive>
</template>

<style>
.ds-sidebar__menu-sub-button {
  display: flex;
  align-items: center;
  gap: var(--ds-space-sm);
  inline-size: 100%;
  min-inline-size: 0;
  block-size: 28px;
  padding: 0 var(--ds-space-sm);
  font-family: var(--ds-font-default);
  font-size: var(--ds-font-size-label);
  color: var(--ds-color-btn-flat-text);
  background: transparent;
  border: 0;
  border-radius: var(--ds-radius-md);
  outline: none;
  text-decoration: none;
  cursor: pointer;
  transform: translateX(-1px);
  overflow: hidden;
  transition: background var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-sidebar__menu-sub-button:hover,
.ds-sidebar__menu-sub-button:active {
  background: var(--ds-color-btn-flat-hover-bg);
}
.ds-sidebar__menu-sub-button[data-active='true'] {
  background: var(--ds-color-accent-bg);
  color: var(--ds-color-accent);
}
.ds-sidebar__menu-sub-button:focus-visible {
  box-shadow: 0 0 0 2px var(--ds-color-primary-transparent);
}
.ds-sidebar__menu-sub-button:disabled,
.ds-sidebar__menu-sub-button[aria-disabled='true'] {
  pointer-events: none;
  opacity: 0.5;
}
.ds-sidebar__menu-sub-button > svg {
  inline-size: 16px;
  block-size: 16px;
  flex: none;
  color: var(--ds-color-accent);
}
.ds-sidebar__menu-sub-button > span:last-child {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.ds-sidebar__menu-sub-button[data-size='sm'] {
  font-size: var(--ds-font-size-xs);
}
[data-collapsible='icon'] .ds-sidebar__menu-sub-button {
  display: none;
}
</style>
