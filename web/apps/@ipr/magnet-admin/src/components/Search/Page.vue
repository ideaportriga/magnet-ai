<template lang="pug">
.row.no-wrap.full-height.justify-center.q-pa-16.fit.relative-position.bl-border
  .column.search-container
    .col
      .column.full-height.q-pb-md.relative-position
        template(v-if='uiSettings?.header_configuration?.header')
          .row.justify-center.q-pb-12.q-pt-md.q-gap-2.items-center.full-width.text-center
            .km-heading-5 {{ uiSettings?.header_configuration?.header }}
          .row.justify-center.q-pb-12.q-gap-2.items-center.full-width(v-if='uiSettings?.header_configuration?.sub_header')
            .km-heading-2.text-center.q-pb-16 {{ uiSettings?.header_configuration?.sub_header }}
        search-prompt.q-mt-md(@onLoad='scrollTop', ref='prompt', hideCollectionPicker, @searchRagExecute='handleSearchRagExecute')
        template(v-if='isShowHints')
          .row.items-center
            .col.km-heading-3 You can ask like this...
            .col-auto
              km-btn(flat, color='primary', @click='showHints = false')
                .km-button-text Don't show hints
          template(v-for='(item, index) in sampleQuestion', :key='index')
            km-btn(flat, @click='refine(item)')
              .wrapped-text {{ item }}
        template(v-if='answers.length || loading')
          q-scroll-area.full-height.col(ref='scroll')
            .column.q-gap-16
              template(v-if='loading')
                .row.justify-center.ba-border.border-radius-12.bg-white.q-pa-16.q-gap-16
                  q-spinner-dots(size='62px', color='primary')
              template(v-for='answer in answers')
                search-answer(:answer='answer', @refine='refine')
    q-separator.q-mb-xs
    .col-auto
      .row.items-center
        km-btn(flat, simple, :label='m.common_clearPreview()', iconSize='16px', icon='fas fa-eraser', @click='clearAnswers', :disable='!answers?.length')
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

<style lang="stylus" scoped>
.search-container {
  min-width: 450px;
  max-width: 800px;
  width: 100%;
}
</style>
