<template lang="pug">
km-drawer-layout(storageKey="drawer-collections", noScroll)
  template(#header)
    .km-heading-7(v-if='!showChunkInfo') {{ m.common_preview() }}
  .column.full-height(v-if='!showChunkInfo')
    .col.column.no-wrap.q-pb-md.relative-position.q-px-16
      retrieval-metadata-filter(v-model='metadataFilter', :sources='[knowledgeSystemName]')
      q-separator.q-mt-md.q-mb-md
      .column.search-prompt-container.border-radius-12.q-mb-16.full-width.q-gap-8
        .row
          km-input.full-width(
            ref='input',
            autogrow,
            border-radius='8px',
            height='36px',
            :model-value='prompt',
            @input='prompt = $event',
            @keydown.enter='submit'
          )
            template(#append='{ height }')
              .self-end.center-flex(:style='{ height }')
                q-btn.border-radius-6(color='primary', @click='getAnswer', unelevated, padding='6px 7px')
                  template(v-slot:default)
                    q-icon(name='fas fa-search', size='16px')
          .km-description.text-secondary-text.q-mt-xs {{ m.collections_searchHint() }}

      template(v-if='answers.length || loading')
        q-scroll-area.full-height.col(ref='scroll')
          .column.q-gap-16
            template(v-if='loading')
              .row.justify-center.ba-border.border-radius-12.bg-white.q-pa-16.q-gap-16
                q-spinner-dots(size='62px', color='primary')
            template(v-for='answer in answers')
              collections-answer(:answer='answer', @refine='refine', @selectAnswer='setDetailInfo')

  template(v-if='showChunkInfo')
    collections-drawer-chunk(:selectedRow='selectedAnswer', @close='showChunkInfo = false')
</template>

<script setup>
import { fetchData } from '@shared'
import { m } from '@/paraglide/messages'
import { ref, computed, watch, onMounted, useTemplateRef } from 'vue'
import { storeToRefs } from 'pinia'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { useAppStore } from '@/stores/appStore'
import { useSearchStore } from '@/stores/searchStore'

const emit = defineEmits(['onLoad'])

const { draft } = useEntityDetail('collections')
const appStore = useAppStore()
const searchStore = useSearchStore()
const {
  semanticSearchAnswers: answers,
  semanticSearchLoading: loading,
  semanticSearch: prompt,
  metadataFilter,
} = storeToRefs(searchStore)

const inputRef = useTemplateRef('input')
const scrollRef = useTemplateRef('scroll')

const showHints = ref(true)
const showChunkInfo = ref(false)
const selectedAnswer = ref({})

function clearSemanticSearchAnswers() {
  answers.value = []
}

const knowledgeId = computed(() => draft.value?.id || '')
const knowledgeSystemName = computed(() => draft.value?.system_name || '')

watch(knowledgeId, (newVal, oldVal) => {
  if (newVal !== oldVal) {
    prompt.value = ''
    metadataFilter.value = []
  }
})

onMounted(() => {
  prompt.value = ''
  metadataFilter.value = []
})

function setDetailInfo(info) {
  selectedAnswer.value = info
  showChunkInfo.value = true
}

function clearAnswers() {
  clearSemanticSearchAnswers()
}

function refine(question) {
  prompt.value = question
  inputRef.value?.focus()
}

function scrollTop() {
  scrollRef.value?.setScrollPosition?.('vertical', 0, 200)
}

function submit(event) {
  if (!event.shiftKey) {
    event.preventDefault()
    getAnswer()
  }
}

async function getAnswer() {
  const { convertFiltersToFilterObject } = await import('@shared')
  const promptVal = prompt.value
  const metadataFilterVal = convertFiltersToFilterObject(metadataFilter.value)
  const collection_id = draft.value?.system_name
  const collection_display_name = draft.value?.name
  const endpoint = appStore.config?.documentSemanticSearch?.endpoint
  const service = `${appStore.config?.documentSemanticSearch?.service}` || ''
  const credentials = appStore.config?.documentSemanticSearch?.credentials

  loading.value = true
  const response = await fetchData({
    method: 'POST',
    endpoint,
    service,
    credentials,
    body: JSON.stringify({
      collection_id,
      collection_display_name,
      user_message: promptVal,
      metadata_filter: metadataFilterVal,
    }),
    headers: { 'Content-Type': 'application/json' },
  })
  loading.value = false

  if (!response?.error) {
    const answer = await response.json()
    answers.value = [{ prompt: promptVal, collection: collection_id, ...answer }, ...answers.value]
  }

  prompt.value = ''
  inputRef.value?.blur()
  emit('onLoad')
}
</script>

<style lang="stylus" scoped>
.search-container {
  min-width: 450px;
  max-width: 800px;
  width: 100%;
}
</style>
