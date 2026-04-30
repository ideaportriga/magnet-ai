<script setup lang="ts">
import type { RangeCalendarHeaderProps } from 'reka-ui'
import { RangeCalendarHeader, useForwardProps } from 'reka-ui'

const props = defineProps<RangeCalendarHeaderProps>()
const forwarded = useForwardProps(props)
</script>

<template>
  <RangeCalendarHeader
    class="ds-range-calendar__header"
    data-test="ds-range-calendar-header"
    v-bind="forwarded"
  >
    <slot />
  </RangeCalendarHeader>
</template>

<style>
.ds-range-calendar__header {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding-block-start: var(--ds-space-2xs);
  inline-size: 100%;
}
</style>
