<script setup lang="ts">
import type { CalendarGridRowProps } from 'reka-ui'
import { CalendarGridRow, useForwardProps } from 'reka-ui'

const props = defineProps<CalendarGridRowProps>()
const forwarded = useForwardProps(props)
</script>

<template>
  <CalendarGridRow
    class="ds-calendar__grid-row"
    data-test="ds-calendar-grid-row"
    v-bind="forwarded"
  >
    <slot />
  </CalendarGridRow>
</template>

<style>
.ds-calendar__grid-row {
  display: flex;
}
</style>
