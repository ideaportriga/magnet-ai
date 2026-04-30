<template>
  <km-chip class="km-small-chip" :tone="tone" :label="label" />
</template>
<script>
import { defineComponent } from 'vue'

export default defineComponent({
  props: ['row'],

  setup() {
    return {}
  },
  computed: {
    label() {
      return this.getStatus()
    },
    tone() {
      const status = this.getStatus()

      if (status === 'In progress') {
        return 'neutral'
      } else if (status === 'Ready for eval') {
        return 'neutral'
      } else if (status === 'Eval in progress') {
        return 'brand'
      } else if (status === 'Eval completed') {
        return 'success'
      } else {
        return 'danger'
      }
    },
  },
  methods: {
    getStatus() {
      if (this.row?.status === 'in_progress') {
        return 'In progress'
      } else if (this.row?.results_with_score === 0) {
        return 'Ready for eval'
      } else if (this.row?.results_with_score > 0 && this.row?.results_with_score !== this.row?.records_count) {
        return 'Eval in progress'
      } else if (this.row?.results_with_score === this.row?.records_count) {
        return 'Eval completed'
      } else {
        return 'Error'
      }
    },
  },
})
</script>
