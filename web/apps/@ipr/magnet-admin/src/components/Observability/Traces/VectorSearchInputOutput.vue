<template lang="pug">
.column.q-gap-12
  .km-button-text.bb-border.q-pb-4.q-pl-sm Search parameters
  .column.q-gap-12.q-pl-sm
    .column.q-gap-6
      .km-input-label.text-text-grey Query
      .km-heading-2 {{ span?.input.query }}
    .column.q-gap-6
      .km-input-label.text-text-grey Knowledge source ID
      .km-heading-2 {{ span?.input.collection_id }}
    .column.q-gap-6
      .km-input-label.text-text-grey Number of documents to return
      .km-heading-2 {{ span?.input.num_results }}
  .km-button-text.bb-border.q-pb-4.q-pl-sm.q-mt-lg Search results
  .col-auto.ba-border.border-radius-8(v-for='(document, index) in span?.output', style='max-width: 463px')
    .row.q-gap-12.q-pa-sm.bg-light.no-wrap.cursor-pointer(style='border-radius: 8px 8px 0 0', @click='toggleCollapse(index)')
      .row(style='font-size: 13px') {{ document?.metadata?.title ?? document?.metadata?.name }}
      q-space 
      .row(style='font-size: 13px') {{ document?.score }}
      q-icon(:name='collapsed[index] ? "expand_less" : "expand_more"', size='16px')
    .row.q-pa-sm.bt-border(v-if='collapsed[index]', style='min-height: 50px; font-size: 13px; white-space: pre-wrap; word-break: break-all') {{ document?.content }}
</template>

<script>
import { ref } from 'vue'
export default {
  props: {
    span: {
      type: Object,
      default: () => null,
    },
  },
  setup() {
    const collapsed = ref([])
    return {
      collapsed,
    }
  },
  methods: {
    toggleCollapse(index) {
      this.collapsed[index] = !this.collapsed[index]
    },
  },
}
</script>
