<template lang="pug">
search-feedback(v-model:modal='showFeedback', @onSubmit='react')
search-feedback-confirm(v-model:modal='showFeedbackConfirm')
.column.no-wrap.height-fit.search-answer-container.border-radius-12.q-pa-12.bg-white(data-test='preview-answer')
  //- QUESTION
  .col-auto
    .row.q-gap-16.no-wrap
      .q-pt-xs
        q-icon(:name='"fas fa-user"', size='20px', color='semi-transparent-primary')
      .row.stretch
        .row.stretch.q-ma-auto.no-wrap
          .search-answer-text.stretch.km-title.q-my-4.text-pre-wrap {{ answer.prompt }}

        km-btn.self-start(icon='fas fa-pen', iconColor='icon', iconSize='16px', size='sm', flat, @click='refine(answer.prompt)', tooltip='Refine')
  .col-auto
    .row.q-gap-16.no-wrap
      .q-pt-xs
        q-icon(:name='"fas fa-user"', size='20px', color='semi-transparent-primary', style='visibility: hidden')
      .row.stretch
        .row.stretch.q-ma-auto.no-wrap
          km-btn(color='primary', link, @click='showResultingPrompt = true', contentClass='q-pa-none') View resulting prompt

  //- ANSWER
  .col-auto.q-pt-md
    .row.q-gap-16.no-wrap
      .q-pt-xs
        km-icon(:name='"magnet"', width='20', height='22')
      .col.overflow-hidden
        .column.border-radius-12.q-pt-8.q-pb-8
          .row.width-100
            .search-answer-text.stretch.km-paragraph
              km-markdown(:source='mainAnswer.text')

          //- FEEDBACK /
          .row.q-gap-16.items-center(style='height: 40px')
            km-icon-btn(
              v-if='uiSettings?.user_fideback',
              :color='`${liked ? "primary" : "icon"}`',
              icon='fas fa-thumbs-up',
              iconSize='16px',
              @click='react({ like: true })',
              :disabled='hasReacted'
            )

            km-icon-btn(
              v-if='uiSettings?.user_fideback',
              :color='`${disliked ? "primary" : "icon"}`',
              icon='fas fa-thumbs-down',
              iconSize='16px',
              @click='showFeedback = true',
              :disabled='hasReacted'
            )
            .row(style='flex: 1 0 0; align-self: stretch')

            km-btn(icon='fas fa-copy', iconSize='16px', size='sm', flat, @click='copy', tooltip='Copy')

        template(v-if='mainAnswer.hasAnswers')
          .column.q-py-12.full-width.q-gap-8.bt-border.q-mt-sm
            .km-description.text-grey The answer was found using information from the following articles:

            template(v-for='(source, index) in mainAnswerSources')
              .row.q-gap-12.items-center
                .col-auto
                  q-icon(name='fas fa-video', color='secondary', v-if='source?.metadata?.type === "video"')
                  q-icon(name='fas fa-file-pdf', color='secondary', v-else-if='source?.metadata?.type === "pdf"')
                  q-icon(name='far fa-file-alt', color='secondary', v-else)
                .col
                  template(v-if='source?.metadata?.source')
                    a.km-link-title.word-break-all.cursor-pointer(@click='$emit("selectAnswer", source)') {{ true ? source?.metadata?.title || source?.metadata?.source : `Source ${index + 1}` }}

                  template(v-else)
                    .km-link-title.word-break-all.text-primary-text {{ source?.metadata?.title || 'Unknown source' }}

                .col-auto.self-start
                  km-chip.border-radius-12.text-score-relevant-text.q-py-2(
                    color='score-relevant',
                    :label='score(source.score)',
                    label-class='km-small-chip',
                    :tooltip='`Score: ${score(source.score)}`'
                  )
              template(v-if='source?.metadata?.type === "video"')
                .row.width-100.q-px-24
                  .relative-position.q-mt-sm.border-radius-12.overflow-hidden.q-mb-16(style='width: 100%; padding-bottom: 60%')
                    iframe.absolute-full(
                      width='100%',
                      height='100%',
                      frameborder='0',
                      scrolling='no',
                      allowfullscreen,
                      :src='source?.metadata?.source'
                    )
  km-popup-confirm(
    :visible='showResultingPrompt',
    title='Resulting prompt details',
    confirmButtonLabel='Copy to clipboard',
    cancelButtonLabel='Cancel',
    @confirm='copy("test")',
    @cancel='showResultingPrompt = false'
  )
    .row.justify-between.q-pt-8.q-pl-8
      .col-12.q-py-8
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Messages
        km-codemirror(v-model='resultingPromptMessages', :readonly='true', language='json')
</template>

<script lang="ts">
import { useChroma } from '@shared'
import { useState } from '@shared'
import { copyToClipboard } from 'quasar'

import { ref } from 'vue'

export default {
  props: ['answer'],
  emits: ['refine'],
  setup() {
    const prompt = useState('searchPrompt')
    const { items } = useChroma('collections')
    const showFeedback = ref(false)
    const showFeedbackConfirm = ref(false)
    return { prompt, showFeedback, showFeedbackConfirm, items, showResultingPrompt: ref(false) }
  },
  computed: {
    uiSettings() {
      return this.$store.getters.ragVariant?.ui_settings
    },
    feedback() {
      return this.answer?.feedback ?? {}
    },

    hasReacted() {
      return 'feedback' in this.answer && this.feedback?.like !== undefined
    },

    liked() {
      return this.feedback?.like === true
    },

    disliked() {
      return this.feedback?.like === false
    },

    mainAnswer() {
      return {
        id: this.answer.id,
        text: this.answer.answer,
        hasAnswers: !!this.answer.results?.length,
        // ...(!!this.answer.results?.length && this.answer.results[0])
      }
    },

    mainAnswerSources() {
      return this.answer.results ?? []
    },
    searchedIn() {
      return this.items
        .filter((item) => this.answer.collection.includes(item.id))
        .map((item) => item.name)
        .join(', ')
    },
    resultingPromptMessages() {
      return JSON.stringify(this.answer?.verbose_details?.resulting_prompt?.messages, null, 2)
    },
  },
  watch: {},
  created() {},
  mounted() {},
  methods: {
    score(text) {
      return Number.parseFloat(text).toFixed(2)
    },

    copy() {
      copyToClipboard(this.resultingPromptMessages || '')
      this.$q.notify({
        position: 'top',
        message: 'Answer has been copied to clipboard',
        color: 'positive',
        textColor: 'black',
        timeout: 1000,
      })
    },

    refine(question) {
      this.$emit('refine', question)
    },

    openURL(val) {
      window.open(val, '_blank')
    },

    async react({ like, comment = '' }) {
      this.showFeedbackConfirm = false
      const res = await this.$store.dispatch('sendFeedback', {
        id: this.answer.id,
        like,
        comment,
      })
      if (res && !like && comment) this.showFeedbackConfirm = true
    },
  },
}
</script>
<style lang="stylus" scoped>
.search-answer-container {
  min-width: 450px;
  max-width: 800px;
  width: 100%;
}

.search-answer-text {
  overflow-wrap: break-word;
  width: 1px;
}
</style>
