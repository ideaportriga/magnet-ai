<script setup lang="ts">
import type { CalendarHeadCellProps } from 'reka-ui'
import { CalendarHeadCell, useForwardProps } from 'reka-ui'

const props = defineProps<CalendarHeadCellProps>()
const forwarded = useForwardProps(props)
</script>

<template>
  <CalendarHeadCell
    class="ds-calendar__head-cell"
    data-test="ds-calendar-head-cell"
    v-bind="forwarded"
  >
    <slot />
  </CalendarHeadCell>
</template>

<style>
.ds-calendar__head-cell {
  flex: 1;
  font-size: var(--ds-font-size-xs);
  font-weight: var(--ds-font-weight-regular);
  color: var(--ds-color-text-grey);
  border-radius: var(--ds-radius-sm);
  text-align: center;
}
</style>
