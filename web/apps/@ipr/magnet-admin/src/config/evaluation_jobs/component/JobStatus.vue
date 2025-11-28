<template lang="pug">
q-chip.km-small-chip(:color='color', :text-color='textColor', :label='label')
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
    color() {
      return this.status === 'in_progress' ? 'in-progress' : this.status === 'completed' ? 'status-ready' : 'error-bg'
    },
    textColor() {
      return this.status === 'in_progress' ? 'text-gray' : this.status === 'completed' ? 'status-ready-text' : 'error-text'
    },
  },
})
</script>
