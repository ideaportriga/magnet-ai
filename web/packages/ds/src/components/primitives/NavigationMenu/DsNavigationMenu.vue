<script setup lang="ts">
import type { NavigationMenuRootEmits, NavigationMenuRootProps } from 'reka-ui'
import { reactiveOmit } from '@vueuse/core'
import {
  NavigationMenuRoot,
  useForwardPropsEmits,
} from 'reka-ui'
import DsNavigationMenuViewport from './DsNavigationMenuViewport.vue'

const props = withDefaults(
  defineProps<NavigationMenuRootProps & { viewport?: boolean }>(),
  { viewport: true },
)
const emits = defineEmits<NavigationMenuRootEmits>()

const delegatedProps = reactiveOmit(props, 'class' as never, 'viewport' as never)
const forwarded = useForwardPropsEmits(delegatedProps, emits)
</script>

<template>
  <NavigationMenuRoot
    v-slot="slotProps"
    class="ds-nav-menu"
    data-test="ds-navigation-menu"
    :data-viewport="viewport"
    v-bind="forwarded"
  >
    <slot v-bind="slotProps" />
    <DsNavigationMenuViewport v-if="viewport" />
  </NavigationMenuRoot>
</template>

<style>
.ds-nav-menu {
  position: relative;
  display: flex;
  flex: 1 1 0%;
  max-inline-size: max-content;
  align-items: center;
  justify-content: center;
}

.ds-nav-menu__list {
  display: flex;
  flex: 1 1 0%;
  align-items: center;
  justify-content: center;
  gap: var(--ds-space-2xs);
  padding: 0;
  margin: 0;
  list-style: none;
}

.ds-nav-menu__item {
  position: relative;
}

.ds-nav-menu__trigger {
  display: inline-flex;
  block-size: 2.25rem;
  inline-size: max-content;
  align-items: center;
  justify-content: center;
  padding-block: var(--ds-space-xs);
  padding-inline: var(--ds-space-md);
  font-size: var(--ds-font-size-label);
  font-weight: var(--ds-font-weight-medium);
  color: var(--ds-color-black);
  background: var(--ds-color-background, var(--ds-color-white));
  border: 0;
  border-radius: var(--ds-radius-md);
  cursor: default;
  outline: none;
  transition: color var(--ds-duration-fast) var(--ds-ease-out),
              background-color var(--ds-duration-fast) var(--ds-ease-out),
              box-shadow var(--ds-duration-fast) var(--ds-ease-out);
  user-select: none;
}
.ds-nav-menu__trigger:hover,
.ds-nav-menu__trigger:focus-visible,
.ds-nav-menu__trigger[data-state='open'] {
  background: var(--ds-color-accent-bg, var(--ds-color-light));
  color: var(--ds-color-accent, var(--ds-color-black));
}
.ds-nav-menu__trigger:disabled,
.ds-nav-menu__trigger[data-disabled] {
  pointer-events: none;
  opacity: 0.5;
}
.ds-nav-menu__trigger:focus-visible {
  outline: 1px solid var(--ds-color-primary);
  outline-offset: 1px;
  box-shadow: 0 0 0 3px var(--ds-color-primary-transparent, var(--ds-color-primary-bg));
}

.ds-nav-menu__chevron {
  position: relative;
  inset-block-start: 1px;
  margin-inline-start: var(--ds-space-2xs);
  inline-size: 0.75rem;
  block-size: 0.75rem;
  transition: transform var(--ds-duration-base) var(--ds-ease-out);
}
.ds-nav-menu__trigger[data-state='open'] .ds-nav-menu__chevron {
  transform: rotate(180deg);
}

.ds-nav-menu__content {
  position: absolute;
  inset-block-start: 0;
  inset-inline-start: 0;
  inline-size: 100%;
  padding-block: var(--ds-space-xs);
  padding-inline: var(--ds-space-xs);
}
@media (min-width: 768px) {
  .ds-nav-menu__content {
    position: absolute;
    inline-size: auto;
  }
}
.ds-nav-menu__content[data-motion^='from-'] {
  animation: ds-fade-in var(--ds-duration-base) var(--ds-ease-out);
}
.ds-nav-menu__content[data-motion='from-end'] {
  animation: ds-nav-menu-slide-from-right var(--ds-duration-base) var(--ds-ease-out);
}
.ds-nav-menu__content[data-motion='from-start'] {
  animation: ds-nav-menu-slide-from-left var(--ds-duration-base) var(--ds-ease-out);
}
.ds-nav-menu__content[data-motion^='to-'] {
  animation: ds-fade-out var(--ds-duration-base) var(--ds-ease-in);
}
.ds-nav-menu__content[data-motion='to-end'] {
  animation: ds-nav-menu-slide-to-right var(--ds-duration-base) var(--ds-ease-in);
}
.ds-nav-menu__content[data-motion='to-start'] {
  animation: ds-nav-menu-slide-to-left var(--ds-duration-base) var(--ds-ease-in);
}

