<script setup lang="ts">
import DsButton from '../Button/DsButton.vue'
import { useSidebar } from './utils'

const { toggleSidebar } = useSidebar()
</script>

<template>
  <DsButton
    class="ds-sidebar__trigger"
    data-test="ds-sidebar-trigger"
    variant="ghost"
    size="icon-sm"
    @click="toggleSidebar"
  >
    <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
      <rect x="1.5" y="2" width="11" height="10" rx="1.5" stroke="currentColor" stroke-width="1.4" fill="none" />
      <line x1="5.5" y1="2" x2="5.5" y2="12" stroke="currentColor" stroke-width="1.4" />
    </svg>
    <span class="ds-sidebar__sr">Toggle Sidebar</span>
  </DsButton>
</template>

<style>
.ds-sidebar__trigger {
  inline-size: 28px;
  block-size: 28px;
}
.ds-sidebar__sr {
  position: absolute;
  inline-size: 1px;
  block-size: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
  border: 0;
}
</style>
