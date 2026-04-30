<script setup lang="ts">
import type { PrimitiveProps } from 'reka-ui'
import type { SidebarMenuButtonVariants } from './utils'
import { Primitive } from 'reka-ui'

export interface SidebarMenuButtonProps extends PrimitiveProps {
  variant?: SidebarMenuButtonVariants['variant']
  size?: SidebarMenuButtonVariants['size']
  isActive?: boolean
}

const props = withDefaults(defineProps<SidebarMenuButtonProps>(), {
  variant: 'default',
  size: 'default',
})
</script>

<template>
  <Primitive
    class="ds-sidebar__menu-button"
    data-sidebar="menu-button"
    data-test="ds-sidebar-menu-button"
    :data-variant="variant"
    :data-size="size"
    :data-active="isActive"
    :as="props.as ?? 'button'"
    :as-child="asChild"
  >
    <slot />
  </Primitive>
</template>

<style>
.ds-sidebar__menu-button {
  display: flex;
  align-items: center;
  gap: var(--ds-space-sm);
  inline-size: 100%;
  block-size: 32px;
  padding: var(--ds-space-xs) var(--ds-space-sm);
  font-family: var(--ds-font-default);
  font-size: var(--ds-font-size-label);
  font-weight: var(--ds-font-weight-regular);
  text-align: start;
  color: var(--ds-color-btn-flat-text);
  background: var(--ds-color-btn-flat-bg);
  border: 1px solid transparent;
  border-radius: var(--ds-radius-md);
  outline: none;
  cursor: pointer;
  user-select: none;
  overflow: hidden;
  transition:
    background var(--ds-duration-fast) var(--ds-ease-out),
    color var(--ds-duration-fast) var(--ds-ease-out),
    inline-size var(--ds-duration-base) var(--ds-ease-linear),
    block-size var(--ds-duration-base) var(--ds-ease-linear),
    padding var(--ds-duration-base) var(--ds-ease-linear);
}
.ds-sidebar__menu-button:hover {
  background: var(--ds-color-btn-flat-hover-bg);
  color: var(--ds-color-btn-flat-text);
}
.ds-sidebar__menu-button:active,
.ds-sidebar__menu-button[data-active='true'],
.ds-sidebar__menu-button[data-state='open'] {
  background: var(--ds-color-accent-bg);
  color: var(--ds-color-accent);
  font-weight: var(--ds-font-weight-medium);
}
.ds-sidebar__menu-button:focus-visible {
  box-shadow: 0 0 0 2px var(--ds-color-primary-transparent);
}
.ds-sidebar__menu-button:disabled,
.ds-sidebar__menu-button[aria-disabled='true'] {
  pointer-events: none;
  opacity: 0.5;
}
.ds-sidebar__menu-button > svg {
  inline-size: 16px;
  block-size: 16px;
  flex: none;
}
.ds-sidebar__menu-button > span:last-child {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.ds-sidebar__menu-button[data-variant='outline'] {
  background: var(--ds-color-background);
  box-shadow: 0 0 0 1px var(--ds-color-border);
}

.ds-sidebar__menu-button[data-size='sm'] {
  block-size: 28px;
  font-size: var(--ds-font-size-xs);
}
.ds-sidebar__menu-button[data-size='lg'] {
  block-size: 48px;
  font-size: var(--ds-font-size-label);
}

[data-collapsible='icon'] .ds-sidebar__menu-button {
  inline-size: 32px !important;
  block-size: 32px !important;
  padding: var(--ds-space-xs) !important;
}
[data-collapsible='icon'] .ds-sidebar__menu-button[data-size='lg'] {
  padding: 0 !important;
}
</style>
