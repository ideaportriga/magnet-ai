<template>
  <div class="cluster" data-gap="xs">
    <km-chip v-for="feature in activeFeatures" :key="feature.value" class="text-uppercase m-0" size="sm">{{ feature.label }}</km-chip>
  </div>
</template>
<script>
import { defineComponent, computed } from 'vue'
import { featureOptions } from '../featureOptions.js'

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
      const active = featureOptions.filter((feature) => {
        return props.row?.[feature.value]
      })

      return active
    })

    return {
      activeFeatures,
    }
  },
})
</script>
