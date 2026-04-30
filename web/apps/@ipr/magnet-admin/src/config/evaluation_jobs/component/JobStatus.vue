<template>
  <km-chip class="km-small-chip" :tone="tone" :label="label" />
</template>
<script>
import { defineComponent } from 'vue'
import { statusOptions } from '@/config/evaluation_jobs/evaluation_jobs'

export default defineComponent({
  props: ['row'],

  setup() {
    return {}
  },
  computed: {
    status() {
      return this.row?.records?.[0]?.status
    },
    label() {
      const status = statusOptions.find((option) => option.value === this.status)
      return status ? status.label : this.status
    },
    tone() {
      return this.status === 'in_progress' ? 'neutral' : this.status === 'completed' ? 'success' : 'danger'
    },
  },
})
</script>
