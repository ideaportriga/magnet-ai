<template lang="pug">
.column
  .center-flex-y.km-chip.text-black(:style='{ height: "40px" }') {{ title }}
  .row-grid.q-gap-8.q-mt-8(:style='{ gridTemplateColumns: "70px 3fr 40px 3fr" }', @click='$emit("update:displayCalendar", title)')
    .center-flex-y.km-label.text-secondary-text Between
    //- INPUT FROM
    km-input.rounded-borders.ba-border.cursor-pointer(
      borderless,
      rounded,
      dense,
      readonly,
      style='width: 235px',
      iconBefore='calendar_month',
      :customClearAction='() => reset("from")',
      :model-value='!isDefaultValues.from ? inputValues.from : ""',
      :placeholder='inputValues.from'
    ) 
    .center-flex.km-label.text-secondary-text and
    //- INPUT TO
    km-input.rounded-borders.ba-border(
      borderless,
      rounded,
      dense,
      readonly,
      style='width: 235px',
      iconBefore='calendar_month',
      :customClearAction='() => reset("to")',
      :placeholder='inputValues.to',
      :model-value='!isDefaultValues.to ? inputValues.to : ""'
    )
  //- CALENDAR BOX
  .row-grid.q-gap-8.q-mt-8(:style='{ gridTemplateColumns: "70px 3fr 40px 3fr" }', v-if='displayCalendar === title')
    .range-container.rounded-borders.ba-border.q-px-6.q-py-12
      .row.q-pa-12(:style='{ gap: "40px" }')
        //-  CALENDAR FROM
        km-date(:date='from', @update:date='(val) => $emit("update:from", val)', :range='range', :options='(date) => date <= to')
        //-  CALENDAR TO
        km-date(:date='to', @update:date='(val) => $emit("update:to", val)', :range='range', :options='(date) => date >= from')
      q-separator
      .row.q-gap-8.q-mt-12
        km-chip(color='background', v-on:click='month(-1)', clickable)
          .text-secondary-text.km-chip Last month
        km-chip(color='background', v-on:click='today()', clickable)
          .text-secondary-text.km-chip Today
        km-chip(color='background', v-on:click='week()', clickable)
          .text-secondary-text.km-chip This week
        km-chip(color='background', v-on:click='month()', clickable)
          .text-secondary-text.km-chip This month
        km-chip(color='background', v-on:click='month(1)', clickable)
          .text-secondary-text.km-chip Next month
</template>
<script lnag="ts">
import { defineComponent, ref } from 'vue'
import { DateTime } from 'luxon'
import { formatDate } from '@shared'

export default defineComponent({
  props: ['title', 'from', 'to', 'displayCalendar', 'range', 'isDefaultValues', 'startValues'],
  emits: ['update:from', 'update:to', 'update:displayCalendar'],
  setup() {
    return {
      open: ref(false),
      date: ref(DateTime.now()),
    }
  },
  computed: {
    inputValues() {
      return {
        from: formatDate(this.from, 'dd.LL.yyyy'),
        to: formatDate(this.to, 'dd.LL.yyyy'),
      }
    },
  },
  methods: {
    reset(type) {
      this.$emit(`update:${type}`, this.startValues[type])
    },
    today() {
      const today = this.date
      this.$emit('update:from', today)
      this.$emit('update:to', today)
    },
    month(val = 0) {
      const month = this.date.plus({ month: val })
      this.$emit('update:from', month.startOf('month'))
      this.$emit('update:to', month.endOf('month'))
    },
    week(val = 0) {
      const week = this.date.plus({ weeks: val })
      this.$emit('update:from', week.startOf('week'))
      this.$emit('update:to', week.endOf('week'))
    },
    checkValue(field, value) {
      if (value) this.$emit(`update:${field}`, value)
    },
  },
})
</script>
<style lang="stylus">
.range-container {
  grid-column: 2 / 5;
}

.q-date {
  min-width: 224px;
  width: 224px;
}

.q-date__view {
  min-height: 213px;
  padding: 0;
}

// opacity: 0.18;
.q-date__years-item .disabled, .q-date__months-item .disabled {
  opacity: 0.18 !important;
}
</style>
