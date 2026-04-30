<template>
  <div class="stack items-center" data-gap="0">
    <km-chip class="km-small-chip chip" :tone="tone" :label="label" />
    <div class="km-field text-left">{{ percentOfEvaluated }} records</div>
  </div>
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
    tone() {
      if (this.averageScore > 4) {
        return 'success'
      } else if ((this.averageScore >= 3 && this.averageScore <= 4) || this.averageScore === 'Not rated') {
        return 'neutral'
      } else if (this.averageScore < 3) {
        return 'danger'
      }
      return undefined
    },
  },
})
</script>
