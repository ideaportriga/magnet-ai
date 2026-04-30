<template>
  <km-drawer-layout storage-key="drawer-collections" no-scroll>
    <template #header>
      <div v-if="!showChunkInfo" class="km-heading-7">{{ m.common_preview() }}</div>
    </template>
    <div v-if="!showChunkInfo" class="stack full-height" data-gap="0">
      <div class="flex-1 stack pb-md relative-position px-lg" data-gap="0">
        <retrieval-metadata-filter v-model="metadataFilter" :sources="[knowledgeSystemName]" />
        <km-separator class="mt-md mb-md" />
        <div class="stack search-prompt-container border-radius-12 mb-lg full-width" data-gap="sm">
          <div>
            <km-input
              ref="input"
              class="full-width"
              data-test="preview-input"
              autogrow
              :rows="1"
              :min-rows="1"
              :max-rows="10"
              :placeholder="m.collections_searchHint()"
              :model-value="prompt"
              border-radius="8px"
              height="36px"
              type="textarea"
              @input="prompt = $event"
              @keydown.enter="submit"
            >
              <template #append>
                <km-btn
                  data-test="preview-btn"
                  type="button"
                  size="icon-xs"
                  icon="search"
                  icon-size="16px"
                  icon-tone="inverse"
                  :disable="!prompt?.length"
                  @click="getAnswer"
                />
              </template>
            </km-input>
            <div class="km-description text-secondary-text mt-xs">{{ m.collections_searchHint() }}</div>
          </div>
        </div>
        <template v-if="answers.length || loading">
          <km-scroll-area ref="scroll" class="full-height flex-1">
            <div class="stack" data-gap="lg">
              <template v-if="loading">
                <div class="cluster ba-border border-radius-12 bg-white p-lg" data-gap="lg" data-justify="center">
                  <km-loader size="62px" />
                </div>
              </template>
              <template v-for="answer in answers" :key="answer">
                <collections-answer :answer="answer" @refine="refine" @select-answer="setDetailInfo" />
              </template>
            </div>
          </km-scroll-area>
        </template>
      </div>
    </div>
    <template v-if="showChunkInfo">
      <collections-drawer-chunk :selected-row="selectedAnswer" @close="showChunkInfo = false" />
    </template>
  </km-drawer-layout>
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

<style scoped>
.search-container {
  min-inline-size: 450px;
  max-inline-size: 800px;
  inline-size: 100%;
}
</style>