/* When viewport is disabled, content displays inline below the trigger */
.ds-nav-menu[data-viewport='false'] .ds-nav-menu__content {
  position: absolute;
  inset-block-start: 100%;
  margin-block-start: var(--ds-space-2xs);
  overflow: hidden;
  background: var(--ds-color-panel-main-bg, var(--ds-color-white));
  color: var(--ds-color-black);
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-md);
  box-shadow: var(--ds-shadow-md);
}
.ds-nav-menu[data-viewport='false'] .ds-nav-menu__content[data-state='open'] {
  animation: ds-nav-menu-zoom-in var(--ds-duration-base) var(--ds-ease-out);
}
.ds-nav-menu[data-viewport='false'] .ds-nav-menu__content[data-state='closed'] {
  animation: ds-nav-menu-zoom-out var(--ds-duration-base) var(--ds-ease-in);
}

.ds-nav-menu__viewport-host {
  position: absolute;
  inset-block-start: 100%;
  inset-inline-start: 0;
  display: flex;
  justify-content: center;
  isolation: isolate;
  z-index: var(--ds-z-popover);
}

.ds-nav-menu__viewport {
  position: relative;
  margin-block-start: var(--ds-space-2xs);
  block-size: var(--reka-navigation-menu-viewport-height);
  inline-size: 100%;
  inset-inline-start: var(--reka-navigation-menu-viewport-left);
  overflow: hidden;
  background: var(--ds-color-panel-main-bg, var(--ds-color-white));
  color: var(--ds-color-black);
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-md);
  box-shadow: var(--ds-shadow-md);
  transform-origin: top center;
  transition: block-size var(--ds-duration-base) var(--ds-ease-out),
              inline-size var(--ds-duration-base) var(--ds-ease-out);
}
@media (min-width: 768px) {
  .ds-nav-menu__viewport {
    inline-size: var(--reka-navigation-menu-viewport-width);
  }
}
.ds-nav-menu__viewport[data-state='open'] {
  animation: ds-nav-menu-zoom-in var(--ds-duration-base) var(--ds-ease-out);
}
.ds-nav-menu__viewport[data-state='closed'] {
  animation: ds-nav-menu-zoom-out var(--ds-duration-base) var(--ds-ease-in);
}

.ds-nav-menu__indicator {
  position: absolute;
  inset-block-start: 100%;
  z-index: 1;
  display: flex;
  block-size: 0.375rem;
  align-items: end;
  justify-content: center;
  overflow: hidden;
  pointer-events: none;
}
.ds-nav-menu__indicator[data-state='visible'] {
  animation: ds-fade-in var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-nav-menu__indicator[data-state='hidden'] {
  animation: ds-fade-out var(--ds-duration-fast) var(--ds-ease-in);
}
.ds-nav-menu__indicator-arrow {
  position: relative;
  inset-block-start: 60%;
  inline-size: 0.5rem;
  block-size: 0.5rem;
  background: var(--ds-color-border);
  border-start-start-radius: var(--ds-radius-xs);
  box-shadow: var(--ds-shadow-md);
  transform: rotate(45deg);
}

.ds-nav-menu__link {
  display: flex;
  flex-direction: column;
  gap: var(--ds-space-2xs);
  padding: var(--ds-space-sm);
  font-size: var(--ds-font-size-label);
  color: inherit;
  text-decoration: none;
  border-radius: var(--ds-radius-sm);
  outline: none;
  transition: color var(--ds-duration-fast) var(--ds-ease-out),
              background-color var(--ds-duration-fast) var(--ds-ease-out),
              box-shadow var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-nav-menu__link:hover,
.ds-nav-menu__link:focus-visible {
  background: var(--ds-color-accent-bg, var(--ds-color-light));
  color: var(--ds-color-accent, var(--ds-color-black));
}
.ds-nav-menu__link[data-active] {
  background: var(--ds-color-accent-bg, var(--ds-color-light));
  color: var(--ds-color-accent, var(--ds-color-black));
}
.ds-nav-menu__link:focus-visible {
  outline: 1px solid var(--ds-color-primary);
  outline-offset: 1px;
  box-shadow: 0 0 0 4px var(--ds-color-primary-transparent, var(--ds-color-primary-bg));
}
.ds-nav-menu__link :where(svg) {
  flex-shrink: 0;
  inline-size: 1rem;
  block-size: 1rem;
  color: var(--ds-color-text-grey, currentColor);
}

</style>
