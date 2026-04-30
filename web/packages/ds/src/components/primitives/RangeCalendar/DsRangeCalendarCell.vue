<script setup lang="ts">
import type { RangeCalendarCellProps } from 'reka-ui'
import { RangeCalendarCell, useForwardProps } from 'reka-ui'

const props = defineProps<RangeCalendarCellProps>()
const forwarded = useForwardProps(props)
</script>

<template>
  <RangeCalendarCell
    class="ds-range-calendar__cell"
    data-test="ds-range-calendar-cell"
    v-bind="forwarded"
  >
    <slot />
  </RangeCalendarCell>
</template>

<style>
.ds-range-calendar__cell {
  position: relative;
  padding: 0;
  text-align: center;
  font-size: var(--ds-font-size-label);
}
.ds-range-calendar__cell:focus-within {
  position: relative;
  z-index: 2;
}
.ds-range-calendar__cell:has([data-selected]) {
  background: var(--ds-color-accent-bg);
}
.ds-range-calendar__cell:first-child:has([data-selected]) {
  border-start-start-radius: var(--ds-radius-md);
  border-end-start-radius: var(--ds-radius-md);
}
.ds-range-calendar__cell:last-child:has([data-selected]) {
  border-start-end-radius: var(--ds-radius-md);
  border-end-end-radius: var(--ds-radius-md);
}
.ds-range-calendar__cell:has([data-selection-start]) {
  border-start-start-radius: var(--ds-radius-md);
  border-end-start-radius: var(--ds-radius-md);
}
.ds-range-calendar__cell:has([data-selection-end]) {
  border-start-end-radius: var(--ds-radius-md);
  border-end-end-radius: var(--ds-radius-md);
}
</style>
