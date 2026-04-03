<template lang="pug">
.column.q-gap-12
  .km-button-text.bb-border.q-pb-4.q-pl-sm Input parameters
  .column.q-gap-12.q-pl-sm
    .column.q-gap-6
      .km-input-label.text-text-grey Number of documents to return
      .km-heading-2 {{ span?.input.num_results }}
  .km-button-text.bb-border.q-pb-4.q-pl-sm.q-mt-lg Recalculated scores
  .col-auto.ba-border.border-radius-8(v-for='(document, index) in span?.output', style='max-width: 463px')
    .row.q-gap-12.q-pa-sm.bg-light.no-wrap.cursor-pointer(style='border-radius: 8px 8px 0 0', @click='toggleCollapse(index)')
      .row.km-body-sm {{ document?.metadata?.title ?? document?.metadata?.name }}
      q-space
      .row.no-wrap.items-center.q-gap-2
        span.km-body-sm {{ getScoreFromResult(document, 'result_1') }}
        span.km-body-lg(style='margin-bottom: 4px') +
        span.km-body-sm {{ getScoreFromResult(document, 'result_2') }}
        span.km-h1(style='margin-bottom: 2px') ⇒
        span.km-body-sm {{ formatScore(document?.score) }}
      q-icon(:name='collapsed[index] ? "expand_less" : "expand_more"', size='16px')
    .row.q-pa-sm.bt-border.km-body-sm(v-if='collapsed[index]', style='min-height: 50px; white-space: pre-wrap; word-break: break-all') {{ document?.content }}
</template>

<script>
import { ref } from 'vue'
import { m } from '@/paraglide/messages'
import { formatScore } from '@shared/utils'

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
      m,
      collapsed,
    }
  },
  methods: {
    formatScore,
    toggleCollapse(index) {
      this.collapsed[index] = !this.collapsed[index]
    },
    getScoreFromResult(document, resultName) {
      const score = this.span?.input?.[resultName]?.find((item) => item.id === document?.id)?.score
      return score ? formatScore(score) : '◯'
    },
  },
}
</script>
