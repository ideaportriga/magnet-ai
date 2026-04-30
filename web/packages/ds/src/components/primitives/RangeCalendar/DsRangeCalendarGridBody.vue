<script setup lang="ts">
import type { RangeCalendarGridBodyProps } from 'reka-ui'
import { RangeCalendarGridBody } from 'reka-ui'

const props = defineProps<RangeCalendarGridBodyProps>()
</script>

<template>
  <RangeCalendarGridBody data-test="ds-range-calendar-grid-body" v-bind="props">
    <slot />
  </RangeCalendarGridBody>
</template>
