<template>
  <search-feedback v-model:modal="showFeedback" @on-submit="react" />
  <search-feedback-confirm v-model:modal="showFeedbackConfirm" />
  <div class="stack height-fit search-answer-container border-radius-12 p-md bg-white" data-gap="0">
    <div class="flex-none">
      <div class="cluster" data-gap="lg" data-wrap="no">
        <div class="pt-xs">
          <km-glyph :name="&quot;user&quot;" size="20px" tone="brand-soft" />
        </div>
        <div class="cluster stretch">
          <div class="cluster stretch m-auto" data-wrap="no">
            <div class="search-answer-text stretch km-title my-xs text-pre-wrap">{{ answer.prompt }}</div>
          </div>
          <km-btn class="self-start" icon="edit" icon-size="16px" size="sm" flat :tooltip="m.common_refine()" @click="refine(answer.prompt)" />
        </div>
      </div>
    </div>
    <div class="flex-none pt-md">
      <div class="cluster" data-gap="lg" data-wrap="no">
        <div class="pt-xs">
          <km-icon :name="&quot;magnet&quot;" width="20" height="22" />
        </div>
        <div class="flex-1 overflow-hidden">
          <template v-if="mainAnswer.hasAnswers">
            <div class="stack full-width mt-sm" data-gap="sm">
              <template v-for="(source, index) in mainAnswerSources" :key="index">
                <div class="cluster" data-gap="md">
                  <div class="flex-none self-start">
                    <km-glyph v-if="source?.metadata?.type === &quot;video&quot;" name="video" />
                    <km-glyph v-else-if="source?.metadata?.type === &quot;pdf&quot;" name="file-pdf" />
                    <km-glyph v-else name="file-text" />
                  </div>
                  <div class="flex-1">
                    <a class="km-link-title word-break-all cursor-pointer" @click="$emit(&quot;selectAnswer&quot;, source)">{{ source?.metadata?.title }}{{ (source?.metadata?.pageNumber || source?.metadata?.page) ? ` | ${source?.metadata?.pageNumber || source?.metadata?.page} ` : '' }}
                      <div class="km-field text-secondary-text py-xs clamp-text">{{ source?.content }}</div></a>
                  </div>
                  <div class="flex-none self-start">
                    <km-chip class="border-radius-12 py-2xs" tone="score" :label="score(source.score)" label-class="km-small-chip" :tooltip="m.panel_score({ score: score(source.score) })" />
                  </div>
                </div>
                <template v-if="source?.metadata?.type === &quot;video&quot;">
                  <div class="cluster width-100 px-2xl">
                    <div class="relative-position mt-sm border-radius-12 overflow-hidden mb-lg" style="inline-size: 100%; padding-block-end: 60%">
                      <iframe class="absolute-full" width="100%" height="100%" frameborder="0" scrolling="no" allowfullscreen :src="source?.metadata?.source" />
                    </div>
                  </div>
                </template>
              </template>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { useEntityQueries } from '@/queries/entities'
import { m } from '@/paraglide/messages'
import { copyToClipboard } from '@ds/utils/clipboard'
import { storeToRefs } from 'pinia'
import { useVariantEntityDetail } from '@/composables/useVariantEntityDetail'
import { useSearchStore } from '@/stores/searchStore'

import { ref, computed } from 'vue'
import { notify } from '@shared/utils/notify'

export default {
  props: ['answer'],
  emits: ['refine', 'selectAnswer'],
  setup() {
    const queries = useEntityQueries()
    const { activeVariant } = useVariantEntityDetail('rag_tools')
    const searchStore = useSearchStore()
    const { searchPrompt: prompt } = storeToRefs(searchStore)
    const { data: collectionsListData } = queries.collections.useList()
    const showFeedback = ref(false)
    const showFeedbackConfirm = ref(false)
    return { m, activeVariant, searchStore, prompt, showFeedback, showFeedbackConfirm, collectionsListData }
  },
  computed: {
    uiSettings() {
      return this.activeVariant?.ui_settings
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
    items() {
      return this.collectionsListData?.items ?? []
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
        notify.copied(m.notify_answerCopied())
    },

    refine(question) {
      this.$emit('refine', question)
    },

    openURL(val) {
      window.open(val, '_blank')
    },

    async react({ like, comment = '' }) {
      this.showFeedbackConfirm = false
      const res = await this.searchStore.sendFeedback({
        id: this.answer.id,
        like,
        comment,
      })
      if (res && !like && comment) this.showFeedbackConfirm = true
    },
  },
}
</script>
<style scoped>
.search-answer-container {
  min-inline-size: 450px;
  max-inline-size: 800px;
  inline-size: 100%;
}
.search-answer-text {
  overflow-wrap: break-word;
  inline-size: 1px;
}
.custom-link {
  transition: background-color 0.3s, transform 0.3s;
  cursor: pointer;
}
.custom-link:hover {
  transform: scale(1.02);
  text-decoration: underline;
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
