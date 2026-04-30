<script setup lang="ts">
import type { RangeCalendarCellTriggerProps } from 'reka-ui'
import { RangeCalendarCellTrigger, useForwardProps } from 'reka-ui'

const props = withDefaults(defineProps<RangeCalendarCellTriggerProps>(), {
  as: 'button',
})
const forwarded = useForwardProps(props)
</script>

<template>
  <RangeCalendarCellTrigger
    class="ds-range-calendar__cell-trigger"
    data-test="ds-range-calendar-cell-trigger"
    v-bind="forwarded"
  >
    <slot />
  </RangeCalendarCellTrigger>
</template>

<style>
.ds-range-calendar__cell-trigger {
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
.ds-range-calendar__cell-trigger:hover {
  background: var(--ds-color-light);
}
.ds-range-calendar__cell-trigger[data-today]:not([data-selected]) {
  background: var(--ds-color-accent-bg);
  color: var(--ds-color-accent);
}
.ds-range-calendar__cell-trigger[data-selection-start],
.ds-range-calendar__cell-trigger[data-selection-end] {
  background: var(--ds-color-primary);
  color: var(--ds-color-static-white);
}
.ds-range-calendar__cell-trigger[data-selection-start]:hover,
.ds-range-calendar__cell-trigger[data-selection-end]:hover,
.ds-range-calendar__cell-trigger[data-selection-start]:focus-visible,
.ds-range-calendar__cell-trigger[data-selection-end]:focus-visible {
  background: var(--ds-color-primary);
  color: var(--ds-color-static-white);
}
.ds-range-calendar__cell-trigger[data-disabled] {
  color: var(--ds-color-text-grey);
  opacity: 0.5;
}
.ds-range-calendar__cell-trigger[data-unavailable] {
  color: var(--ds-color-error-text);
  text-decoration: line-through;
}
.ds-range-calendar__cell-trigger[data-outside-view] {
  color: var(--ds-color-text-grey);
}
</style>
