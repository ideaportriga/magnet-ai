<template lang="pug">
//- search-feedback(v-model:modal='showFeedback', @onSubmit='react')
//- search-feedback-confirm(v-model:modal='showFeedbackConfirm')
.column.no-wrap.height-fit.search-answer-container.border-radius-12.q-pa-12(:class='{ "bg-white": $theme === "default" }')
  //- QUESTION
  .col-auto
    .row.q-gap-16.no-wrap
      template(v-if='$theme === "default"')
        .q-pt-xs
          q-icon(:name='"fas fa-user"', size='20px', color='semi-transparent-primary')
      template(v-else)
        .bg-user-grey.flex.flex-center.round(:style='{ width: "28px", height: "28px" }')
          km-icon(name='user', width='14', height='14')
      .row.stretch
        .row.stretch.no-wrap
          .search-answer-text.stretch.km-title.q-my-4.text-pre-wrap {{ answer.prompt }}
        template(v-if='$theme === "default"')
          km-btn.self-start(icon='fas fa-pen', iconColor='icon', iconSize='16px', size='sm', flat, @click='refine(answer.prompt)', tooltip='Refine')
        template(v-else)
          km-btn.self-start(svgIcon='edit', iconColor='primary', iconSize='12px', size='xs', flat, @click='refine(answer.prompt)', tooltip='Refine')

  //- ANSWER
  .col-auto.q-pt-md.q-pr-6
    .row.q-gap-16.no-wrap
      .q-pt-xs
        template(v-if='$theme === "default"')
          km-icon(:name='"magnet"', width='20', height='22')
        template(v-else) 
          .bg-primary.flex.flex-center.round(:style='{ width: "28px", height: "28px" }')
            km-icon(name='ai', width='14', height='14')
      .column.q-py-8.full-width.q-gap-8
        template(v-if='mainAnswer.hasAnswers')
          template(v-for='(source, index) in mainAnswerSources')
            .row.q-gap-12.items-center
              .col-auto.self-start
                template(v-if='$theme === "default"')
                  q-icon(name='fas fa-video', color='secondary', v-if='source?.metadata?.type === "video"')
                  q-icon(name='fas fa-file-pdf', color='secondary', v-else-if='source?.metadata?.type === "pdf"')
                  q-icon(name='far fa-file-alt', color='secondary', v-else)
                template(v-else)
                  km-icon.q-mt-2(name='video-file', color='secondary', v-if='source?.metadata?.type === "video"', width='18px', height='18px')
                  km-icon.q-mt-2(name='pdf', color='secondary', v-else-if='source?.metadata?.type === "pdf"', width='18px', height='18px')
                  km-icon.q-mt-2(name='file', color='secondary', v-else, width='18px', height='18px')

              .col
                template(v-if='source?.metadata?.source')
                  a.km-link-title.word-break-all.cursor-pointer(:href='source?.metadata?.source', target='_blank') {{ `${source?.metadata?.title} ${source?.metadata?.pageNumber || source?.metadata?.page ? ` | Page ${source?.metadata?.pageNumber || source?.metadata?.page} ` : ''}` }}
                    .km-field.text-secondary-text.q-py-xs.clamp-text {{ source?.content }}
                template(v-else)
                  .km-link-title.word-break-all.text-primary-text {{ source?.metadata?.title || 'Unknown source' }}

              .col-auto.self-start
                km-chip.border-radius-12.text-score-relevant-text.q-py-2(
                  :round='$theme === "salesforce"',
                  color='score-relevant',
                  :label='score(source.score)',
                  label-class='km-small-chip',
                  :class='{ "ba-border": $theme === "salesforce" }',
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
    @confirm='copyToClipboard("test")',
    @cancel='showResultingPrompt = false'
  )
    .row.justify-between.q-pt-8.q-pl-8
      .col-12.q-py-8
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Messages
        km-input(:readonly='true', :rows='10', autogrow)
</template>

<script lang="ts">
import { useCollections } from '@/pinia'
import { storeToRefs } from 'pinia'
import { copyToClipboard } from 'quasar'

import { ref } from 'vue'

export default {
  props: ['answer', 'uiSettings'],
  emits: ['refine'],
  setup() {
    const collectionsStore = useCollections()
    const { items } = storeToRefs(collectionsStore)
    const showFeedback = ref(false)
    const showFeedbackConfirm = ref(false)
    return { showFeedback, showFeedbackConfirm, items, showResultingPrompt: ref(false) }
  },
  computed: {
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
    }
  },
}
</script>
<style lang="stylus" scoped>
.search-answer-container {
  min-width: 450px;
  max-width: 800px;
  width: 100%;
}

@media (max-width: 500px)
  .search-answer-container
    min-width: unset
    max-width: unset

.clamp-text {
  display: -webkit-box; /* Necessary for webkit-based browsers */
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2; /* Limits the text to 2 lines */
  overflow: hidden; /* Hides the rest of the text */
  text-overflow: ellipsis; /* Adds ellipsis (...) at the end if the text overflows */
  white-space: normal; /* Ensures the text wraps to the next line */
}

.search-answer-text {
  overflow-wrap: break-word;
  width: 1px;
}
</style>
