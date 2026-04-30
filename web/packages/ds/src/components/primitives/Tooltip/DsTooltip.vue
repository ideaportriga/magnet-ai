<script setup lang="ts">
/**
 * Tooltip primitive — wrapped Reka UI Tooltip.
 *
 *   <DsTooltip text="Save changes" placement="top">
 *     <button>Save</button>
 *   </DsTooltip>
 *
 * Or with rich content:
 *
 *   <DsTooltip placement="right">
 *     <template #trigger><button /></template>
 *     <strong>Hint</strong> <em>more details</em>
 *   </DsTooltip>
 */

import {
  TooltipArrow,
  TooltipContent,
  TooltipPortal,
  TooltipProvider,
  TooltipRoot,
  TooltipTrigger,
} from 'reka-ui'

export type DsTooltipPlacement = 'top' | 'right' | 'bottom' | 'left'

withDefaults(
  defineProps<{
    text?: string
    placement?: DsTooltipPlacement
    /** Distance in pixels between the tooltip and the trigger. */
    sideOffset?: number
    /** Delay before the tooltip appears, in ms. */
    delay?: number
    /** Hide the small arrow indicator. */
    noArrow?: boolean
    /** Disable the tooltip without removing it from the markup. */
    disabled?: boolean
  }>(),
  {
    placement: 'top',
    sideOffset: 6,
    delay: 200,
    noArrow: false,
    disabled: false,
  },
)

defineSlots<{
  trigger?: () => unknown
  default?: () => unknown
}>()
</script>

<template>
  <TooltipProvider :delay-duration="delay" :disable-hoverable-content="false">
    <TooltipRoot :open="disabled ? false : undefined">
      <TooltipTrigger as-child>
        <slot name="trigger">
          <slot />
        </slot>
      </TooltipTrigger>

      <TooltipPortal>
        <TooltipContent
          class="ds-tooltip"
          :side="placement"
          :side-offset="sideOffset"
          :align="'center'"
          data-test="ds-tooltip"
        >
          <slot v-if="$slots.trigger && $slots.default" />
          <template v-else>{{ text }}</template>
          <TooltipArrow v-if="!noArrow" class="ds-tooltip__arrow" />
        </TooltipContent>
      </TooltipPortal>
    </TooltipRoot>
  </TooltipProvider>
</template>

<style>
.ds-tooltip {
  z-index: var(--ds-z-tooltip);
  padding: var(--ds-space-xs) var(--ds-space-sm);
  background: var(--ds-color-tooltip-bg);
  color: var(--ds-color-tooltip-text);
  font-size: var(--ds-font-size-caption);
  font-weight: var(--ds-font-weight-medium);
  line-height: var(--ds-line-height-snug);
  border-radius: var(--ds-radius-sm);
  box-shadow: var(--ds-shadow-md);
  user-select: none;
  animation: ds-scale-in var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-tooltip[data-state='closed'] {
  animation: ds-fade-out var(--ds-duration-instant) var(--ds-ease-in);
}
.ds-tooltip__arrow { fill: var(--ds-color-tooltip-bg); }
</style>
