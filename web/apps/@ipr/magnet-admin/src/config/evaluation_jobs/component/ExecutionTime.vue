<template lang="pug">
q-chip.km-small-chip(v-if='label', :color='color', :text-color='textColor', :label='label')
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
    // Calculate the label to show the time in MM:SS format
    label() {
      const startTime = new Date(this.row?.started_at)
      const finishTime = new Date(this.row?.finished_at)

      // Calculate the difference in milliseconds
      const timeDiff = finishTime - startTime

      if (!isNaN(timeDiff) && timeDiff > 0) {
        // Convert milliseconds to seconds
        const totalSeconds = Math.floor(timeDiff / 1000)

        // Calculate minutes and seconds
        const minutes = Math.floor(totalSeconds / 60)
        const seconds = totalSeconds % 60

        // Format as MM:SS
        return `${String(minutes).padStart(2, '0')} min ${String(seconds).padStart(2, '0')} sec`
      }

      // Fallback to status label if dates are invalid
      return ''
    },

    color() {
      return 'in-progress'
    },

    textColor() {
      return 'text-gray'
    },
  },
})
</script>
