<script setup lang="ts">
import type { CalendarPrevProps } from 'reka-ui'
import { CalendarPrev, useForwardProps } from 'reka-ui'

const props = defineProps<CalendarPrevProps>()
const forwarded = useForwardProps(props)
</script>

<template>
  <CalendarPrev
    class="ds-calendar__nav-btn"
    data-test="ds-calendar-prev"
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
  </CalendarPrev>
</template>
