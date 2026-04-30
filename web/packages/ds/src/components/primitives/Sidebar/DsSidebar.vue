<script setup lang="ts">
/**
 * Sidebar — the main sidebar container. Behaviour:
 * - Mobile: rendered inside a Reka Dialog as an off-canvas sheet.
 * - Desktop: a fixed-position rail that supports `offcanvas`, `icon`, `none`
 *   collapsible modes and `sidebar` / `floating` / `inset` variants.
 */

import type { SidebarProps } from './utils'
import {
  DialogContent,
  DialogDescription,
  DialogOverlay,
  DialogPortal,
  DialogRoot,
  DialogTitle,
  VisuallyHidden,
} from 'reka-ui'
import { SIDEBAR_WIDTH_MOBILE, useSidebar } from './utils'

defineOptions({
  inheritAttrs: false,
})

const props = withDefaults(defineProps<SidebarProps>(), {
  side: 'left',
  variant: 'sidebar',
  collapsible: 'offcanvas',
})

const { isMobile, state, openMobile, setOpenMobile } = useSidebar()
</script>

<template>
  <div
    v-if="collapsible === 'none'"
    class="ds-sidebar ds-sidebar--static"
    data-test="ds-sidebar"
    v-bind="$attrs"
  >
    <slot />
  </div>

  <DialogRoot
    v-else-if="isMobile"
    :open="openMobile"
    @update:open="setOpenMobile"
  >
    <DialogPortal>
      <DialogOverlay class="ds-sidebar__mobile-overlay" />
      <DialogContent
        class="ds-sidebar ds-sidebar--mobile"
        data-test="ds-sidebar"
        data-mobile="true"
        :data-side="side"
        :style="{ '--ds-sidebar-width': SIDEBAR_WIDTH_MOBILE }"
        v-bind="$attrs"
      >
        <VisuallyHidden>
          <DialogTitle>Sidebar</DialogTitle>
          <DialogDescription>Displays the mobile sidebar.</DialogDescription>
        </VisuallyHidden>
        <div class="ds-sidebar__inner">
          <slot />
        </div>
      </DialogContent>
    </DialogPortal>
  </DialogRoot>

  <div
    v-else
    class="ds-sidebar ds-sidebar--desktop"
    data-test="ds-sidebar"
    :data-state="state"
    :data-collapsible="state === 'collapsed' ? collapsible : ''"
    :data-variant="variant"
    :data-side="side"
  >
    <!-- Gap reservation -->
    <div class="ds-sidebar__gap" />
    <!-- Fixed rail -->
    <div class="ds-sidebar__rail-wrapper" v-bind="$attrs">
      <div class="ds-sidebar__inner" data-sidebar="sidebar">
        <slot />
      </div>
    </div>
  </div>
</template>

<style>
/* Static (no collapse) */
.ds-sidebar--static {
  display: flex;
  flex-direction: column;
  block-size: 100%;
  inline-size: var(--ds-sidebar-width, 16rem);
  background: var(--ds-color-background);
  color: var(--ds-color-black);
}

/* Mobile dialog */
.ds-sidebar__mobile-overlay {
  position: fixed;
  inset: 0;
  z-index: var(--ds-z-modal);
  background: rgba(15, 16, 26, 0.45);
  animation: ds-fade-in var(--ds-duration-base) var(--ds-ease-out);
}
.ds-sidebar__mobile-overlay[data-state='closed'] {
  animation: ds-fade-out var(--ds-duration-fast) var(--ds-ease-in);
}
.ds-sidebar--mobile {
  position: fixed;
  inset-block: 0;
  z-index: calc(var(--ds-z-modal) + 1);
  inline-size: var(--ds-sidebar-width, 18rem);
  background: var(--ds-color-background);
  color: var(--ds-color-black);
  padding: 0;
  outline: none;
}
.ds-sidebar--mobile[data-side='left'] {
  inset-inline-start: 0;
  animation: ds-slide-in-from-left var(--ds-duration-base) var(--ds-ease-out);
}
.ds-sidebar--mobile[data-side='right'] {
  inset-inline-end: 0;
  animation: ds-slide-in-from-right var(--ds-duration-base) var(--ds-ease-out);
}
.ds-sidebar--mobile[data-state='closed'][data-side='left']  { animation: ds-slide-out-to-left  var(--ds-duration-fast) var(--ds-ease-in); }
.ds-sidebar--mobile[data-state='closed'][data-side='right'] { animation: ds-slide-out-to-right var(--ds-duration-fast) var(--ds-ease-in); }

