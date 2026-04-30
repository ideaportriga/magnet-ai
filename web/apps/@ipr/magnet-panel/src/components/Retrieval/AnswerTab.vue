<template>
  <div
    class="stack height-fit search-answer-container border-radius-12 p-md"
    data-gap="0"
    :class="{ &quot;bg-white&quot;: $theme === &quot;default&quot; }"
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
        </div>
      </div>
    </div>
    <div class="flex-none pt-md pr-sm">
      <div
        class="cluster"
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
        <div
          class="stack py-sm full-width"
          data-gap="sm"
        >
          <template v-if="mainAnswer.hasAnswers">
            <template
              v-for="(source, index) in mainAnswerSources"
              :key="index"
            >
              <div
                class="cluster"
                data-gap="md"
              >
                <div class="flex-none self-start">
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
                    >{{ source?.metadata?.title }}{{ (source?.metadata?.pageNumber || source?.metadata?.page) ? ` | Page ${source?.metadata?.pageNumber || source?.metadata?.page} ` : '' }}
                      <div class="km-field text-secondary-text py-xs clamp-text">{{ source?.content }}</div></a>
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
          </template>
        </div>
      </div>
    </div>
    <km-popup-confirm
      :visible="showResultingPrompt"
      title="Resulting prompt details"
      confirm-button-label="Copy to clipboard"
      cancel-button-label="Cancel"
      @confirm="copyToClipboard(&quot;test&quot;)"
      @cancel="showResultingPrompt = false"
    >
      <div
        class="cluster pt-sm pl-sm"
        data-justify="between"
      >
        <div class="basis-12 py-sm">
          <div class="km-field text-secondary-text pb-xs pl-sm">
            Messages
          </div>
          <km-input
            :readonly="true"
            :rows="10"
            autogrow
          />
        </div>
      </div>
    </km-popup-confirm>
  </div>
</template>

<script lang="ts">
import { useCollections } from '@/pinia'
import { storeToRefs } from 'pinia'
import { copyToClipboard } from '@ds/utils/clipboard'
import { notify } from '@shared/utils/notify'

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
      notify.copied()
    },

    refine(question) {
      this.$emit('refine', question)
    },

    openURL(val) {
      window.open(val, '_blank')
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
  inline-size: 1px;
}
</style>
