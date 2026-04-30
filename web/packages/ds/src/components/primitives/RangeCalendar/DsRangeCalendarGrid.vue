<script setup lang="ts">
import type { RangeCalendarGridProps } from 'reka-ui'
import { RangeCalendarGrid, useForwardProps } from 'reka-ui'

const props = defineProps<RangeCalendarGridProps>()
const forwarded = useForwardProps(props)
</script>

<template>
  <RangeCalendarGrid
    class="ds-range-calendar__grid"
    data-test="ds-range-calendar-grid"
    v-bind="forwarded"
  >
    <slot />
  </RangeCalendarGrid>
</template>

<style>
.ds-range-calendar__grid {
  inline-size: 100%;
  border-collapse: collapse;
}
</style>
