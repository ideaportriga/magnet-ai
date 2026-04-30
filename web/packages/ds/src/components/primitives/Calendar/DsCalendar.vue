<script setup lang="ts">
/**
 * Calendar — single-date picker built on Reka UI's Calendar primitive backed
 * by `@internationalized/date`.
 *
 *   <DsCalendar v-model="value" />
 *
 * Supports `layout` for month-and-year / month-only / year-only header
 * variants; plug a custom heading via the `calendar-heading` slot.
 */

import type { CalendarRootEmits, CalendarRootProps, DateValue } from 'reka-ui'
import type { Ref } from 'vue'
import type { LayoutTypes } from './types'
import { getLocalTimeZone, today } from '@internationalized/date'
import { createReusableTemplate, useVModel } from '@vueuse/core'
import { CalendarRoot, useDateFormatter, useForwardPropsEmits } from 'reka-ui'
import { createYear, createYearRange, toDate } from 'reka-ui/date'
import { computed, toRaw } from 'vue'
import DsCalendarCell from './DsCalendarCell.vue'
import DsCalendarCellTrigger from './DsCalendarCellTrigger.vue'
import DsCalendarGrid from './DsCalendarGrid.vue'
import DsCalendarGridBody from './DsCalendarGridBody.vue'
import DsCalendarGridHead from './DsCalendarGridHead.vue'
import DsCalendarGridRow from './DsCalendarGridRow.vue'
import DsCalendarHeadCell from './DsCalendarHeadCell.vue'
import DsCalendarHeader from './DsCalendarHeader.vue'
import DsCalendarHeading from './DsCalendarHeading.vue'
import DsCalendarNextButton from './DsCalendarNextButton.vue'
import DsCalendarPrevButton from './DsCalendarPrevButton.vue'

const props = withDefaults(
  defineProps<CalendarRootProps & { layout?: LayoutTypes, yearRange?: DateValue[] }>(),
  {
    modelValue: undefined,
    layout: undefined,
  },
)
const emits = defineEmits<CalendarRootEmits>()

const placeholder = useVModel(props, 'placeholder', emits, {
  passive: true,
  defaultValue: props.defaultPlaceholder ?? today(getLocalTimeZone()),
}) as Ref<DateValue>

const formatter = useDateFormatter(props.locale ?? 'en')

const yearRange = computed(() => {
  return (
    props.yearRange
    ?? createYearRange({
      start:
        props?.minValue
        ?? (toRaw(props.placeholder) ?? props.defaultPlaceholder ?? today(getLocalTimeZone())).cycle(
          'year',
          -100,
        ),
      end:
        props?.maxValue
        ?? (toRaw(props.placeholder) ?? props.defaultPlaceholder ?? today(getLocalTimeZone())).cycle(
          'year',
          10,
        ),
    })
  )
})

const [DefineMonthTemplate, ReuseMonthTemplate] = createReusableTemplate<{ date: DateValue }>()
const [DefineYearTemplate, ReuseYearTemplate] = createReusableTemplate<{ date: DateValue }>()

const forwarded = useForwardPropsEmits(props, emits)
</script>

