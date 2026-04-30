<template>
  <search-feedback v-model:modal="showFeedback" @on-submit="react" />
  <search-feedback-confirm v-model:modal="showFeedbackConfirm" />
  <div class="stack height-fit search-answer-container border-radius-12 p-md bg-white" data-gap="0" data-test="preview-answer">
    <div class="flex-none">
      <div class="cluster" data-gap="lg" data-wrap="no">
        <div class="pt-xs">
          <km-glyph :name="&quot;user&quot;" size="20px" tone="brand-soft" />
        </div>
        <div class="flex stretch">
          <div class="flex stretch" style="flex-wrap: nowrap; margin: auto">
            <div class="search-answer-text stretch km-title my-xs text-pre-wrap">{{ answer.prompt }}</div>
          </div>
          <km-btn v-if="!answer.loading" class="self-start" icon="edit" icon-size="16px" size="sm" flat :tooltip="m.panel_refine()" @click="refine(answer.prompt)" />
        </div>
      </div>
    </div>
    <div v-if="!answer.loading" class="flex-none">
      <div class="cluster" data-gap="lg" data-wrap="no">
        <div class="pt-xs">
          <km-glyph :name="&quot;user&quot;" size="20px" tone="brand-soft" style="visibility: hidden" />
        </div>
        <div class="flex stretch">
          <div class="flex stretch" style="flex-wrap: nowrap; margin: auto">
            <km-btn tone="brand" link content-class="p-0" @click="showResultingPrompt = true">{{ m.ragTools_viewResultingPrompt() }}</km-btn>
          </div>
        </div>
      </div>
    </div>
    <div class="flex-none pt-md">
      <div class="cluster" data-gap="lg" data-wrap="no">
        <div class="pt-xs">
          <km-icon :name="&quot;magnet&quot;" width="20" height="22" />
        </div>
        <div class="flex-1 overflow-hidden">
          <template v-if="answer.loading">
            <div class="py-sm">
              <km-loader size="32px" />
            </div>
          </template>
          <div v-else class="stack border-radius-12 pt-sm pb-sm" data-gap="0">
            <div class="full-width">
              <div class="search-answer-text stretch km-paragraph">
                <km-markdown :source="mainAnswer.text" />
              </div>
            </div>
            <div class="cluster" data-gap="lg" style="block-size: 40px">
              <km-icon-btn v-if="uiSettings?.user_fideback" :tone="liked ? &quot;brand&quot; : undefined" icon="thumbs-up" icon-size="16px" :disabled="hasReacted" @click="react({ like: true })" />
              <km-icon-btn v-if="uiSettings?.user_fideback" :tone="disliked ? &quot;brand&quot; : undefined" icon="thumbs-down" icon-size="16px" :disabled="hasReacted" @click="showFeedback = true" />
              <div class="flex" style="flex: 1 0 0; align-self: stretch" />
              <km-btn icon="copy" icon-size="16px" size="sm" flat :tooltip="m.common_copy()" @click="copy" />
            </div>
          </div>
          <template v-if="mainAnswer.hasAnswers">
            <div class="stack py-md full-width bt-border mt-sm" data-gap="sm">
              <div class="km-description text-grey">{{ m.panel_answerFromArticles() }}</div>
              <template v-for="(source, index) in mainAnswerSources" :key="index">
                <div class="cluster" data-gap="md">
                  <div class="flex-none">
                    <km-glyph v-if="source?.metadata?.type === &quot;video&quot;" name="video" />
                    <km-glyph v-else-if="source?.metadata?.type === &quot;pdf&quot;" name="file-pdf" />
                    <km-glyph v-else name="file-text" />
                  </div>
                  <div class="flex-1">
                    <template v-if="source?.metadata?.source"><a class="km-link-title word-break-all cursor-pointer" @click="$emit(&quot;selectAnswer&quot;, source)">{{ true ? source?.metadata?.title || source?.metadata?.source : `Source ${index + 1}` }}</a></template>
                    <template v-else>
                      <div class="km-link-title word-break-all text-primary-text">{{ source?.metadata?.title || m.panel_unknownSource() }}</div>
                    </template>
                  </div>
                  <div class="flex-none self-start">
                    <km-chip class="border-radius-12 py-2xs" tone="score" :label="score(source.score)" label-class="km-small-chip" :tooltip="m.panel_score({ score: score(source.score) })" />
                  </div>
                </div>
                <template v-if="source?.metadata?.type === &quot;video&quot;">
                  <div class="full-width px-2xl">
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
    <km-popup-confirm :visible="showResultingPrompt" :title="m.ragTools_resultingPromptDetails()" :confirm-button-label="m.common_copyToClipboard()" :cancel-button-label="m.common_cancel()" @confirm="copy(&quot;test&quot;)" @cancel="showResultingPrompt = false">
      <div class="cluster pt-sm pl-sm" data-justify="between">
        <div class="basis-12 py-sm">
          <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.ragTools_messages() }}</div>
          <km-codemirror v-model="resultingPromptMessages" :readonly="true" language="json" />
        </div>
      </div>
    </km-popup-confirm>
  </div>
</template>

<script lang="ts">
import { m } from '@/paraglide/messages'
import { useCatalogOptions } from '@/queries/useCatalogOptions'
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
    const { activeVariant } = useVariantEntityDetail('rag_tools')
    const searchStore = useSearchStore()
    const { searchPrompt: prompt } = storeToRefs(searchStore)
    const { options: collectionsItems } = useCatalogOptions('collections')
    const showFeedback = ref(false)
    const showFeedbackConfirm = ref(false)
    return { m, activeVariant, searchStore, prompt, showFeedback, showFeedbackConfirm, collectionsItems, showResultingPrompt: ref(false) }
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
        // ...(!!this.answer.results?.length && this.answer.results[0])
      }
    },

    items() {
      return this.collectionsItems
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
      notify.copied(m.ragTools_answerCopied())
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
</style>
