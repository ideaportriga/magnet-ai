<template>
  <div class="stack" data-gap="md">
    <div class="km-button-text bb-border pb-xs pl-sm">Rerank parameters</div>
    <div class="stack pl-sm" data-gap="md">
      <div class="stack" data-gap="xs">
        <div class="km-input-label text-text-grey">Query</div>
        <div class="km-heading-2">{{ span?.input.query }}</div>
      </div>
      <div class="stack" data-gap="xs">
        <div class="km-input-label text-text-grey">Number of documents to return</div>
        <div class="km-heading-2">{{ span?.model?.parameters?.top_n }}</div>
      </div>
    </div>
    <div class="km-button-text bb-border pb-xs pl-sm mt-lg">Rerank results</div>
    <div v-for="(document, index) in span.output" :key="index" class="flex-none ba-border border-radius-8" style="max-inline-size: 463px">
      <div class="cluster p-sm bg-light cursor-pointer" data-gap="md" data-wrap="no" style="border-radius: 8px 8px 0 0" @click="toggleCollapse(index)">
        <div class="cluster km-body-sm">{{ document?.metadata?.title ?? document?.metadata?.name }}</div>
        <div class="km-space" />
        <div class="cluster km-body-sm" data-wrap="no" data-gap="xs"><span class="km-body-sm">{{ formatScore(span.input?.documents?.[document.original_index]?.score) }}</span><span class="km-h1" style="margin-block-end: 2px">⇒</span><span class="km-body-sm">{{ formatScore(document?.score) }}</span></div>
        <km-glyph :name="collapsed[index] ? &quot;chevron-up&quot; : &quot;chevron-down&quot;" size="16px" />
      </div>
      <div v-if="collapsed[index]" class="cluster p-sm bt-border km-body-sm" style="min-block-size: 50px; white-space: pre-wrap; word-break: break-all">{{ document?.content }}</div>
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
  },
}
</script>
