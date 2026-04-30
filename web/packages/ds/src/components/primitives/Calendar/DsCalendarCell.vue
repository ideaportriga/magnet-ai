<script setup lang="ts">
import type { CalendarCellProps } from 'reka-ui'
import { CalendarCell, useForwardProps } from 'reka-ui'

const props = defineProps<CalendarCellProps>()
const forwarded = useForwardProps(props)
</script>

<template>
  <CalendarCell
    class="ds-calendar__cell"
    data-test="ds-calendar-cell"
    v-bind="forwarded"
  >
    <slot />
  </CalendarCell>
</template>

<style>
.ds-calendar__cell {
  position: relative;
  flex: 1;
  padding: 0;
  text-align: center;
  font-size: var(--ds-font-size-label);
}
.ds-calendar__cell:focus-within {
  position: relative;
  z-index: 2;
}
.ds-calendar__cell:has([data-selected]) {
  border-radius: var(--ds-radius-md);
  background: var(--ds-color-accent-bg);
}
</style>
