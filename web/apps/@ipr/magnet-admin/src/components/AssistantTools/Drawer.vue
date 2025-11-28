<template lang="pug">
.row.no-wrap.full-height.justify-center.q-pa-16.bg-white.fit.relative-position.bl-border(style='max-width: 500px; min-width: 500px !important')
  .column(v-if='!showChunkInfo')
    .col-auto.km-heading-7.q-mb-xs
      .row
        .col Assistant tool definition
    q-separator.q-mb-xs
    .col.full-width.scroll-container(style='max-height: calc(100vh - 100px); overflow-y: auto')
      km-codemirror(:modelValue='definition', :readonly='true', language='json')
</template>

<script>
import { useState } from '@shared'
import { ref } from 'vue'

export default {
  props: ['open'],
  setup() {
    const answers = useState('answers')
    const loading = useState('answersLoading')
    return {
      loading,
      answers,
      showHints: ref(true),
      selectedAnswer: ref({}),
      showChunkInfo: ref(false),
      showNewDialog: ref(false),
      showEvaluationCreateDialog: ref(false),
      evaluationId: ref(''),
    }
  },
  computed: {
    definition: {
      get() {
        return JSON.stringify(this.$store.getters.assistant_tool?.definition, null, 2) || ''
      },
    },
  },
  watch: {},
  mounted() {},
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
