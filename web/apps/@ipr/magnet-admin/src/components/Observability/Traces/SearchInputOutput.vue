<template>
  <div class="stack" data-gap="md">
    <div class="km-button-text bb-border pb-xs pl-sm">Search parameters</div>
    <div class="stack pl-sm" data-gap="md">
      <div class="stack" data-gap="xs">
        <div class="km-input-label text-text-grey">Query</div>
        <div class="km-heading-2">{{ span?.input.query }}</div>
      </div>
      <div v-if="metadataFilter" class="stack" data-gap="xs">
        <div class="km-input-label text-text-grey">Metadata filter</div>
        <div class="km-heading-2">{{ metadataFilter }}</div>
      </div>
      <div v-if="span?.input.collection_id" class="stack" data-gap="xs">
        <div class="km-input-label text-text-grey">Knowledge source ID</div>
        <div class="km-heading-2">{{ span?.input.collection_id }}</div>
      </div>
      <div v-if="span?.input.collection_name" class="stack" data-gap="xs">
        <div class="km-input-label text-text-grey">Knowledge source name</div>
        <div class="km-heading-2">{{ span?.input.collection_name }}</div>
      </div>
      <div v-if="span?.input.num_results" class="stack" data-gap="xs">
        <div class="km-input-label text-text-grey">Number of documents to return</div>
        <div class="km-heading-2">{{ span?.input.num_results }}</div>
      </div>
      <div v-if="span?.input.score_threshold" class="stack" data-gap="xs">
        <div class="km-input-label text-text-grey">Score threshold</div>
        <div class="km-heading-2">{{ span?.input.score_threshold }}</div>
      </div>
    </div>
    <div class="km-button-text bb-border pb-xs pl-sm mt-lg">Search results</div>
    <template v-if="Array.isArray(span?.output)">
      <div v-for="(document, index) in span?.output" :key="index" class="flex-none ba-border border-radius-8 search-result-card">
        <div class="cluster p-sm bg-light cursor-pointer search-result-header" data-gap="md" data-wrap="no" @click="toggleCollapse(index)">
          <div class="km-body-sm">
            {{ document?.metadata?.title ?? document?.metadata?.name ?? document?.title }}
          </div>
          <div class="km-space" />
          <div class="km-body-sm">
            {{ formatScore(document?.score) }}
          </div>
          <km-glyph v-if="document?.content" :name="collapsed[index] ? 'chevron-up' : 'chevron-down'" size="16px" />
        </div>
        <div
          v-if="collapsed[index] && document?.content"
          class="p-sm bt-border km-body-sm search-result-content"
        >
          {{ document?.content }}
        </div>
      </div>
    </template>
    <template v-if="typeof span?.output?.count === 'number'">
      <div class="stack pl-sm" data-gap="xs">
        <div class="km-input-label text-text-grey">Records found</div>
        <div class="km-heading-2">
          {{ span.output.count }}
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { formatScore } from '@shared/utils'
import { m } from '@/paraglide/messages'
import { computed, ref } from 'vue'

const props = defineProps<{
  span: any
}>()

const metadataFilter = computed(() => {
  return JSON.stringify(props.span?.input.filter, null, 2)
})

const collapsed = ref([])

const toggleCollapse = (index: string | number) => {
  collapsed.value[index] = !collapsed.value[index]
}
</script>

<style scoped>
.search-result-card {
  max-inline-size: 463px;
}
.search-result-header {
  border-radius: var(--ds-radius-lg) var(--ds-radius-lg) 0 0;
}
.search-result-content {
  min-block-size: 50px;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
