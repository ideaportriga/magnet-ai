<script setup lang="ts">
/**
 * `<km-drawer-layout>` — drawer skeleton with header / tabs / content /
 * footer slots and a left-edge resize handle. The width is persisted via
 * `useDrawerResize` (localStorage-backed).
 *
 * Drop-in replacement for the legacy DrawerLayout (which used
 * `q-scroll-area` for the content region). We use a native scroll container
 * styled via the `@ds` scrollbars; if the legacy fancy scroll is required,
 * wrap the slot in `<DsScrollArea>` directly.
 */

import { useDrawerResize } from '../../composables/useDrawerResize'

const props = withDefaults(
  defineProps<{
    storageKey: string
    defaultWidth?: number
    minWidth?: number
    maxWidth?: number
    /** When true, the content slot takes its own scroll responsibility. */
    noScroll?: boolean
    /** Default text shown by the built-in empty state when no default slot
     * content is provided. Overridable via the `#empty` slot. */
    emptyText?: string
  }>(),
  {
    defaultWidth: 500,
    minWidth: 320,
    maxWidth: 900,
    noScroll: false,
    emptyText: 'Nothing to show',
  },
)

const { drawerStyle, onResizeStart } = useDrawerResize({
  storageKey: props.storageKey,
  defaultWidth: props.defaultWidth,
  minWidth: props.minWidth,
  maxWidth: props.maxWidth,
})

defineSlots<{
  header?: () => unknown
  tabs?: () => unknown
  default?: () => unknown
  empty?: () => unknown
  footer?: () => unknown
}>()
</script>

<template>
  <aside
    class="km-drawer-layout"
    :style="drawerStyle"
    data-test="km-drawer-layout"
  >
    <span
      class="km-drawer-layout__handle"
      role="separator"
      aria-orientation="vertical"
      aria-label="Resize drawer"
      tabindex="0"
      @mousedown="onResizeStart"
    />

    <header v-if="$slots.header" class="km-drawer-layout__header">
      <slot name="header" />
    </header>

    <div v-if="$slots.tabs" class="km-drawer-layout__tabs">
      <slot name="tabs" />
    </div>

    <div
      class="km-drawer-layout__content"
      :data-scroll="noScroll ? 'plain' : 'auto'"
    >
      <slot>
        <div class="km-drawer-layout__empty" data-test="km-drawer-layout-empty">
          <slot name="empty">
            <p class="km-drawer-layout__empty-text">{{ emptyText }}</p>
          </slot>
        </div>
      </slot>
    </div>

    <footer v-if="$slots.footer" class="km-drawer-layout__footer">
      <slot name="footer" />
    </footer>
  </aside>
</template>

<style>
.km-drawer-layout {
  position: relative;
  display: flex;
  flex-direction: column;
  block-size: 100%;
  background: var(--ds-color-white);
  border-inline-start: 1px solid var(--ds-color-border);
}

.km-drawer-layout__handle {
  position: absolute;
  inset-block: 0;
  inset-inline-start: -3px;
  inline-size: 6px;
  cursor: col-resize;
  z-index: var(--ds-z-raised);
}
.km-drawer-layout__handle:hover { background: var(--ds-color-primary-bg); }

.km-drawer-layout__header {
  padding: var(--ds-space-lg);
  background: var(--ds-color-panel-main-bg);
  flex: 0 0 auto;
}
.km-drawer-layout__tabs {
  background: var(--ds-color-panel-main-bg);
  flex: 0 0 auto;
}
.km-drawer-layout__footer {
  padding: var(--ds-space-md) var(--ds-space-lg);
  /* Opaque background so the scrollable content above doesn't show through
   * at the bottom of the viewport. flex: 0 0 auto pins the footer so it
   * never gets squashed by overflowing body content. */
  background: var(--ds-color-panel-main-bg);
  flex: 0 0 auto;
}

.km-drawer-layout__content {
  flex: 1 1 auto;
  min-block-size: 0;
  padding: var(--ds-space-lg);
}
.km-drawer-layout__content[data-scroll='auto'] { overflow: auto; overscroll-behavior: contain; }

.km-drawer-layout__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  block-size: 100%;
  min-block-size: 12rem;
  gap: var(--ds-space-sm);
  padding: var(--ds-space-2xl);
  text-align: center;
  color: var(--ds-color-text-grey);
}
.km-drawer-layout__empty-text {
  margin: 0;
  font-size: var(--ds-font-size-label);
}
</style>
