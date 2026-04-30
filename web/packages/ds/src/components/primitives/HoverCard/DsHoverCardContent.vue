<script setup lang="ts">
/**
 * HoverCardContent — popover content rendered inside a portal. All Reka
 * positioning props (`side`, `align`, `sideOffset`, …) pass through.
 */

import { reactiveOmit } from '@vueuse/core'
import {
  HoverCardContent,
  type HoverCardContentProps,
  HoverCardPortal,
  useForwardProps,
} from 'reka-ui'

defineOptions({ inheritAttrs: false })

const props = withDefaults(defineProps<HoverCardContentProps>(), {
  sideOffset: 4,
})

const delegatedProps = reactiveOmit(props, 'class' as never)
const forwardedProps = useForwardProps(delegatedProps)
</script>

<template>
  <HoverCardPortal>
    <HoverCardContent
      v-bind="{ ...$attrs, ...forwardedProps }"
      class="ds-hover-card__content"
      data-test="ds-hover-card-content"
    >
      <slot />
    </HoverCardContent>
  </HoverCardPortal>
</template>

<style>
.ds-hover-card__content {
  z-index: var(--ds-z-popover);
  inline-size: 16rem;
  background: var(--ds-color-white);
  color: var(--ds-color-black);
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-md);
  padding: var(--ds-space-lg);
  box-shadow: var(--ds-shadow-md);
  outline: none;
  font-family: var(--ds-font-default);
  font-size: var(--ds-font-size-label);
}
.ds-hover-card__content[data-state='open'] {
  animation: ds-scale-in var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-hover-card__content[data-state='closed'] {
  animation: ds-scale-out var(--ds-duration-fast) var(--ds-ease-in);
}
</style>
