<template lang="pug">
km-icon-btn(icon='fas fa-download', iconSize='16px', @click.stop='getEvalutionReport')
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
  methods: {
    async getEvalutionReport() {
      let ids = []
      if (!this.row?.records?.length) {
        ids = [this.row?._id]
      } else {
        ids = this.row?.records?.map((record) => record?._id)
      }
      await this.$store.dispatch('generateEvaluationReport', { ids })
    },
  },
})
</script>
