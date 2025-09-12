<template lang="pug">
.column.items-center
  q-chip.km-small-chip.chip(:color='color', :text-color='textColor', :label='label')
  .km-field.text-left {{ percentOfEvaluated }} records
</template>

<script>
import { defineComponent } from 'vue'

export default defineComponent({
  props: {
    row: {
      type: Object,
      required: true,
    },
  },
  computed: {
    percentOfEvaluated() {
      const res = this.row?.records_count ? this.row?.results_with_score / this.row?.records_count : 0
      // format to percentage
      return `${(res * 100).toFixed(0)}%`
    },
    label() {
      if (this.averageScore === 'Not rated') return 'Not rated'
      return this.averageScore.toFixed(2)
    },
    averageScore() {
      return this.row?.average_score || 'Not rated'
    },
    statusStyles() {
      if (this.averageScore > 4) {
        return { color: 'status-ready', textColor: 'status-ready-text' }
      } else if ((this.averageScore >= 3 && this.averageScore <= 4) || this.averageScore === 'Not rated') {
        return { color: 'in-progress', textColor: 'text-gray' }
      } else if (this.averageScore < 3) {
        return { color: 'error-bg', textColor: 'error-text' }
      }
      return null
    },
    color() {
      return this.statusStyles?.color || ''
    },
    textColor() {
      return this.statusStyles?.textColor || ''
    },
  },
})
</script>
