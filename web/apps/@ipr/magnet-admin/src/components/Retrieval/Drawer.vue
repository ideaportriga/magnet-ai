<template>
  <km-drawer-layout storage-key="drawer-retrieval" no-scroll>
    <template #header>
      <div v-if="!showChunkInfo" class="km-heading-7">{{ m.common_preview() }}</div>
    </template>
    <div v-if="!showChunkInfo" class="stack full-height" data-gap="0">
      <div class="flex-1 stack pb-md relative-position px-lg" data-gap="0">
        <template v-if="uiSettings?.header_configuration?.header">
          <div class="cluster pb-md pt-md full-width text-center" data-justify="center" data-gap="sm">
            <div class="km-heading-5">{{ uiSettings?.header_configuration?.header }}</div>
          </div>
          <div v-if="uiSettings?.header_configuration?.sub_header" class="cluster pb-md full-width" data-justify="center" data-gap="sm">
            <div class="km-heading-2 text-center pb-lg">{{ uiSettings?.header_configuration?.sub_header }}</div>
          </div>
        </template>
        <retrieval-metadata-filter v-if="allowMetadataFilter" v-model="metadataFilter" class="mt-md" :sources="collectionSystemNames" :collections="collectionItems" />
        <km-separator v-if="allowMetadataFilter" class="mt-md" />
        <retrieval-prompt ref="prompt" class="mt-md" hide-collection-picker retrieval :search-string="searchString" @on-load="scrollTop" @search-retrieval="handleSearchRetrieval" />
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
            <km-btn flat block justify="start" @click="refine(item)">
              <div class="wrapped-text">{{ item }}</div>
            </km-btn>
          </template>
        </template>
        <template v-if="answers.length">
          <km-scroll-area ref="scroll" class="full-height flex-1">
            <div class="stack" data-gap="lg">
              <template v-for="(answer, index) in answers" :key="index">
                <retrieval-answer :answer="answer" @refine="refine" @select-answer="setDetailInfo" />
              </template>
            </div>
          </km-scroll-area>
        </template>
      </div>
      <km-separator class="mb-xs" />
      <div class="flex-none px-lg">
        <div class="cluster">
          <km-btn flat simple :label="m.common_clearPreviewAction()" icon-size="16px" icon="eraser" :disable="!answers?.length" @click="clearAnswers" />
        </div>
      </div>
    </div>
    <template v-if="showChunkInfo">
      <collections-drawer-chunk :selected-row="selectedAnswer" @close="showChunkInfo = false" />
    </template>
    <km-popup-confirm :visible="showEvaluationCreateDialog" :confirm-button-label="m.common_viewEvaluation()" notification-icon="check" :cancel-button-label="m.common_cancel()" @cancel="showEvaluationCreateDialog = false" @confirm="navigate(`evaluation-jobs/${evaluationId}`)">
      <div class="cluster km-heading-7" data-justify="center">{{ m.common_evaluationStarted() }}</div>
      <div class="cluster text-center" data-justify="center">{{ m.common_evaluationTakeTime() }}</div>
      <div class="cluster text-center" data-justify="center">{{ m.common_evaluationViewResults() }}</div>
    </km-popup-confirm>
  </km-drawer-layout>
</template>

<script>
import { m } from '@/paraglide/messages'
import { ref, computed } from 'vue'
import { storeToRefs } from 'pinia'
import useState from '@shared/composables/useState'
import { useVariantEntityDetail } from '@/composables/useVariantEntityDetail'
import { useSearchStore } from '@/stores/searchStore'
import { useEntityQueries } from '@/queries/entities'

export default {
  props: ['open'],
  setup() {
    const { draft, activeVariant, testSetItem } = useVariantEntityDetail('retrieval')
    const searchStore = useSearchStore()
    const { answers, answersLoading: loading, metadataFilter } = storeToRefs(searchStore)
    const sharedPrompt = useState('searchPrompt')
    const { data: collectionsData } = useEntityQueries().collections.useList()
    const collectionItems = computed(() => collectionsData.value?.items ?? [])
    return {
      draft,
      activeVariant,
      testSetItem,
      searchStore,
      loading,
      answers,
      metadataFilter,
      sharedPrompt,
      collectionItems,
      m,
      showHints: ref(true),
      selectedAnswer: ref({}),
      showChunkInfo: ref(false),
      showNewDialog: ref(false),
      showEvaluationCreateDialog: ref(false),
      evaluationId: ref(''),
      searchString: ref(''),
    }
  },
  computed: {
    retrievalId() {
      return this.draft?.id || ''
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
      return this.activeVariant?.ui_settings?.sample_questions?.questions
    },
    uiSettings() {
      return this.activeVariant?.ui_settings
    },
    retrievalTestSetItem() {
      return this.testSetItem
    },
    retrievalCode() {
      return this.draft.system_name
    },
    allowMetadataFilter() {
      return this.activeVariant?.retrieve?.allow_metadata_filter || false
    },
    collectionSystemNames() {
      return this.activeVariant?.retrieve?.collection_system_names || []
    },
  },
  watch: {
    retrievalId(newVal, oldVal) {
      if (newVal !== oldVal) {
        this.clearAnswers()
      }
    },
    retrievalTestSetItem: {
      deep: true,
      handler(next, prev) {
        this.metadataFilter = next?.metadata_filter || []
        this.searchString = next?.user_input || ''
      },
    },
  },
  mounted() {
    this.clearAnswers()
    this.metadataFilter = []
  },
  beforeUnmount() {
    this.clearAnswers()
  },
  methods: {
    createEvaluation(obj) {
      this.evaluationId = obj?.id
      this.showNewDialog = false
      if (this.evaluationId) this.showEvaluationCreateDialog = true
    },
    navigate(path = '') {
      if (this.$route?.path !== `/${path}`) {
        this.$router?.push(`/${path}`)
      }
    },
    setDetailInfo(info) {
      this.selectedAnswer = info
      this.showChunkInfo = true
    },
    async handleSearchRetrieval() {
      const variant = this.activeVariant
      const entity = this.draft
      if (variant && entity) {
        // Sync prompt from shared UI state to searchStore before calling API
        this.searchStore.searchPrompt = this.sharedPrompt || ''
        await this.searchStore.getAnswerRetrieval(variant, entity)
      }
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
