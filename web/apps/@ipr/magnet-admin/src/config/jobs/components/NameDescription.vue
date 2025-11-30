<template lang="pug">
.km-title.text-lef.ellipsis {{ typeLabel }}
.km-field.text-left.ellipsis {{ row?.definition?.run_configuration?.params?.system_name }}
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

    return { typeLabel }
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
