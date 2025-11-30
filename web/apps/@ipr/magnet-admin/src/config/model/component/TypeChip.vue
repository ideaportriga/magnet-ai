<template lang="pug">
q-chip.text-uppercase.q-ma-none(v-if='row?.[name]', size='sm') {{ displayValue }}
</template>
<script>
import { defineComponent, computed } from 'vue'
import { categoryOptions } from '../model.js'

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
  setup(props) {
    const displayValue = computed(() => {
      const value = props.row[props.name]
      const option = categoryOptions.find((opt) => opt.value === value)
      return option ? option.label : value
    })

    return {
      displayValue,
    }
  },
})
</script>