<template>
  <DefineMonthTemplate v-slot="{ date }">
    <select
      class="ds-calendar__select"
      :value="date.month"
      @change="(e: Event) => {
        placeholder = placeholder.set({
          month: Number((e?.target as HTMLSelectElement)?.value),
        })
      }"
    >
      <option
        v-for="month in createYear({ dateObj: date })"
        :key="month.toString()"
        :value="month.month"
        :selected="date.month === month.month"
      >
        {{ formatter.custom(toDate(month), { month: 'short' }) }}
      </option>
    </select>
  </DefineMonthTemplate>

  <DefineYearTemplate v-slot="{ date }">
    <select
      class="ds-calendar__select"
      :value="date.year"
      @change="(e: Event) => {
        placeholder = placeholder.set({
          year: Number((e?.target as HTMLSelectElement)?.value),
        })
      }"
    >
      <option
        v-for="year in yearRange"
        :key="year.toString()"
        :value="year.year"
        :selected="date.year === year.year"
      >
        {{ formatter.custom(toDate(year), { year: 'numeric' }) }}
      </option>
    </select>
  </DefineYearTemplate>

  <CalendarRoot
    v-slot="{ grid, weekDays, date }"
    v-bind="forwarded"
    v-model:placeholder="placeholder"
    class="ds-calendar"
    data-test="ds-calendar"
  >
    <DsCalendarHeader>
      <nav class="ds-calendar__nav">
        <DsCalendarPrevButton>
          <slot name="calendar-prev-icon" />
        </DsCalendarPrevButton>
        <DsCalendarNextButton>
          <slot name="calendar-next-icon" />
        </DsCalendarNextButton>
      </nav>

      <slot
        name="calendar-heading"
        :date="date"
        :month="ReuseMonthTemplate"
        :year="ReuseYearTemplate"
      >
        <template v-if="layout === 'month-and-year'">
          <div class="ds-calendar__heading-group">
            <ReuseMonthTemplate :date="date" />
            <ReuseYearTemplate :date="date" />
          </div>
        </template>
        <template v-else-if="layout === 'month-only'">
          <div class="ds-calendar__heading-group">
            <ReuseMonthTemplate :date="date" />
            {{ formatter.custom(toDate(date), { year: 'numeric' }) }}
          </div>
        </template>
        <template v-else-if="layout === 'year-only'">
          <div class="ds-calendar__heading-group">
            {{ formatter.custom(toDate(date), { month: 'short' }) }}
            <ReuseYearTemplate :date="date" />
          </div>
        </template>
        <template v-else>
          <DsCalendarHeading />
        </template>
      </slot>
    </DsCalendarHeader>

    <div class="ds-calendar__months">
      <DsCalendarGrid v-for="month in grid" :key="month.value.toString()">
        <DsCalendarGridHead>
          <DsCalendarGridRow>
            <DsCalendarHeadCell v-for="day in weekDays" :key="day">
              {{ day }}
            </DsCalendarHeadCell>
          </DsCalendarGridRow>
        </DsCalendarGridHead>
        <DsCalendarGridBody>
          <DsCalendarGridRow
            v-for="(weekDates, index) in month.rows"
            :key="`weekDate-${index}`"
            class="ds-calendar__week"
          >
            <DsCalendarCell
              v-for="weekDate in weekDates"
              :key="weekDate.toString()"
              :date="weekDate"
            >
              <DsCalendarCellTrigger :day="weekDate" :month="month.value" />
            </DsCalendarCell>
          </DsCalendarGridRow>
        </DsCalendarGridBody>
      </DsCalendarGrid>
    </div>
  </CalendarRoot>
</template>

<style>
.ds-calendar {
  display: flex;
  flex-direction: column;
  gap: var(--ds-space-md);
  padding: var(--ds-space-md);
  background: var(--ds-color-background);
  color: var(--ds-color-black);
  border-radius: var(--ds-radius-lg);
}

.ds-calendar__nav {
  position: absolute;
  inset-block-start: 0;
  inset-inline: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--ds-space-2xs);
}

.ds-calendar__heading-group {
  display: inline-flex;
  align-items: center;
  gap: var(--ds-space-2xs);
  font-size: var(--ds-font-size-label);
  font-weight: var(--ds-font-weight-medium);
}

.ds-calendar__select {
  font-family: var(--ds-font-default);
  font-size: var(--ds-font-size-sm);
  block-size: 28px;
  padding-inline: var(--ds-space-xs);
  background: var(--ds-color-control-bg);
  color: var(--ds-color-black);
  border: 1px solid var(--ds-color-control-border);
  border-radius: var(--ds-radius-sm);
  cursor: pointer;
}

.ds-calendar__months {
  display: flex;
  flex-direction: column;
  gap: var(--ds-space-md);
  margin-block-start: var(--ds-space-md);
}
@media (min-width: 640px) {
  .ds-calendar__months {
    flex-direction: row;
    gap: var(--ds-space-md);
  }
}

.ds-calendar__week {
  margin-block-start: var(--ds-space-xs);
  inline-size: 100%;
}
</style>
