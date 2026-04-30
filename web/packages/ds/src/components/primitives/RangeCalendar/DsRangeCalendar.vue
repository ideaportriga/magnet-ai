<script setup lang="ts">
/**
 * RangeCalendar — date-range picker built on Reka UI's RangeCalendar primitive
 * backed by `@internationalized/date`.
 *
 *   <DsRangeCalendar v-model="value" />
 */

import type { RangeCalendarRootEmits, RangeCalendarRootProps } from 'reka-ui'
import { RangeCalendarRoot, useForwardPropsEmits } from 'reka-ui'
import DsRangeCalendarCell from './DsRangeCalendarCell.vue'
import DsRangeCalendarCellTrigger from './DsRangeCalendarCellTrigger.vue'
import DsRangeCalendarGrid from './DsRangeCalendarGrid.vue'
import DsRangeCalendarGridBody from './DsRangeCalendarGridBody.vue'
import DsRangeCalendarGridHead from './DsRangeCalendarGridHead.vue'
import DsRangeCalendarGridRow from './DsRangeCalendarGridRow.vue'
import DsRangeCalendarHeadCell from './DsRangeCalendarHeadCell.vue'
import DsRangeCalendarHeader from './DsRangeCalendarHeader.vue'
import DsRangeCalendarHeading from './DsRangeCalendarHeading.vue'
import DsRangeCalendarNextButton from './DsRangeCalendarNextButton.vue'
import DsRangeCalendarPrevButton from './DsRangeCalendarPrevButton.vue'

const props = defineProps<RangeCalendarRootProps>()
const emits = defineEmits<RangeCalendarRootEmits>()
const forwarded = useForwardPropsEmits(props, emits)
</script>

<template>
  <RangeCalendarRoot
    v-slot="{ grid, weekDays }"
    class="ds-range-calendar"
    data-test="ds-range-calendar"
    v-bind="forwarded"
  >
    <DsRangeCalendarHeader>
      <DsRangeCalendarHeading />
      <DsRangeCalendarPrevButton />
      <DsRangeCalendarNextButton />
    </DsRangeCalendarHeader>

    <div class="ds-range-calendar__months">
      <DsRangeCalendarGrid v-for="month in grid" :key="month.value.toString()">
        <DsRangeCalendarGridHead>
          <DsRangeCalendarGridRow>
            <DsRangeCalendarHeadCell v-for="day in weekDays" :key="day">
              {{ day }}
            </DsRangeCalendarHeadCell>
          </DsRangeCalendarGridRow>
        </DsRangeCalendarGridHead>
        <DsRangeCalendarGridBody>
          <DsRangeCalendarGridRow
            v-for="(weekDates, index) in month.rows"
            :key="`weekDate-${index}`"
            class="ds-range-calendar__week"
          >
            <DsRangeCalendarCell
              v-for="weekDate in weekDates"
              :key="weekDate.toString()"
              :date="weekDate"
            >
              <DsRangeCalendarCellTrigger :day="weekDate" :month="month.value" />
            </DsRangeCalendarCell>
          </DsRangeCalendarGridRow>
        </DsRangeCalendarGridBody>
      </DsRangeCalendarGrid>
    </div>
  </RangeCalendarRoot>
</template>

<style>
.ds-range-calendar {
  display: flex;
  flex-direction: column;
  gap: var(--ds-space-md);
  padding: var(--ds-space-md);
  background: var(--ds-color-background);
  color: var(--ds-color-black);
  border-radius: var(--ds-radius-lg);
}

.ds-range-calendar__months {
  display: flex;
  flex-direction: column;
  gap: var(--ds-space-md);
  margin-block-start: var(--ds-space-md);
}
@media (min-width: 640px) {
  .ds-range-calendar__months {
    flex-direction: row;
    gap: var(--ds-space-md);
  }
}

.ds-range-calendar__week {
  margin-block-start: var(--ds-space-xs);
  inline-size: 100%;
}
</style>
