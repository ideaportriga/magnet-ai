<script setup lang="ts">
import type { RangeCalendarHeadCellProps } from 'reka-ui'
import { RangeCalendarHeadCell, useForwardProps } from 'reka-ui'

const props = defineProps<RangeCalendarHeadCellProps>()
const forwarded = useForwardProps(props)
</script>

<template>
  <RangeCalendarHeadCell
    class="ds-range-calendar__head-cell"
    data-test="ds-range-calendar-head-cell"
    v-bind="forwarded"
  >
    <slot />
  </RangeCalendarHeadCell>
</template>

<style>
.ds-range-calendar__head-cell {
  inline-size: 32px;
  font-size: var(--ds-font-size-xs);
  font-weight: var(--ds-font-weight-regular);
  color: var(--ds-color-text-grey);
  border-radius: var(--ds-radius-sm);
  text-align: center;
}
</style>
