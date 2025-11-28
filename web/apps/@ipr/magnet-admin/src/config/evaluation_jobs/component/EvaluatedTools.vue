<template lang="pug">
pre.cursor-pointer.wrapped-text.km-heading-1 {{ tool }}
  q-tooltip(:offset='[0, 10]')
    .row.items-center(v-if='row?.tool?.system_name')
      .col-auto.q-mr-sm
        .km-field System name:
      .col-auto
        .km-heading-1 {{ row?.tool?.system_name }}
    .row.items-center.q-mt-xs(v-if='row?.tool?.description')
      .col-auto.q-mr-sm
        .km-field Description:
      .col-auto
        .km-heading-1 {{ row?.tool?.description }}
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
  computed: {
    tool() {
      console.log(this.row)
      return this.row?.tool.name || ''
    },
  },
})
</script>

<style scoped>
.wrapped-text {
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
