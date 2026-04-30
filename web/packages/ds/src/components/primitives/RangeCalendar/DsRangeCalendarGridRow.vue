<script setup lang="ts">
import type { RangeCalendarGridRowProps } from 'reka-ui'
import { RangeCalendarGridRow, useForwardProps } from 'reka-ui'

const props = defineProps<RangeCalendarGridRowProps>()
const forwarded = useForwardProps(props)
</script>

<template>
  <RangeCalendarGridRow
    class="ds-range-calendar__grid-row"
    data-test="ds-range-calendar-grid-row"
    v-bind="forwarded"
  >
    <slot />
  </RangeCalendarGridRow>
</template>

<style>
.ds-range-calendar__grid-row {
  display: flex;
}
</style>
