<template>
  <div class="column q-gap-12">
    <div class="km-button-text bb-border q-pb-4 q-pl-sm">Search parameters</div>
    <div class="column q-gap-12 q-pl-sm">
      <div class="column q-gap-6">
        <div class="km-input-label text-text-grey">Query</div>
        <div class="km-heading-2">{{ span?.input.query }}</div>
      </div>
      <div v-if="metadataFilter" class="column q-gap-6">
        <div class="km-input-label text-text-grey">Metadata filter</div>
        <div class="km-heading-2">{{ metadataFilter }}</div>
      </div>
      <div v-if="span?.input.collection_id" class="column q-gap-6">
        <div class="km-input-label text-text-grey">Knowledge source ID</div>
        <div class="km-heading-2">{{ span?.input.collection_id }}</div>
      </div>
      <div v-if="span?.input.collection_name" class="column q-gap-6">
        <div class="km-input-label text-text-grey">Knowledge source name</div>
        <div class="km-heading-2">{{ span?.input.collection_name }}</div>
      </div>
      <div v-if="span?.input.num_results" class="column q-gap-6">
        <div class="km-input-label text-text-grey">Number of documents to return</div>
        <div class="km-heading-2">{{ span?.input.num_results }}</div>
      </div>
      <div v-if="span?.input.score_threshold" class="column q-gap-6">
        <div class="km-input-label text-text-grey">Score threshold</div>
        <div class="km-heading-2">{{ span?.input.score_threshold }}</div>
      </div>
    </div>
    <div class="km-button-text bb-border q-pb-4 q-pl-sm q-mt-lg">Search results</div>
    <div v-for="(document, index) in span?.output" :key="index" class="col-auto ba-border border-radius-8" style="max-width: 463px">
      <div class="row q-gap-12 q-pa-sm bg-light no-wrap cursor-pointer" style="border-radius: 8px 8px 0 0" @click="toggleCollapse(index)">
        <div class="row" style="font-size: 13px">
          {{ document?.metadata?.title ?? document?.metadata?.name ?? document?.title }}
        </div>
        <q-space />
        <div class="row" style="font-size: 13px">
          {{ formatScore(document?.score) }}
        </div>
        <q-icon v-if="document?.content" :name="collapsed[index] ? 'expand_less' : 'expand_more'" size="16px" />
      </div>
      <div
        v-if="collapsed[index] && document?.content"
        class="row q-pa-sm bt-border"
        style="min-height: 50px; font-size: 13px; white-space: pre-wrap; word-break: break-all"
      >
        {{ document?.content }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { formatScore } from '@shared/utils'
import { computed, ref } from 'vue'

const props = defineProps<{
  span: any
}>()

const metadataFilter = computed(() => {
  return JSON.stringify(props.span?.input.filter, null, 2)
})

const collapsed = ref([])

const toggleCollapse = (index: number) => {
  collapsed.value[index] = !collapsed.value[index]
}
</script>
