<script setup lang="ts">
import type { RangeCalendarHeadingProps } from 'reka-ui'
import { RangeCalendarHeading, useForwardProps } from 'reka-ui'

defineSlots<{
  default: (props: { headingValue: string }) => any
}>()

const props = defineProps<RangeCalendarHeadingProps>()
const forwarded = useForwardProps(props)
</script>

<template>
  <RangeCalendarHeading
    v-slot="{ headingValue }"
    class="ds-range-calendar__heading"
    data-test="ds-range-calendar-heading"
    v-bind="forwarded"
  >
    <slot :heading-value="headingValue">
      {{ headingValue }}
    </slot>
  </RangeCalendarHeading>
</template>

<style>
.ds-range-calendar__heading {
  font-size: var(--ds-font-size-label);
  font-weight: var(--ds-font-weight-medium);
  color: var(--ds-color-black);
}
</style>
