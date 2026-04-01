<template lang="pug">
div
  .km-title.text-left.ellipsis {{ row?.name }}
  q-chip.km-small-chip(color='in-progress', text-color='text-gray', :label='row?.system_name')
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
})
</script>
