<script setup lang="ts">
import type { CalendarCellTriggerProps } from 'reka-ui'
import { CalendarCellTrigger, useForwardProps } from 'reka-ui'

const props = withDefaults(defineProps<CalendarCellTriggerProps>(), {
  as: 'button',
})
const forwarded = useForwardProps(props)
</script>

<template>
  <CalendarCellTrigger
    class="ds-calendar__cell-trigger"
    data-test="ds-calendar-cell-trigger"
    v-bind="forwarded"
  >
    <slot />
  </CalendarCellTrigger>
</template>

<style>
.ds-calendar__cell-trigger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  inline-size: 32px;
  block-size: 32px;
  padding: 0;
  font-family: var(--ds-font-default);
  font-size: var(--ds-font-size-label);
  font-weight: var(--ds-font-weight-regular);
  color: var(--ds-color-black);
  background: transparent;
  border: 0;
  border-radius: var(--ds-radius-md);
  cursor: default;
  transition:
    background var(--ds-duration-fast) var(--ds-ease-out),
    color var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-calendar__cell-trigger:hover {
  background: var(--ds-color-light);
}
.ds-calendar__cell-trigger[data-today]:not([data-selected]) {
  background: var(--ds-color-accent-bg);
  color: var(--ds-color-accent);
}
.ds-calendar__cell-trigger[data-selected] {
  background: var(--ds-color-primary);
  color: var(--ds-color-static-white);
}
.ds-calendar__cell-trigger[data-selected]:hover,
.ds-calendar__cell-trigger[data-selected]:focus-visible {
  background: var(--ds-color-primary);
  color: var(--ds-color-static-white);
}
.ds-calendar__cell-trigger[data-disabled] {
  color: var(--ds-color-text-grey);
  opacity: 0.5;
}
.ds-calendar__cell-trigger[data-unavailable] {
  color: var(--ds-color-error-text);
  text-decoration: line-through;
}
.ds-calendar__cell-trigger[data-outside-view] {
  color: var(--ds-color-text-grey);
}
</style>
