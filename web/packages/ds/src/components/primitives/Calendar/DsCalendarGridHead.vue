<script setup lang="ts">
import type { CalendarGridHeadProps } from 'reka-ui'
import { CalendarGridHead } from 'reka-ui'

const props = defineProps<CalendarGridHeadProps>()
</script>

<template>
  <CalendarGridHead data-test="ds-calendar-grid-head" v-bind="props">
    <slot />
  </CalendarGridHead>
</template>
