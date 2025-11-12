<template lang="pug">
.row.no-wrap.full-height.justify-center.q-pa-16.bg-white.fit.relative-position.bl-border(style='max-width: 500px; min-width: 500px !important')
  .column(v-if='!showChunkInfo')
    .col-auto.km-heading-7.q-mb-xs
      .row
        .col Preview
    q-separator.q-mb-xs
    .col
      .column.full-height.q-pb-md.relative-position
        template(v-if='uiSettings?.header_configuration?.header')
          .row.justify-center.q-pb-12.q-pt-md.q-gap-2.items-center.full-width.text-center
            .km-heading-5 {{ uiSettings?.header_configuration?.header }}
          .row.justify-center.q-pb-12.q-gap-2.items-center.full-width(v-if='uiSettings?.header_configuration?.sub_header')
            .km-heading-2.text-center.q-pb-16 {{ uiSettings?.header_configuration?.sub_header }}
        retrieval-metadata-filter.q-mt-md(v-if='allowMetadataFilter', v-model='metadataFilter', :sources='collectionSystemNames')
        q-separator.q-mt-md(v-if='allowMetadataFilter')
        retrieval-prompt.q-mt-md(@onLoad='scrollTop', ref='prompt', hideCollectionPicker, retrieval, :searchString='searchString')
        template(v-if='isShowHints')
          .row.items-center
            .col.km-heading-3 You can ask like this...
            .col-auto
              km-btn(flat, color='primary', @click='showHints = false')
                .km-button-text Don’t show hints
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
                retrieval-answer(:answer='answer', @refine='refine', @selectAnswer='setDetailInfo')
    q-separator.q-mb-xs
    .col-auto
      .row.items-center
        km-btn(flat, simple, label='Clear preview', iconSize='16px', icon='fas fa-eraser', @click='clearAnswers', :disable='!answers?.length')
  template(v-if='showChunkInfo')
    collections-drawer-chunk(:selectedRow='selectedAnswer', @close='showChunkInfo = false')
  //- TODO: Add a new component for this
  km-popup-confirm(
    :visible='showEvaluationCreateDialog',
    confirmButtonLabel='View Evaluation',
    notificationIcon='far fa-circle-check',
    cancelButtonLabel='Cancel',
    @cancel='showEvaluationCreateDialog = false',
    @confirm='navigate(`evaluation-jobs/${evaluationId}`)'
  )
    .row.item-center.justify-center.km-heading-7 Evaluation has started!
    .row.text-center.justify-center It may take some time for the Evaluation to finish.
    .row.text-center.justify-center You’ll be able to view run results on the Evaluation screen.
</template>

<script>
import { useState } from '@shared'
import { ref } from 'vue'

export default {
  props: ['open'],
  setup() {
    const answers = useState('answers')
    const loading = useState('answersLoading')
    const metadataFilter = useState('metadataFilter')
    return {
      loading,
      answers,
      metadataFilter,
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
      return this.$store.getters.retrieval?.id || ''
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
      return this.$store.getters.retrievalVariant?.ui_settings?.sample_questions?.questions
    },
    uiSettings() {
      return this.$store.getters.retrievalVariant?.ui_settings
    },
    retrievalTestSetItem() {
      return this.$store.getters.retrievalTestSetItem
    },
    retrievalCode() {
      return this.$store.getters.retrieval.system_name
    },
    allowMetadataFilter() {
      return this.$store.getters.retrieval?.retrieve?.allow_metadata_filter || false
    },
    collectionSystemNames() {
      return this.$store.getters.retrieval?.retrieve?.collection_system_names || []
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
      console.log('setDetailInfo', info)
      this.selectedAnswer = info
      this.showChunkInfo = true
    },
    clearAnswers() {
      this.$store.commit('clearAnswers')
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
