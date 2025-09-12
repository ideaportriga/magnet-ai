<template lang="pug">
q-chip.km-chip(:color='color', :text-color='textColor', :label='label')
</template>

<script>
import { defineComponent } from 'vue'

export default defineComponent({
  props: {
    score: {
      required: true,
    },
  },
  computed: {
    label() {
      if (this.averageScore === 'Not rated') return 'Not rated'
      return this.averageScore.toFixed(2)
    },
    averageScore() {
      return this.score || 'Not rated'
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
