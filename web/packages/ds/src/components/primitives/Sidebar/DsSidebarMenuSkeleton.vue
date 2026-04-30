<script setup lang="ts">
import { computed } from 'vue'
import DsSkeleton from '../Skeleton/DsSkeleton.vue'

defineProps<{
  showIcon?: boolean
}>()

const width = computed(() => `${Math.floor(Math.random() * 40) + 50}%`)
</script>

<template>
  <div
    class="ds-sidebar__menu-skeleton"
    data-sidebar="menu-skeleton"
    data-test="ds-sidebar-menu-skeleton"
  >
    <DsSkeleton
      v-if="showIcon"
      class="ds-sidebar__menu-skeleton-icon"
      data-sidebar="menu-skeleton-icon"
    />
    <DsSkeleton
      class="ds-sidebar__menu-skeleton-text"
      data-sidebar="menu-skeleton-text"
      :style="{ '--ds-skeleton-width': width }"
    />
  </div>
</template>

<style>
.ds-sidebar__menu-skeleton {
  display: flex;
  align-items: center;
  gap: var(--ds-space-sm);
  block-size: 32px;
  padding-inline: var(--ds-space-sm);
  border-radius: var(--ds-radius-md);
}
.ds-sidebar__menu-skeleton-icon {
  inline-size: 16px;
  block-size: 16px;
  border-radius: var(--ds-radius-sm);
}
.ds-sidebar__menu-skeleton-text {
  block-size: 16px;
  flex: 1;
  max-inline-size: var(--ds-skeleton-width);
}
</style>
