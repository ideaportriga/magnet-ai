<template lang="pug">
.column.q-gap-12
  .km-button-text.bb-border.q-pb-4.q-pl-sm Input parameters
  .column.q-gap-12.q-pl-sm
    .column.q-gap-6
      .km-input-label.text-text-grey Score threshold
      .km-heading-2 {{ span?.input.score_threshold }}
    .column.q-gap-6
      .km-input-label.text-text-grey Number of documents to return
      .km-heading-2 {{ span?.input.num_results }}
  .km-button-text.bb-border.q-pb-4.q-pl-sm.q-mt-lg Selected results
  .col-auto.ba-border.border-radius-8(v-for='(document, index) in span?.output', style='max-width: 463px')
    .row.q-gap-12.q-pa-sm.bg-light.no-wrap.cursor-pointer(style='border-radius: 8px 8px 0 0', @click='toggleSelectedResultsCollapse(index)')
      .row(style='font-size: 13px') {{ document?.metadata?.title ?? document?.metadata?.name }}
      q-space 
      .row(style='font-size: 13px') {{ formatScore(document?.score) }}
      q-icon(:name='selectedResultsCollapsed[index] ? "expand_less" : "expand_more"', size='16px')
    .row.q-pa-sm.bt-border(
      v-if='selectedResultsCollapsed[index]',
      style='min-height: 50px; font-size: 13px; white-space: pre-wrap; word-break: break-all'
    ) {{ document?.content }}
  .km-button-text.bb-border.q-pb-4.q-pl-sm.q-mt-lg Discarded results
  .col-auto.ba-border.border-radius-8(v-for='(document, index) in discardedResults', style='max-width: 463px')
    .row.q-gap-12.q-pa-sm.bg-light.no-wrap.cursor-pointer(style='border-radius: 8px 8px 0 0', @click='toggleDiscardedResultsCollapse(index)')
      .row(style='font-size: 13px') {{ document?.metadata?.title ?? document?.metadata?.name }}
      q-space 
      .row(style='font-size: 13px') {{ formatScore(document?.score) }}
      q-icon(:name='discardedResultsCollapsed[index] ? "expand_less" : "expand_more"', size='16px')
    .row.q-pa-sm.bt-border(
      v-if='discardedResultsCollapsed[index]',
      style='min-height: 50px; font-size: 13px; white-space: pre-wrap; word-break: break-all'
    ) {{ document?.content }}
</template>

<script>
import { ref } from 'vue'
import { formatScore } from '@shared/utils'

export default {
  props: {
    span: {
      type: Object,
      default: () => null,
    },
  },
  setup() {
    return {
      selectedResultsCollapsed: ref([]),
      discardedResultsCollapsed: ref([]),
    }
  },
  computed: {
    discardedResults() {
      return this.span?.input?.documents?.filter((document) => !this.span?.output?.find((result) => result.id === document.id))
    },
  },
  methods: {
    formatScore,
    toggleSelectedResultsCollapse(index) {
      this.selectedResultsCollapsed[index] = !this.selectedResultsCollapsed[index]
    },
    toggleDiscardedResultsCollapse(index) {
      this.discardedResultsCollapsed[index] = !this.discardedResultsCollapsed[index]
    },
  },
}
</script>
