<template lang="pug">
q-chip.text-uppercase.q-ma-none(
  v-if='row?.[name]',
  size='sm',
) {{ row[name] }}
</template>
<script>
import { defineComponent } from 'vue'

export default defineComponent({
  props: {
    row: {
      type: Object,
      required: true,
    },
    name: {
      type: String,
      required: true,
    },
  },
})
</script>
