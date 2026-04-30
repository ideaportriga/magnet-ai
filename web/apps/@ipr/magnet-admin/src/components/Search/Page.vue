<template>
  <div class="cluster full-height p-lg fit relative-position bl-border" data-wrap="no" data-justify="center">
    <div class="stack search-container">
      <div class="flex-1">
        <div class="stack full-height pb-md relative-position">
          <template v-if="uiSettings?.header_configuration?.header">
            <div class="cluster pb-md pt-md full-width text-center" data-justify="center" data-gap="xs">
              <div class="km-heading-5">{{ uiSettings?.header_configuration?.header }}</div>
            </div>
            <div v-if="uiSettings?.header_configuration?.sub_header" class="cluster pb-md full-width" data-justify="center" data-gap="xs">
              <div class="km-heading-2 text-center pb-lg">{{ uiSettings?.header_configuration?.sub_header }}</div>
            </div>
          </template>
          <search-prompt ref="prompt" class="mt-md" hide-collection-picker :t="{ placeholder: m.placeholder_typeQuestionHere() }" @on-load="scrollTop" @search-rag-execute="handleSearchRagExecute" />
          <template v-if="isShowHints">
            <div class="cluster">
              <div class="flex-1 km-heading-3">{{ m.common_youCanAskLikeThis() }}</div>
              <div class="flex-none">
                <km-btn flat tone="brand" @click="showHints = false">
                  <div class="km-button-text">{{ m.common_dontShowHints() }}</div>
                </km-btn>
              </div>
            </div>
            <template v-for="(item, index) in sampleQuestion" :key="index">
              <km-btn flat @click="refine(item)">
                <div class="wrapped-text">{{ item }}</div>
              </km-btn>
            </template>
          </template>
          <template v-if="answers.length || loading">
            <km-scroll-area ref="scroll" class="full-height flex-1">
              <div class="stack" data-gap="lg">
                <template v-if="loading">
                  <div class="cluster ba-border border-radius-12 bg-white p-lg" data-justify="center" data-gap="lg">
                    <km-loader size="62px" />
                  </div>
                </template>
                <template v-for="answer in answers" :key="answer">
                  <search-answer :answer="answer" @refine="refine" />
                </template>
              </div>
            </km-scroll-area>
          </template>
        </div>
      </div>
      <km-separator class="mb-xs" />
      <div class="flex-none">
        <div class="cluster">
          <km-btn flat simple :label="m.common_clearPreview()" icon-size="16px" icon="eraser" :disable="!answers?.length" @click="clearAnswers" />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { m } from '@/paraglide/messages'
import { storeToRefs } from 'pinia'
import { useEntityQueries } from '@/queries/entities'
import { useSearchStore } from '@/stores/searchStore'

export default {
  props: ['open'],
  setup() {
    const searchStore = useSearchStore()
    const { answers, answersLoading: loading } = storeToRefs(searchStore)
    const queries = useEntityQueries()
    const { data: ragToolsListData } = queries.rag_tools.useList()
    return {
      m,
      loading,
      answers,
      showHints: ref(true),
      ragToolsListData,
      searchStore,
    }
  },
  computed: {
    items() {
      return this.ragToolsListData?.items ?? []
    },
    defaultRag() {
      return this.items.find((el) => el.code === 'RAG_TOOL_TEST')
    },
    ragId() {
      return this.defaultRag?.id || ''
    },
    defaultRagActiveVariant() {
      return this.defaultRag?.variants?.find((el) => el.variant === this.defaultRag?.active_variant)
    },
    isShowHints() {
      return (
        this.answers?.length == 0 &&
        this.showHints &&
        this.uiSettings?.sample_questions?.enabled &&
        (!!this.uiSettings?.sample_questions?.questions?.question1 ||
          !!this.uiSettings?.sample_questions?.questions?.question2 ||
          !!this.uiSettings?.sample_questions?.questions?.question3)
      )
    },

    sampleQuestion() {
      return this.defaultRagActiveVariant?.ui_settings?.sample_questions?.questions
    },
    uiSettings() {
      return this.defaultRagActiveVariant?.ui_settings
    },
  },
  watch: {
    ragId(newVal, oldVal) {
      if (newVal !== oldVal) {
        this.clearAnswers()
      }
    },
  },
  created() {},
  mounted() {
    this.clearAnswers()
  },
  methods: {
    async handleSearchRagExecute(ragCode) {
      const systemName = this.defaultRag?.system_name
      await this.searchStore.getAnswerRagExecute(ragCode || null, systemName)
    },
    clearAnswers() {
      this.searchStore.clearAnswers()
    },
    refine(question) {
      this.$refs?.prompt?.refine(question)
    },
    scrollTop() {
      this.$refs?.scroll?.setScrollPosition?.('vertical', 0, 200)
    },
  },
}
</script>

<style scoped>
.search-container {
  min-inline-size: 450px;
  max-inline-size: 800px;
  inline-size: 100%;
}
</style>
