<script setup lang="ts">
import type { RangeCalendarPrevProps } from 'reka-ui'
import { RangeCalendarPrev, useForwardProps } from 'reka-ui'

const props = defineProps<RangeCalendarPrevProps>()
const forwarded = useForwardProps(props)
</script>

<template>
  <RangeCalendarPrev
    class="ds-range-calendar__nav-btn ds-range-calendar__nav-btn--prev"
    data-test="ds-range-calendar-prev"
    v-bind="forwarded"
  >
    <slot>
      <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
        <path
          d="M9 3 L5 7 L9 11"
          stroke="currentColor"
          stroke-width="1.6"
          fill="none"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
    </slot>
  </RangeCalendarPrev>
</template>
