<template>
  <search-feedback
    v-model:modal="showFeedback"
    @on-submit="react"
  />
  <search-feedback-confirm v-model:modal="showFeedbackConfirm" />
  <div
    class="stack height-fit search-answer-container border-radius-12 p-md"
    data-gap="0"
    :class="{ &quot;bg-white&quot;: $theme === &quot;default&quot; }"
    @mouseenter="isHover = true"
    @mouseleave="isHover = false"
  >
    <div class="flex-none">
      <div
        class="cluster"
        data-gap="lg"
        data-wrap="no"
      >
        <template v-if="$theme === &quot;default&quot;">
          <div class="pt-xs">
            <km-glyph
              :name="&quot;user&quot;"
              size="20px"
              tone="brand-soft"
            />
          </div>
        </template>
        <template v-else>
          <div
            class="bg-user-grey flex flex-center round"
            :style="{ width: &quot;28px&quot;, height: &quot;28px&quot; }"
          >
            <km-glyph
              name="user"
              size="14px"
            />
          </div>
        </template>
        <div class="flex stretch">
          <div
            class="flex stretch"
            style="flex-wrap: nowrap"
          >
            <div class="search-answer-text stretch km-title my-xs text-pre-wrap">
              {{ answer.prompt }}
            </div>
          </div>
          <template v-if="!answer.loading">
            <template v-if="$theme === &quot;default&quot;">
              <km-btn
                class="self-start"
                icon="edit"
                icon-size="16px"
                size="sm"
                flat
                tooltip="Refine"
                @click="refine(answer.prompt)"
              />
            </template>
            <template v-else>
              <km-btn
                class="self-start"
                icon="edit"
                icon-size="12px"
                size="xs"
                flat
                tooltip="Refine"
                @click="refine(answer.prompt)"
              />
            </template>
          </template>
        </div>
      </div>
    </div>
    <div class="flex-none pt-md">
      <div
        class="cluster pt-md"
        data-gap="lg"
        data-wrap="no"
      >
        <div class="pt-xs">
          <template v-if="$theme === &quot;default&quot;">
            <km-icon
              :name="&quot;magnet&quot;"
              width="20"
              height="22"
            />
          </template>
          <template v-else>
            <div
              class="bg-primary flex flex-center round"
              :style="{ width: &quot;28px&quot;, height: &quot;28px&quot; }"
            >
              <km-glyph
                name="robot"
                size="14px"
              />
            </div>
          </template>
        </div>
        <div class="flex-1 overflow-hidden">
          <template v-if="answer.loading">
            <div class="py-sm">
              <km-loader
                size="32px"
              />
            </div>
          </template>
          <div
            v-else
            class="stack border-radius-12 pt-sm pb-sm"
            data-gap="0"
          >
            <div class="full-width">
              <div class="search-answer-text stretch km-paragraph">
                <km-markdown :source="mainAnswer.text" />
              </div>
            </div>
            <div
              class="cluster"
              style="block-size: 40px"
            >
              <template v-if="$theme === &quot;default&quot; &amp;&amp; displayFeedback">
                <km-icon-btn
                  v-if="uiSettings?.user_fideback"
                  :tone="liked ? &quot;brand&quot; : undefined"
                  icon="thumbs-up"
                  icon-size="16px"
                  :disable="hasReacted"
                  @click="like()"
                />
                <km-icon-btn
                  v-if="uiSettings?.user_fideback"
                  :tone="disliked ? &quot;brand&quot; : undefined"
                  icon="thumbs-down"
                  icon-size="16px"
                  :disable="hasReacted"
                  @click="dislike()"
                />
                <div
                  class="flex"
                  style="flex: 1 0 0; align-self: stretch"
                />
                <km-btn
                  icon="copy"
                  icon-size="16px"
                  size="sm"
                  flat
                  tooltip="Copy"
                  @click="copy"
                />
              </template>
              <template v-else-if="displayFeedback">
                <km-btn
                  v-if="uiSettings?.user_fideback"
                  icon="thumbs-up"
                  icon-size="16px"
                  size="xs"
                  flat
                  :disable="hasReacted"
                  :class="{ &quot;bg-like-bg border-radius-6&quot;: feedback === true }"
                  @click="like()"
                />
                <km-btn
                  v-if="uiSettings?.user_fideback"
                  icon="thumbs-down"
                  icon-size="16px"
                  size="xs"
                  flat
                  :disable="hasReacted"
                  :class="{ &quot;bg-dislike-bg border-radius-6&quot;: feedback === false }"
                  @click="dislike()"
                />
                <div
                  class="flex"
                  style="flex: 1 0 0; align-self: stretch"
                />
                <km-btn
                  icon="copy"
                  icon-size="16px"
                  size="xs"
                  flat
                  tooltip="Copy"
                  @click="copy"
                />
              </template>
            </div>
          </div>
          <template v-if="mainAnswer.hasAnswers">
            <div
              class="stack py-md full-width bt-border mt-sm"
              data-gap="sm"
            >
              <div class="km-description text-grey">
                The answer was found using information from the following articles:
              </div>
              <template
                v-for="(source, index) in mainAnswerSources"
                :key="index"
              >
                <div
                  class="cluster"
                  data-gap="md"
                >
                  <div class="flex-none">
                    <template v-if="$theme === &quot;default&quot;">
                      <km-glyph
                        v-if="source?.metadata?.type === &quot;video&quot;"
                        name="video"
                      />
                      <km-glyph
                        v-else-if="source?.metadata?.type === &quot;pdf&quot;"
                        name="file-pdf"
                      />
                      <km-glyph
                        v-else
                        name="file-text"
                      />
                    </template>
                    <template v-else>
                      <km-glyph
                        v-if="source?.metadata?.type === &quot;video&quot;"
                        name="video"
                        size="16px"
                      />
                      <km-glyph
                        v-else-if="source?.metadata?.type === &quot;pdf&quot;"
                        name="file-pdf"
                        size="16px"
                      />
                      <km-glyph
                        v-else
                        name="file"
                        size="16px"
                      />
                    </template>
                  </div>
                  <div class="flex-1">
                    <template v-if="source?.metadata?.source">
                      <a
                        class="km-link-title word-break-all cursor-pointer"
                        :href="source?.metadata?.source"
                        target="_blank"
                      >{{ source?.metadata?.title }}{{ (source?.metadata?.pageNumber || source?.metadata?.page) ? ` | Page ${source?.metadata?.pageNumber || source?.metadata?.page} ` : '' }}</a>
                    </template>
                    <template v-else>
                      <div class="km-link-title word-break-all text-primary-text">
                        {{ source?.metadata?.title || 'Unknown source' }}
                      </div>
                    </template>
                  </div>
                  <div class="flex-none self-start">
                    <km-chip
                      class="border-radius-12 py-2xs"
                      :round="$theme === &quot;salesforce&quot;"
                      tone="score"
                      :label="score(source.score)"
                      label-class="km-small-chip"
                      :class="{ &quot;ba-border&quot;: $theme === &quot;salesforce&quot; }"
                      :tooltip="`Score: ${score(source.score)}`"
                    />
                  </div>
                </div>
                <template v-if="source?.metadata?.type === &quot;video&quot;">
                  <div class="full-width px-2xl">
                    <div
                      class="relative-position mt-sm border-radius-12 overflow-hidden mb-lg"
                      style="inline-size: 100%; padding-block-end: 60%"
                    >
                      <iframe
                        class="absolute-full"
                        width="100%"
                        height="100%"
                        frameborder="0"
                        scrolling="no"
                        allowfullscreen
                        :src="source?.metadata?.source"
                      />
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
import { copyToClipboard } from '@ds/utils/clipboard'
import { notify } from '@shared/utils/notify'
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
      notify.copied()
    },

    refine(question: string) {
      this.$emit('refine', question)
    },

    openURL(val: string) {
      window.open(val, '_blank')
    },
    like() {
      // this.showFeedbackConfirm = true
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
<style scoped>
.search-answer-container {
  min-inline-size: 450px;
  max-inline-size: 800px;
  inline-size: 100%;
}
@media (max-width: 500px) {
  .search-answer-container {
    min-inline-size: unset;
    max-inline-size: unset;
  }
}
.search-answer-text {
  overflow-wrap: break-word;
  inline-size: 1px;
}
</style>
