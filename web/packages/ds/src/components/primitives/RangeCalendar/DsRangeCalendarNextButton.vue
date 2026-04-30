<script setup lang="ts">
import type { RangeCalendarNextProps } from 'reka-ui'
import { RangeCalendarNext, useForwardProps } from 'reka-ui'

const props = defineProps<RangeCalendarNextProps>()
const forwarded = useForwardProps(props)
</script>

<template>
  <RangeCalendarNext
    class="ds-range-calendar__nav-btn ds-range-calendar__nav-btn--next"
    data-test="ds-range-calendar-next"
    v-bind="forwarded"
  >
    <slot>
      <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
        <path
          d="M5 3 L9 7 L5 11"
          stroke="currentColor"
          stroke-width="1.6"
          fill="none"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
    </slot>
  </RangeCalendarNext>
</template>

<style>
.ds-range-calendar__nav-btn {
  position: absolute;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  inline-size: 28px;
  block-size: 28px;
  padding: 0;
  background: transparent;
  color: var(--ds-color-black);
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-md);
  opacity: 0.5;
  cursor: pointer;
  transition: opacity var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-range-calendar__nav-btn:hover {
  opacity: 1;
  background: var(--ds-color-control-hover-bg);
}
.ds-range-calendar__nav-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}
.ds-range-calendar__nav-btn--next {
  inset-inline-end: var(--ds-space-2xs);
}
.ds-range-calendar__nav-btn--prev {
  inset-inline-start: var(--ds-space-2xs);
}
</style>
