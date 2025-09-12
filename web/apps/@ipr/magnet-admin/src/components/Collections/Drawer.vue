<template lang="pug">
.row.no-wrap.full-height.justify-center.q-pa-16.bg-white.fit.relative-position.bl-border(style='max-width: 500px; min-width: 500px !important')
  .column(v-if='!showChunkInfo')
    .col-auto.km-heading-7.q-mb-xs Preview
    q-separator.q-mb-md
    .col
      .column.full-height.q-pb-md.relative-position
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
            .km-description.text-secondary-text.q-mt-xs Perform semantic search for your search term. Returns best 20 results

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

<script>
import { useState } from '@shared'
import { ref } from 'vue'

export default {
  props: ['open'],
  emits: ['onLoad'],
  setup() {
    const answers = useState('semanticSearchAnswers')
    const loading = useState('semanticSearchLoading')
    const prompt = useState('semanticSearch')

    return {
      loading,
      answers,
      prompt,
      showHints: ref(true),
      showChunkInfo: ref(false),
      selectedAnswer: ref({}),
    }
  },
  computed: {
    knowledgeId() {
      return this.$store.getters.knowledge?.id || ''
    },
  },
  watch: {
    knowledgeId(newVal, oldVal) {
      if (newVal !== oldVal) {
        this.prompt = ''
      }
    },
  },
  created() {},
  mounted() {
    this.prompt = ''
  },
  methods: {
    setDetailInfo(info) {
      console.log('setDetailInfo', info)
      this.selectedAnswer = info
      this.showChunkInfo = true
    },
    clearAnswers() {
      this.$store.commit('clearSemanticSeacrhAnswers')
    },
    refine(question) {
      this.prompt = question
      this.$refs?.input.focus()
    },
    scrollTop() {
      this.$refs?.scroll?.setScrollPosition?.('vertical', 0, 200)
    },
    submit(event) {
      if (!event.shiftKey) {
        event.preventDefault()
        this.getAnswer()
      }
    },
    async getAnswer() {
      await this.$store.dispatch('getSemanticSearchAnswer')
      this.prompt = ''
      this.$refs?.input.blur()
      this.$emit('onLoad')
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
