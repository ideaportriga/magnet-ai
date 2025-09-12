<template lang="pug">
search-feedback(v-model:modal='showFeedback', @onSubmit='react')
search-feedback-confirm(v-model:modal='showFeedbackConfirm')
.column.no-wrap.height-fit.search-answer-container.border-radius-12.q-pa-12(
  :class='{ "bg-white": $theme === "default" }',
  @mouseenter='isHover = true',
  @mouseleave='isHover = false'
)
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
  .col-auto.q-pt-md
    .row.q-gap-16.no-wrap
      .q-pt-xs
        template(v-if='$theme === "default"')
          km-icon(:name='"magnet"', width='20', height='22')
        template(v-else)
          .bg-primary.flex.flex-center.round(:style='{ width: "28px", height: "28px" }')
            km-icon(name='ai', width='14', height='14')
      .col.overflow-hidden
        .column.border-radius-12.q-pt-8.q-pb-8
          .row.width-100
            .search-answer-text.stretch.km-paragraph
              km-markdown(:source='mainAnswer.text')

          //- FEEDBACK /
          .row.q-gap-16.items-center(style='height: 40px')
            template(v-if='$theme === "default" && displayFeedback')
              km-icon-btn(
                :color='`${liked ? "primary" : "icon"}`',
                icon='fas fa-thumbs-up',
                iconSize='16px',
                @click='like()',
                :disable='hasReacted',
                v-if='uiSettings?.user_fideback'
              )

              km-icon-btn(
                :color='`${disliked ? "primary" : "icon"}`',
                icon='fas fa-thumbs-down',
                iconSize='16px',
                @click='dislike()',
                :disable='hasReacted',
                v-if='uiSettings?.user_fideback'
              )
              .row(style='flex: 1 0 0; align-self: stretch')

              km-btn(icon='fas fa-copy', iconSize='16px', size='sm', flat, @click='copy', tooltip='Copy')
            template(v-else-if='displayFeedback')
              km-btn(
                svgIcon='like',
                iconColor='primary',
                iconSize='12px',
                size='xs',
                flat,
                @click='like()',
                :disable='hasReacted',
                v-if='uiSettings?.user_fideback',
                :class='{ "bg-like-bg border-radius-6": feedback === true }'
              )
              km-btn(
                svgIcon='dislike',
                iconColor='primary',
                iconSize='12px',
                size='xs',
                flat,
                @click='dislike()',
                :disable='hasReacted',
                v-if='uiSettings?.user_fideback',
                :class='{ "bg-dislike-bg border-radius-6": feedback === false }'
              )
              .row(style='flex: 1 0 0; align-self: stretch')
              km-btn(svgIcon='copy', iconColor='primary', iconSize='12px', size='xs', flat, @click='copy', tooltip='Copy')

        template(v-if='mainAnswer.hasAnswers')
          .column.q-py-12.full-width.q-gap-8.bt-border.q-mt-sm
            .km-description.text-grey The answer was found using information from the following articles:

            template(v-for='(source, index) in mainAnswerSources')
              .row.q-gap-12.items-center
                .col-auto
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
</template>

<script lang="ts">
import { copyToClipboard } from 'quasar'
import { useSearch } from '@/pinia'
import { ref, Ref } from 'vue'

export default {
  props: ['answer', 'uiSettings', 'isLastMessage'],
  emits: ['refine'],
  setup() {
    const showFeedback = ref(false)
    const showFeedbackConfirm = ref(false)
    const searchStore = useSearch()
    const isHover = ref(false)

    return { showFeedback, showFeedbackConfirm, searchStore, isHover }
  },
  computed: {
    hasReacted() {
      return this.answer.feedback?.type === 'like' || this.answer.feedback?.type === 'dislike'
    },
    feedback() {
      if (this.answer.feedback?.type === 'like') return true
      if (this.answer.feedback?.type === 'dislike') return false
      return null
    },
    displayFeedback() {
      if (this.uiSettings?.user_fideback) {
        return this.isHover || this.isLastMessage
      }
      return false
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
  },
  watch: {},
  created() {},
  mounted() {},
  methods: {
    score(text: string) {
      return Number.parseFloat(text).toFixed(2)
    },

    copy() {
      copyToClipboard(this.mainAnswer.text || '')
      this.searchStore.reportCopyUsage(this.answer)
      this.$q.notify({
        position: 'top',
        message: 'Answer has been copied to clipboard',
        color: 'positive',
        textColor: 'black',
        timeout: 1000,
      })
    },

    refine(question: string) {
      this.$emit('refine', question)
    },

    openURL(val: string) {
      window.open(val, '_blank')
    },
    like() {
      this.showFeedbackConfirm = true
      this.react({ type: 'like' })
    },
    dislike() {
      this.showFeedback = true
    },
    async react(feedback: { type: string; reason?: string; comment?: string }) {
      this.searchStore.sendFeedback(this.answer, feedback)
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

@media (max-width: 500px)
  .search-answer-container
    min-width: unset
    max-width: unset

.search-answer-text {
  overflow-wrap: break-word;
  width: 1px;
}
</style>
