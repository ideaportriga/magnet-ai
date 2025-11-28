<template lang="pug">
.km-field.text-left {{ test_set }}
</template>
<script>
import { defineComponent } from 'vue'
import { typeOptions } from '@/config/evaluation_sets/evaluation_sets'

export default defineComponent({
  props: ['row'],

  setup() {
    return {
      typeOptions,
    }
  },
  computed: {
    test_set() {
      return this.row?.test_sets?.[0]
    },
    records() {
      return `${this.row?.records_count} records`
    },
  },
})
</script>
