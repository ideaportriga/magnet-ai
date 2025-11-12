<template lang="pug">
q-date(
  ref='date',
  :flat='flat',
  :minimal='minimal',
  :color='color',
  :text-color='textColor',
  first-day-of-week='1',
  :model-value='calendarValue',
  :navigation-min-year-month='scope?.min',
  :navigation-max-year-month='scope?.max',
  @update:model-value='updateModelValue($event)',
  :options='(date) => checkOptions(date)'
)
  slot
</template>
<script>
// TODO
// add startYearMonth if needed
import { DateTime } from 'luxon'
import { defineComponent } from 'vue'

export default defineComponent({
  props: {
    flat: {
      default: true,
    },
    minimal: {
      default: true,
    },
    color: {
      default: 'secondary',
    },
    textColor: {
      default: 'primary-text',
    },
    date: {
      default: DateTime.now(),
      required: true,
    },
    range: {
      default: false,
    },
    options: {
      type: Function,
      default: () => true,
    },
  },
  emits: ['update:date'],
  computed: {
    scope() {
      if (!this.range)
        return {
          min: '1000/01',
          max: '3000/01',
        }
      return {
        min: this.range?.min?.toFormat('yyyy/MM'),
        max: this.range?.max?.toFormat('yyyy/MM'),
      }
    },
    calendarValue() {
      return this.date?.toFormat('yyyy/LL/dd')
    },
  },
  methods: {
    updateModelValue(value) {
      if (value) this.$emit('update:date', DateTime.fromFormat(value, 'yyyy/LL/dd'))
    },
    checkOptions(d) {
      const date = DateTime.fromFormat(d, 'yyyy/LL/dd')
      const isInRange = this.range === false ? true : date <= this.range?.max && date >= this.range?.min
      let isOptions = this.options(date)
      return isInRange && isOptions
    },
  },
})
</script>
