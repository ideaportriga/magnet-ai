<template lang="pug">
.row.no-wrap.full-height.justify-center.q-pa-16.fit.relative-position
  .column.search-container
    //prompt
    .bg-user-input-bg.q-px-16
      search-prompt.q-mt-md(@onLoad='scrollTop', ref='prompt', hideCollectionPicker, :rag_code='rag_code')
    //hints
    template(v-if='isShowHints')
      .row.items-center.q-mt-16.q-mb-8
        .col.km-heading-3 You can ask like this...
        .col-auto
          km-btn(flat, color='primary', @click='showHints = false')
            .km-button-text Don’t show hints

      template(v-if='$theme === "default"')
        template(v-for='(item, index) in sampleQuestion', :key='index')
          km-btn(flat, @click='refine(item)')
            .wrapped-text {{ item }}
      template(v-else)
        template(v-for='(item, index) in sampleQuestion', :key='index')
          .flex
            km-btn.hint(bg='transparent', color='primary', @click='refine(item)')
              .wrapped-text {{ item }}
    //answers
    template(v-if='answers.length || loading')
      q-scroll-area.full-height.col(ref='scroll')
        .column.q-gap-16.q-mt-md
          template(v-if='loading')
            .row.justify-center.border-radius-12.bg-white.q-pa-16.q-gap-16
              q-spinner-dots(size='62px', color='primary')
          .column.q-gap-16
            template(v-for='(answer, index) in answers', :key='index')
              search-answer(:answer='answer', @refine='refine', :uiSettings='uiSettings', :isLastMessage='index == 0')
</template>

<script>
import { ref } from 'vue'
import { useSearch, useAiApps } from '@/pinia'
import { storeToRefs } from 'pinia'
export default {
  props: {
    index: Number,
    open: Boolean,
    // eslint-disable-next-line vue/prop-name-casing
    rag_code: {
      type: String,
      default: '',
    },
  },
  setup() {
    const searchStore = useSearch()

    const { answers: storeAnswers, answersLoading: loading } = storeToRefs(searchStore)
    const aiAppsStore = useAiApps()
    const { app, displayTab } = storeToRefs(aiAppsStore)

    return {
      loading,
      storeAnswers,
      showHints: ref(true),
      searchStore,
      app,
      displayTab,
    }
  },
  computed: {
    answers() {
      return this.storeAnswers
    },
    allAnswers() {
      return [...this.answers].reverse()
    },
    panel() {
      return this.displayTab
    },
    tool() {
      return this.panel?.entityObject
    },
    systemName() {
      return this.tool?.system_name || ''
    },
    uiSettings() {
      return this.defaultRagActiveVariant?.ui_settings
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
    defaultRagActiveVariant() {
      return this.tool?.active_variant
    },
    sampleQuestion() {
      return this.defaultRagActiveVariant?.ui_settings?.sample_questions?.questions
    },
  },
  watch: {
    systemName(newVal, oldVal) {
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
    clearAnswers() {
      this.answers = []
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
@media (max-width: 500px)
  .search-container
    min-width: unset
    max-width: unset
</style>
