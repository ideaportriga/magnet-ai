<template lang="pug">
search-feedback(v-model:modal='showFeedback', @onSubmit='react')
search-feedback-confirm(v-model:modal='showFeedbackConfirm')
.column.no-wrap.height-fit.search-answer-container.border-radius-12.q-pa-12.bg-white
  //- QUESTION
  .col-auto
    .row.q-gap-16.no-wrap
      .q-pt-xs
        q-icon(:name='"fas fa-user"', size='20px', color='semi-transparent-primary')
      .row.stretch
        .row.stretch.q-ma-auto.no-wrap
          .search-answer-text.stretch.km-title.q-my-4.text-pre-wrap {{ answer.prompt }}

        km-btn.self-start(icon='fas fa-pen', iconColor='icon', iconSize='16px', size='sm', flat, @click='refine(answer.prompt)', tooltip='Refine')
  //- ANSWER
  .col-auto.q-pt-md
    .row.q-gap-16.no-wrap
      .q-pt-xs
        km-icon(:name='"magnet"', width='20', height='22')
      .col.overflow-hidden
        template(v-if='mainAnswer.hasAnswers')
          .column.full-width.q-gap-8.q-mt-sm
            template(v-for='(source, index) in mainAnswerSources')
              .row.q-gap-12.items-center
                .col-auto.self-start
                  q-icon(name='fas fa-video', color='secondary', v-if='source?.metadata?.type === "video"')
                  q-icon(name='fas fa-file-pdf', color='secondary', v-else-if='source?.metadata?.type === "pdf"')
                  q-icon(name='far fa-file-alt', color='secondary', v-else)
                .col
                  a.km-link-title.word-break-all.cursor-pointer(@click='$emit("selectAnswer", source)') {{ `${source?.metadata?.title} ${source?.metadata?.pageNumber || source?.metadata?.page ? ` | ${source?.metadata?.pageNumber || source?.metadata?.page} ` : ''}` }}
                    .km-field.text-secondary-text.q-py-xs.clamp-text {{ source?.content }}

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
</template>

<script lang="ts">
import { useChroma } from '@shared'
import { useState } from '@shared'
import { copyToClipboard } from 'quasar'

import { ref } from 'vue'

export default {
  props: ['answer'],
  emits: ['refine', 'selectAnswer'],
  setup() {
    const prompt = useState('searchPrompt')
    const { items } = useChroma('collections')
    const showFeedback = ref(false)
    const showFeedbackConfirm = ref(false)
    return { prompt, showFeedback, showFeedbackConfirm, items }
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
      }
    },
    mainAnswerSources() {
      return this.answer.results ?? []
    },
    searchedIn() {
      //answer.collection
      return this.items
        .filter((item) => this.answer.collection.includes(item.id))
        .map((item) => item.name)
        .join(', ')
    },
  },
  watch: {},
  created() {},
  mounted() {},
  methods: {
    openCollection() {},
    score(text) {
      return Number.parseFloat(text).toFixed(2)
    },

    copy() {
      copyToClipboard(this.mainAnswer.text || '')
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

.custom-link {
  transition: background-color 0.3s, transform 0.3s;
  cursor: pointer;
}

.custom-link:hover {
  // background-color: #3700b3; /* Darker shade for hover effect */
  transform: scale(1.02);
  text-decoration: underline
}

.clamp-text {
  display: -webkit-box; /* Necessary for webkit-based browsers */
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3; /* Limits the text to 2 lines */
  overflow: hidden; /* Hides the rest of the text */
  text-overflow: ellipsis; /* Adds ellipsis (...) at the end if the text overflows */
  white-space: normal; /* Ensures the text wraps to the next line */
}
</style>
