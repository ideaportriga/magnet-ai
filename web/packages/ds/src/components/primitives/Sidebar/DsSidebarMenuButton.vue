<script setup lang="ts">
import type { Component } from 'vue'
import type { SidebarMenuButtonProps } from './DsSidebarMenuButtonChild.vue'
import {
  TooltipContent,
  TooltipPortal,
  TooltipProvider,
  TooltipRoot,
  TooltipTrigger,
} from 'reka-ui'
import DsSidebarMenuButtonChild from './DsSidebarMenuButtonChild.vue'
import { useSidebar } from './utils'

defineOptions({
  inheritAttrs: false,
})

const props = defineProps<SidebarMenuButtonProps & { tooltip?: string | Component }>()

const { isMobile, state } = useSidebar()
</script>

<template>
  <DsSidebarMenuButtonChild
    v-if="!props.tooltip"
    :as="props.as"
    :as-child="props.asChild"
    :variant="props.variant"
    :size="props.size"
    :is-active="props.isActive"
    v-bind="$attrs"
  >
    <slot />
  </DsSidebarMenuButtonChild>

  <TooltipProvider v-else>
    <TooltipRoot>
      <TooltipTrigger as-child>
        <DsSidebarMenuButtonChild
          :as="props.as"
          :as-child="props.asChild"
          :variant="props.variant"
          :size="props.size"
          :is-active="props.isActive"
          v-bind="$attrs"
        >
          <slot />
        </DsSidebarMenuButtonChild>
      </TooltipTrigger>
      <TooltipPortal>
        <TooltipContent
          class="ds-sidebar__menu-tooltip"
          side="right"
          align="center"
          :hidden="state !== 'collapsed' || isMobile"
        >
          <template v-if="typeof props.tooltip === 'string'">
            {{ props.tooltip }}
          </template>
          <component :is="props.tooltip" v-else />
        </TooltipContent>
      </TooltipPortal>
    </TooltipRoot>
  </TooltipProvider>
</template>

<style>
.ds-sidebar__menu-tooltip {
  z-index: var(--ds-z-tooltip);
  padding: var(--ds-space-2xs) var(--ds-space-sm);
  font-size: var(--ds-font-size-xs);
  color: var(--ds-color-static-white);
  background: var(--ds-color-black);
  border-radius: var(--ds-radius-sm);
}
</style>
