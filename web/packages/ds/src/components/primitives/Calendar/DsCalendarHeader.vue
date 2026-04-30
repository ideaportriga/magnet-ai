<script setup lang="ts">
import type { CalendarHeaderProps } from 'reka-ui'
import { CalendarHeader, useForwardProps } from 'reka-ui'

const props = defineProps<CalendarHeaderProps>()
const forwarded = useForwardProps(props)
</script>

<template>
  <CalendarHeader
    class="ds-calendar__header"
    data-test="ds-calendar-header"
    v-bind="forwarded"
  >
    <slot />
  </CalendarHeader>
</template>

<style>
.ds-calendar__header {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding-block-start: var(--ds-space-2xs);
  padding-inline: var(--ds-space-2xl);
  inline-size: 100%;
}
</style>
