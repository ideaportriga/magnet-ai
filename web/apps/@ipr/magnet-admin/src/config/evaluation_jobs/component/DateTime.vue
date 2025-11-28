<template lang="pug">
.km-button-xs-text {{ dateTimeLabel.date }}
.km-button-xs-text {{ dateTimeLabel.time }}
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
    dateTimeLabel() {
      const startTime = this.row?.started_at ? new Date(this.row.started_at) : null

      const locale = navigator.language || 'en-US'

      return {
        date: startTime.toLocaleDateString(locale),
        time: startTime.toLocaleTimeString(locale),
      }
    },
  },
})
</script>
