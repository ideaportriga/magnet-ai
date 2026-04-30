<script setup lang="ts">
/**
 * `<km-range>` — date-range picker with "from" and "to" inputs and a
 * collapsible double-calendar drop-down. Drop-in for the legacy `Range.vue`.
 *
 * Public API kept identical:
 *   title, from, to, displayCalendar, range, isDefaultValues, startValues
 *   emits: update:from, update:to, update:displayCalendar
 */

import { computed, ref } from 'vue'
import { DateTime } from 'luxon'
import KmChip from './KmChip.vue'
import KmDate from './KmDate.vue'
import KmInput from './KmInput.vue'
import KmSeparator from './KmSeparator.vue'

const props = withDefaults(
  defineProps<{
    title: string
    from: DateTime
    to: DateTime
    displayCalendar?: string | null
    range?: false | { min: DateTime; max: DateTime }
    isDefaultValues?: { from: boolean; to: boolean }
    startValues?: { from: DateTime; to: DateTime }
  }>(),
  {
    displayCalendar: null,
    range: false,
    isDefaultValues: () => ({ from: true, to: true }),
    startValues: () => ({ from: DateTime.now(), to: DateTime.now() }),
  },
)

const emit = defineEmits<{
  'update:from': [value: DateTime]
  'update:to': [value: DateTime]
  'update:displayCalendar': [value: string | null]
}>()

const today = ref(DateTime.now())

const inputValues = computed(() => ({
  from: props.from?.isValid ? props.from.toFormat('dd.LL.yyyy') : '',
  to: props.to?.isValid ? props.to.toFormat('dd.LL.yyyy') : '',
}))

const open = computed(() => props.displayCalendar === props.title)

function toggleOpen() {
  emit('update:displayCalendar', open.value ? null : props.title)
}

function reset(field: 'from' | 'to') {
  emit(`update:${field}`, props.startValues[field])
}

function setToday() {
  emit('update:from', today.value)
  emit('update:to', today.value)
}

function shiftMonth(offset = 0) {
  const month = today.value.plus({ months: offset })
  emit('update:from', month.startOf('month'))
  emit('update:to', month.endOf('month'))
}

function shiftWeek(offset = 0) {
  const week = today.value.plus({ weeks: offset })
  emit('update:from', week.startOf('week'))
  emit('update:to', week.endOf('week'))
}
</script>

<template>
  <div class="km-range stack" data-gap="sm" data-test="km-range">
    <span class="km-range__title">{{ title }}</span>

    <div
      class="km-range__row"
      :data-open="open ? 'true' : undefined"
      @click="toggleOpen"
    >
      <span class="km-range__between">Between</span>

      <KmInput
        class="km-range__input"
        readonly
        rounded
        dense
        icon-before="calendar"
        :placeholder="inputValues.from"
        :model-value="!isDefaultValues.from ? inputValues.from : ''"
        :custom-clear-action="() => reset('from')"
      />

      <span class="km-range__and">and</span>

      <KmInput
        class="km-range__input"
        readonly
        rounded
        dense
        icon-before="calendar"
        :placeholder="inputValues.to"
        :model-value="!isDefaultValues.to ? inputValues.to : ''"
        :custom-clear-action="() => reset('to')"
      />
    </div>

    <div v-if="open" class="km-range__panel stack" data-gap="sm">
      <div class="km-range__calendars cluster gap-md" data-justify="center">
        <KmDate
          :date="from"
          :range="range"
          :options="(d: DateTime) => d <= to"
          @update:date="(v: DateTime) => emit('update:from', v)"
        />
        <KmDate
          :date="to"
          :range="range"
          :options="(d: DateTime) => d >= from"
          @update:date="(v: DateTime) => emit('update:to', v)"
        />
      </div>

      <KmSeparator />

      <div class="km-range__shortcuts cluster gap-sm">
        <KmChip display="filter" tone="neutral" clickable @click="shiftMonth(-1)">
          <span class="km-chip__heading">Last month</span>
        </KmChip>
        <KmChip display="filter" tone="neutral" clickable @click="setToday">
          <span class="km-chip__heading">Today</span>
        </KmChip>
        <KmChip display="filter" tone="neutral" clickable @click="shiftWeek(0)">
          <span class="km-chip__heading">This week</span>
        </KmChip>
        <KmChip display="filter" tone="neutral" clickable @click="shiftMonth(0)">
          <span class="km-chip__heading">This month</span>
        </KmChip>
        <KmChip display="filter" tone="neutral" clickable @click="shiftMonth(1)">
          <span class="km-chip__heading">Next month</span>
        </KmChip>
      </div>
    </div>
  </div>
</template>

<style>
.km-range__title {
  font-size: var(--ds-font-size-label);
  font-weight: var(--ds-font-weight-medium);
  color: var(--ds-color-black);
}
.km-range__row {
  display: grid;
  grid-template-columns: 70px minmax(0, 3fr) 40px minmax(0, 3fr);
  gap: var(--ds-space-sm);
  align-items: center;
  cursor: pointer;
}
.km-range__between,
.km-range__and {
  font-size: var(--ds-font-size-caption);
  color: var(--ds-color-secondary-text);
  text-align: center;
}
.km-range__input { inline-size: 235px; }

.km-range__panel {
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-md);
  padding: var(--ds-space-md);
  background: var(--ds-color-white);
}

.km-range__calendars {
  /* CUBE composition: cluster handles wrap automatically */
}
</style>
