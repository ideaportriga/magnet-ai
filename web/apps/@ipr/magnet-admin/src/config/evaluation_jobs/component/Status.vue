<template lang="pug">
q-chip.km-small-chip(:color='color', :text-color='textColor', :label='label')
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
    color() {
      const status = this.getStatus()

      if (status === 'In progress') {
        return 'in-progress'
      } else if (status === 'Ready for eval') {
        return 'in-progress'
      } else if (status === 'Eval in progress') {
        return 'primary-light'
      } else if (status === 'Eval completed') {
        return 'status-ready'
      } else {
        return 'error-bg'
      }
    },
    textColor() {
      const status = this.getStatus()
      if (status === 'In progress') {
        return 'text-gray'
      } else if (status === 'Ready for eval') {
        return 'text-gray'
      } else if (status === 'Eval in progress') {
        return 'primary'
      } else if (status === 'Eval completed') {
        return 'status-ready-text'
      } else {
        return 'error-text'
      }

      // if (this.row?.status === 'in_progress') {
      //   return 'text-gray'
      // } else if (this.row?.results_with_score === 0) {
      //   return 'status-ready-text'
      // } else if (this.row?.results_with_score > 0 && this.row?.results_with_score !== this.row?.records_count) {
      //   return 'text-gray'
      // } else if (this.row?.results_with_score === this.row?.records_count) {
      //   return 'status-ready-text'
      // } else {
      //   return 'error-text'
      // }
      // return this.row?.status === 'in_progress' ? 'text-gray' : this.row?.status === 'completed' ? 'status-ready-text' : 'error-text'
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
