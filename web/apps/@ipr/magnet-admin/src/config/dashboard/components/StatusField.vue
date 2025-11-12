<template lang="pug">
q-chip.km-small-chip(:color='color', :text-color='textColor', :label='row?.status', style='text-transform: uppercase')
  q-tooltip(v-if='row?.status_message', :offset='[0, 10]')
    .row.items-center
      .col-auto.q-mr-sm
        .km-field {{ row?.status_message }}
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
    color() {
      switch (this.row?.status) {
        case 'success':
          return 'status-ready'
        case 'error':
          return 'error-bg'
        default:
          return 'gray'
      }
    },
    textColor() {
      switch (this.row?.status) {
        case 'success':
          return 'status-ready-text'
        case 'error':
          return 'error-text'
        default:
          return 'text-gray'
      }
    },
  },
})
</script>
