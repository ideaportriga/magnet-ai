<template lang="pug">
.km-title.text-lef.ellipsis {{ typeLabel }}
.km-field.text-left.ellipsis {{ description }}
</template>

<script>
import { defineComponent, computed } from 'vue'
import { jobTypeOptions } from '../jobs.js'

export default defineComponent({
  props: {
    row: {
      type: Object,
      required: true,
    },
  },
  setup(props) {
    const typeLabel = computed(() => {
      const typeValue = props.row?.definition?.run_configuration?.type
      return jobTypeOptions.find((el) => el.value === typeValue)?.label || typeValue
    })

    const description = computed(() => {
      const params = props.row?.definition?.run_configuration?.params
      if (!params) return props.row?.definition?.run_configuration?.params?.system_name

      const type = props.row?.definition?.run_configuration?.type

      // For evaluation jobs, show eval type + test set names
      if (type === 'evaluation') {
        const parts = []
        if (params.type) parts.push(params.type)
        const testSets = params.config
          ?.flatMap((c) => c.test_set_system_names || [])
          ?.join(', ')
        if (testSets) parts.push(testSets)
        return parts.join(' · ') || params.system_name || '—'
      }

      // For cleanup_logs, show retention days
      if (type === 'cleanup_logs') {
        const days = params.retention_days
        return days ? `Retention: ${days} days` : params.system_name || '—'
      }

      // Default: show system_name
      return params.system_name || '—'
    })

    return { typeLabel, description }
  },
})
</script>

<style scoped>
.km-title,
.km-field {
  max-width: 300px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
