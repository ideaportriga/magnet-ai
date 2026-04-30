<script setup lang="ts">
import type { CalendarNextProps } from 'reka-ui'
import { CalendarNext, useForwardProps } from 'reka-ui'

const props = defineProps<CalendarNextProps>()
const forwarded = useForwardProps(props)
</script>

<template>
  <CalendarNext
    class="ds-calendar__nav-btn"
    data-test="ds-calendar-next"
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
  </CalendarNext>
</template>

<style>
.ds-calendar__nav-btn {
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
.ds-calendar__nav-btn:hover {
  opacity: 1;
  background: var(--ds-color-control-hover-bg);
}
.ds-calendar__nav-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}
</style>
