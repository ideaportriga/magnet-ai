<script setup lang="ts">
import { useSidebar } from './utils'

const { toggleSidebar } = useSidebar()
</script>

<template>
  <button
    class="ds-sidebar__rail"
    data-test="ds-sidebar-rail"
    aria-label="Toggle Sidebar"
    title="Toggle Sidebar"
    :tabindex="-1"
    type="button"
    @click="toggleSidebar"
  >
    <slot />
  </button>
</template>

<style>
.ds-sidebar__rail {
  display: none;
  position: absolute;
  inset-block: 0;
  z-index: 2;
  inline-size: 16px;
  transform: translateX(-50%);
  background: transparent;
  border: 0;
  cursor: ew-resize;
}
@media (min-width: 640px) {
  .ds-sidebar__rail { display: flex; }
}
.ds-sidebar__rail::after {
  content: '';
  position: absolute;
  inset-block: 0;
  inset-inline-start: 50%;
  inline-size: 2px;
  transition: background-color var(--ds-duration-base) var(--ds-ease-linear);
}
.ds-sidebar__rail:hover::after {
  background: var(--ds-color-border);
}

[data-side='left']  .ds-sidebar__rail { inset-inline-end: -16px; }
[data-side='right'] .ds-sidebar__rail { inset-inline-start: 0; }
</style>
