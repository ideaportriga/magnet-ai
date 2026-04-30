<template>
  <km-chip v-if="row?.[name]" class="text-uppercase m-0" size="sm">{{ displayValue }}</km-chip>
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
