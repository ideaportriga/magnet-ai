<template>
  <div class="stack" data-gap="md">
    <div class="km-button-text bb-border pb-xs pl-sm">Input parameters</div>
    <div class="stack pl-sm" data-gap="md">
      <div class="stack" data-gap="xs">
        <div class="km-input-label text-text-grey">Score threshold</div>
        <div class="km-heading-2">{{ span?.input.score_threshold }}</div>
      </div>
      <div class="stack" data-gap="xs">
        <div class="km-input-label text-text-grey">Number of documents to return</div>
        <div class="km-heading-2">{{ span?.input.num_results }}</div>
      </div>
    </div>
    <div class="km-button-text bb-border pb-xs pl-sm mt-lg">Selected results</div>
    <div v-for="(document, index) in span?.output" :key="index" class="flex-none ba-border border-radius-8" style="max-inline-size: 463px">
      <div class="cluster p-sm bg-light cursor-pointer" style="border-radius: 8px 8px 0 0" data-gap="md" data-wrap="no" @click="toggleSelectedResultsCollapse(index)">
        <div class="km-body-sm">{{ document?.metadata?.title ?? document?.metadata?.name }}</div>
        <div class="km-space" />
        <div class="km-body-sm">{{ formatScore(document?.score) }}</div>
        <km-glyph :name="selectedResultsCollapsed[index] ? &quot;chevron-up&quot; : &quot;chevron-down&quot;" size="16px" />
      </div>
      <div v-if="selectedResultsCollapsed[index]" class="p-sm bt-border km-body-sm" style="min-block-size: 50px; white-space: pre-wrap; word-break: break-all">{{ document?.content }}</div>
    </div>
    <div class="km-button-text bb-border pb-xs pl-sm mt-lg">Discarded results</div>
    <div v-for="(document, index) in discardedResults" :key="index" class="flex-none ba-border border-radius-8" style="max-inline-size: 463px">
      <div class="cluster p-sm bg-light cursor-pointer" style="border-radius: 8px 8px 0 0" data-gap="md" data-wrap="no" @click="toggleDiscardedResultsCollapse(index)">
        <div class="km-body-sm">{{ document?.metadata?.title ?? document?.metadata?.name }}</div>
        <div class="km-space" />
        <div class="km-body-sm">{{ formatScore(document?.score) }}</div>
        <km-glyph :name="discardedResultsCollapsed[index] ? &quot;chevron-up&quot; : &quot;chevron-down&quot;" size="16px" />
      </div>
      <div v-if="discardedResultsCollapsed[index]" class="p-sm bt-border km-body-sm" style="min-block-size: 50px; white-space: pre-wrap; word-break: break-all">{{ document?.content }}</div>
    </div>
  </div>
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
    return {
      m,
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
