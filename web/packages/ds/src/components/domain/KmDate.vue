<script setup lang="ts">
/**
 * `<km-date>` — calendar / date-picker. Drop-in for the legacy `Date.vue`
 * that was a wrapper over `<km-date>` working with Luxon's `DateTime`.
 *
 * Public surface preserved:
 *   - `:date` — Luxon DateTime (legacy contract); `@update:date` emits one.
 *   - `:range` — `false` (default) or `{ min, max }` Luxon DateTimes that
 *     constrain the navigable months.
 *   - `:options(date: DateTime): boolean` — per-day enable predicate.
 *
 * Internally we use Reka UI's `Calendar` primitive, which reads/writes
 * `@internationalized/date` `CalendarDate` values; we translate at the
 * boundary.
 */

import {
  CalendarCell,
  CalendarCellTrigger,
  CalendarGrid,
  CalendarGridBody,
  CalendarGridHead,
  CalendarGridRow,
  CalendarHeadCell,
  CalendarHeader,
  CalendarHeading,
  CalendarNext,
  CalendarPrev,
  CalendarRoot,
} from 'reka-ui'
import { CalendarDate, type DateValue } from '@internationalized/date'
import { DateTime } from 'luxon'
import { computed } from 'vue'
import KmGlyph from './KmGlyph.vue'

const props = withDefaults(
  defineProps<{
    /** Active date — Luxon DateTime (legacy contract). */
    date: DateTime
    /** Render in compact mode (no header buttons). */
    minimal?: boolean
    /** When set, restrict navigable months to `min..max`. */
    range?: false | { min: DateTime; max: DateTime }
    /** Enable predicate evaluated per-day. */
    options?: (date: DateTime) => boolean
  }>(),
  {
    minimal: true,
    range: false,
    options: () => true,
  },
)

const emit = defineEmits<{
  'update:date': [value: DateTime]
}>()

function dateTimeToCalendar(dt: DateTime): CalendarDate {
  return new CalendarDate(dt.year, dt.month, dt.day)
}

function calendarToDateTime(value: DateValue): DateTime {
  return DateTime.fromObject({ year: value.year, month: value.month, day: value.day })
}

const calendarValue = computed(() => dateTimeToCalendar(props.date))

const minValue = computed(() => (props.range ? dateTimeToCalendar(props.range.min) : undefined))
const maxValue = computed(() => (props.range ? dateTimeToCalendar(props.range.max) : undefined))

function isDateUnavailable(value: DateValue): boolean {
  const dt = calendarToDateTime(value)
  return !props.options(dt)
}

function handleUpdate(next: DateValue | undefined) {
  if (!next) return
  emit('update:date', calendarToDateTime(next))
}
</script>

<template>
  <CalendarRoot
    :model-value="calendarValue"
    :min-value="minValue"
    :max-value="maxValue"
    :is-date-unavailable="isDateUnavailable"
    :weekday-format="'short'"
    :first-day-of-week="1"
    class="km-date"
    data-test="km-date"
    @update:model-value="handleUpdate"
  >
    <CalendarHeader v-if="!minimal" class="km-date__header">
      <CalendarPrev class="km-date__nav" aria-label="Previous month">
        <KmGlyph name="chevron_left" size="20px" />
      </CalendarPrev>
      <CalendarHeading class="km-date__title" />
      <CalendarNext class="km-date__nav" aria-label="Next month">
        <KmGlyph name="chevron_right" size="20px" />
      </CalendarNext>
    </CalendarHeader>

    <CalendarGrid v-slot="{ month, weekDays }" class="km-date__grid">
      <CalendarGridHead>
        <CalendarGridRow class="km-date__row">
          <CalendarHeadCell
            v-for="day in weekDays"
            :key="day"
            class="km-date__weekday"
          >
            {{ day }}
          </CalendarHeadCell>
        </CalendarGridRow>
      </CalendarGridHead>

      <CalendarGridBody>
        <CalendarGridRow
          v-for="(weekDates, weekIndex) in month.rows"
          :key="`week-${weekIndex}`"
          class="km-date__row"
        >
          <CalendarCell
            v-for="weekDate in weekDates"
            :key="weekDate.toString()"
            :date="weekDate"
            class="km-date__cell"
          >
            <CalendarCellTrigger
              :day="weekDate"
              :month="month.value"
              class="km-date__day"
              data-test="km-date-day"
            />
          </CalendarCell>
        </CalendarGridRow>
      </CalendarGridBody>
    </CalendarGrid>
  </CalendarRoot>
</template>

<style>
.km-date {
  display: inline-flex;
  flex-direction: column;
  gap: var(--ds-space-sm);
  padding: var(--ds-space-md);
  background: var(--ds-color-white);
  border-radius: var(--ds-radius-md);
  font-size: var(--ds-font-size-label);
  user-select: none;
}

.km-date__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--ds-space-sm);
}
.km-date__title {
  font-weight: var(--ds-font-weight-semibold);
  text-align: center;
  flex: 1 1 auto;
}
.km-date__nav {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  inline-size: 28px;
  block-size: 28px;
  background: transparent;
  border: 0;
  border-radius: var(--ds-radius-sm);
  cursor: pointer;
  color: var(--ds-color-icon);
}
.km-date__nav:hover { background: var(--ds-color-light); color: var(--ds-color-primary); }

.km-date__grid {
  border-collapse: collapse;
  inline-size: 100%;
}
.km-date__row { display: flex; }

.km-date__weekday {
  flex: 1 1 0;
  text-align: center;
  font-size: var(--ds-font-size-caption);
  color: var(--ds-color-text-grey);
  font-weight: var(--ds-font-weight-medium);
  padding: var(--ds-space-2xs) 0;
}

.km-date__cell { flex: 1 1 0; }

.km-date__day {
  inline-size: 100%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  block-size: 32px;
  font-size: var(--ds-font-size-caption);
  background: transparent;
  border: 0;
  border-radius: var(--ds-radius-full);
  cursor: pointer;
  color: var(--ds-color-black);
  transition: background var(--ds-duration-fast) var(--ds-ease-out);
}
.km-date__day:hover { background: var(--ds-color-primary-bg); }
.km-date__day[data-selected] { background: var(--ds-color-primary); color: var(--ds-color-static-white); }
.km-date__day[data-today]:not([data-selected]) { color: var(--ds-color-primary); font-weight: var(--ds-font-weight-semibold); }
.km-date__day[data-outside-view] { color: var(--ds-color-placeholder); }
.km-date__day[data-disabled],
.km-date__day[data-unavailable] {
  color: var(--ds-color-placeholder);
  pointer-events: none;
  text-decoration: line-through;
}
.km-date__day:focus-visible { outline: 2px solid var(--ds-color-primary); outline-offset: 1px; }
</style>
