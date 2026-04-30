<script setup lang="ts">
import type { CalendarGridProps } from 'reka-ui'
import { CalendarGrid, useForwardProps } from 'reka-ui'

const props = defineProps<CalendarGridProps>()
const forwarded = useForwardProps(props)
</script>

<template>
  <CalendarGrid
    class="ds-calendar__grid"
    data-test="ds-calendar-grid"
    v-bind="forwarded"
  >
    <slot />
  </CalendarGrid>
</template>

<style>
.ds-calendar__grid {
  inline-size: 100%;
  border-collapse: collapse;
}
</style>
