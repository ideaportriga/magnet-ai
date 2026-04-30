<script setup lang="ts">
import type { CalendarHeadingProps } from 'reka-ui'
import { CalendarHeading, useForwardProps } from 'reka-ui'

defineSlots<{
  default: (props: { headingValue: string }) => any
}>()

const props = defineProps<CalendarHeadingProps>()
const forwarded = useForwardProps(props)
</script>

<template>
  <CalendarHeading
    v-slot="{ headingValue }"
    class="ds-calendar__heading"
    data-test="ds-calendar-heading"
    v-bind="forwarded"
  >
    <slot :heading-value="headingValue">
      {{ headingValue }}
    </slot>
  </CalendarHeading>
</template>

<style>
.ds-calendar__heading {
  font-size: var(--ds-font-size-label);
  font-weight: var(--ds-font-weight-medium);
  color: var(--ds-color-black);
}
</style>
