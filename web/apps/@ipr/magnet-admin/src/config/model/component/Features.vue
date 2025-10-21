<template lang="pug">
.row.q-gap-4.no-wrap
  q-chip.text-uppercase.q-ma-none(
    v-for='feature in activeFeatures',
    :key='feature.value',
    size='sm'
  ) {{ feature.label }}
</template>
<script>
import { defineComponent, computed } from 'vue'
import { featureOptions } from '../model.js'

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
    const activeFeatures = computed(() => {

      const active = featureOptions.filter(feature => {
    
        return props.row?.[feature.value]
      })
  
      return active
    })

    return {
      activeFeatures
    }
  }
})
</script>
