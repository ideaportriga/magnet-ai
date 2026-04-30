<template>
  <km-drawer-layout storage-key="drawer-configuration" no-scroll>
    <template #header>
      <div v-if="!showChunkInfo" class="km-heading-7">
        <div class="cluster" data-justify="between">
          <div class="flex-1">{{ m.common_preview() }}</div>
          <div class="flex-none">
            <km-btn flat simple :label="m.common_evaluate()" icon-size="16px" icon="clipboard-check" @click="showNewDialog = true" />
          </div>
        </div>
      </div>
    </template>
    <div v-if="!showChunkInfo" class="stack full-height" data-gap="0">
      <div class="flex-1 stack" data-gap="0" style="padding-block-end: var(--ds-space-md); position: relative; padding-inline: var(--ds-space-md)">
        <template v-if="uiSettings?.header_configuration?.header">
          <div class="cluster justify-center pb-md pt-md full-width text-center" data-gap="xs">
            <div class="km-heading-5">{{ uiSettings?.header_configuration?.header }}</div>
          </div>
          <div v-if="uiSettings?.header_configuration?.sub_header" class="cluster justify-center pb-md full-width" data-gap="xs">
            <div class="km-heading-2 text-center pb-lg">{{ uiSettings?.header_configuration?.sub_header }}</div>
          </div>
        </template>
        <retrieval-metadata-filter v-if="allowMetadataFilter" v-model="metadataFilter" class="mt-md" :sources="collectionSystemNames" :collections="collectionItems" />
        <km-separator v-if="allowMetadataFilter" class="mt-md" />
        <search-prompt ref="prompt" class="mt-md" hide-collection-picker rag :search-string="searchString" :t="{ placeholder: m.placeholder_typeQuestionHere() }" @on-load="scrollTop" @search-rag="handleSearchRag" />
        <template v-if="isShowHints">
          <div class="cluster" data-justify="between">
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
                <rag-answer :answer="answer" @refine="refine" @select-answer="setDetailInfo" />
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
    <evaluation-jobs-create-new v-if="showNewDialog" :show-new-dialog="showNewDialog" :system_name="ragSystemName" type="rag_tool" :disable-rag-selection="true" @cancel="showNewDialog = false" @create="createEvaluation" />
    <km-popup-confirm :visible="showEvaluationCreateDialog" :confirm-button-label="m.common_viewEvaluation()" notification-icon="check" :cancel-button-label="m.common_cancel()" @cancel="showEvaluationCreateDialog = false" @confirm="navigateToEval()">
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
    const { draft, activeVariant, testSetItem } = useVariantEntityDetail('rag_tools')
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
    ragId() {
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
    ragSystemName() {
      return this.draft?.system_name
    },
    ragTestSetItem() {
      return this.testSetItem
    },
    allowMetadataFilter() {
      return this.activeVariant?.retrieve?.allow_metadata_filter || false
    },
    collectionSystemNames() {
      return this.activeVariant?.retrieve?.collection_system_names || []
    },
  },
  watch: {
    ragId(newVal, oldVal) {
      if (newVal !== oldVal) {
        this.clearAnswers()
      }
    },
    ragTestSetItem: {
      deep: true,
      handler(next, prev) {
        this.metadataFilter = next?.metadata_filter || []
        this.searchString = next?.user_input || ''
      },
    },
  },
  created() {},
  mounted() {
    this.clearAnswers()
    this.metadataFilter = []
  },
  beforeUnmount() {
    this.clearAnswers()
  },
  methods: {
    navigateToEval() {
      const query = {
        job_id: this.evaluationResults?.job_id,
      }
      const path = '/evaluation-jobs'
      this.$router.push({ path, query })
    },
    createEvaluation(obj) {
      this.evaluationResults = obj
      this.showNewDialog = false
      if (this.evaluationResults) this.showEvaluationCreateDialog = true
    },
    setDetailInfo(info) {
      this.selectedAnswer = info
      this.showChunkInfo = true
    },
    async handleSearchRag() {
      const variant = this.activeVariant
      const rag = this.draft
      if (variant && rag) {
        this.searchStore.searchPrompt = this.sharedPrompt || ''
        await this.searchStore.getAnswerRag(variant, rag)
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