/* Desktop layout */
.ds-sidebar--desktop {
  display: none;
  color: var(--ds-color-black);
}
@media (min-width: 768px) {
  .ds-sidebar--desktop {
    display: block;
  }
}

.ds-sidebar__gap {
  position: relative;
  inline-size: var(--ds-sidebar-width, 16rem);
  background: transparent;
  transition: inline-size var(--ds-duration-base) var(--ds-ease-linear);
}
.ds-sidebar--desktop[data-collapsible='offcanvas'] .ds-sidebar__gap { inline-size: 0; }
.ds-sidebar--desktop[data-side='right'] .ds-sidebar__gap { transform: rotate(180deg); }

.ds-sidebar--desktop[data-variant='floating'] .ds-sidebar__gap,
.ds-sidebar--desktop[data-variant='inset']    .ds-sidebar__gap {
  /* When collapsed-icon, leave room for icon column + 4 spacing units */
}
.ds-sidebar--desktop[data-collapsible='icon'][data-variant='floating'] .ds-sidebar__gap,
.ds-sidebar--desktop[data-collapsible='icon'][data-variant='inset']    .ds-sidebar__gap {
  inline-size: calc(var(--ds-sidebar-width-icon) + var(--ds-space-md));
}
.ds-sidebar--desktop[data-collapsible='icon']:not([data-variant='floating']):not([data-variant='inset']) .ds-sidebar__gap {
  inline-size: var(--ds-sidebar-width-icon);
}

.ds-sidebar__rail-wrapper {
  position: fixed;
  inset-block: 0;
  z-index: var(--ds-z-sticky);
  display: none;
  block-size: 100svb;
  inline-size: var(--ds-sidebar-width, 16rem);
  transition:
    inset-inline-start var(--ds-duration-base) var(--ds-ease-linear),
    inset-inline-end   var(--ds-duration-base) var(--ds-ease-linear),
    inline-size        var(--ds-duration-base) var(--ds-ease-linear);
}
@media (min-width: 768px) {
  .ds-sidebar__rail-wrapper { display: flex; }
}
.ds-sidebar--desktop[data-side='left']  .ds-sidebar__rail-wrapper { inset-inline-start: 0; }
.ds-sidebar--desktop[data-side='right'] .ds-sidebar__rail-wrapper { inset-inline-end:   0; }
.ds-sidebar--desktop[data-collapsible='offcanvas'][data-side='left']  .ds-sidebar__rail-wrapper { inset-inline-start: calc(var(--ds-sidebar-width) * -1); }
.ds-sidebar--desktop[data-collapsible='offcanvas'][data-side='right'] .ds-sidebar__rail-wrapper { inset-inline-end:   calc(var(--ds-sidebar-width) * -1); }

.ds-sidebar--desktop[data-variant='floating'] .ds-sidebar__rail-wrapper,
.ds-sidebar--desktop[data-variant='inset']    .ds-sidebar__rail-wrapper {
  padding: var(--ds-space-sm);
}
.ds-sidebar--desktop[data-collapsible='icon'][data-variant='floating'] .ds-sidebar__rail-wrapper,
.ds-sidebar--desktop[data-collapsible='icon'][data-variant='inset']    .ds-sidebar__rail-wrapper {
  inline-size: calc(var(--ds-sidebar-width-icon) + var(--ds-space-md) + 2px);
}
.ds-sidebar--desktop[data-collapsible='icon']:not([data-variant='floating']):not([data-variant='inset']) .ds-sidebar__rail-wrapper {
  inline-size: var(--ds-sidebar-width-icon);
}
.ds-sidebar--desktop[data-side='left']:not([data-variant='floating']):not([data-variant='inset'])  .ds-sidebar__rail-wrapper { border-inline-end: 1px solid var(--ds-color-border); }
.ds-sidebar--desktop[data-side='right']:not([data-variant='floating']):not([data-variant='inset']) .ds-sidebar__rail-wrapper { border-inline-start: 1px solid var(--ds-color-border); }

.ds-sidebar__inner {
  display: flex;
  flex-direction: column;
  block-size: 100%;
  inline-size: 100%;
  background: var(--ds-color-background);
  color: var(--ds-color-black);
}
.ds-sidebar--desktop[data-variant='floating'] .ds-sidebar__inner {
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-lg);
  box-shadow: var(--ds-shadow-sm);
}

</style>
