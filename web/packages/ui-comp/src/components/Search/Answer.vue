<script setup lang="ts">
/**
 * Search answer card with feedback (like / dislike), copy, and a list of
 * source citations. Rewritten on `@ds`. Theme-conditional rendering
 * (`$theme === 'default'` vs salesforce) is preserved via the same global
 * property.
 */

import { computed, getCurrentInstance, ref } from 'vue'
import { copyToClipboard } from '@ds/utils/clipboard'
import { notify } from '@shared/utils/notify'
import KmBtn from '@ds/components/domain/KmBtn.vue'
import KmChip from '@ds/components/domain/KmChip.vue'
import KmGlyph from '@ds/components/domain/KmGlyph.vue'
import KmIcon from '@ds/components/domain/KmIcon.vue'
import KmIconBtn from '@ds/components/domain/KmIconBtn.vue'
import KmMarkdown from '@ds/components/domain/KmMarkdown.vue'
import SearchFeedback from './Feedback.vue'
import SearchFeedbackConfirm from './FeedbackConfirm.vue'

const DEFAULT_T = {
  refine: 'Refine',
  copy: 'Copy',
  unknownSource: 'Unknown source',
  sourcesIntro: 'The answer was found using information from the following articles:',
}

interface Source {
  score?: number
  content?: string
  metadata?: { type?: string; source?: string; title?: string; pageNumber?: number; page?: number }
}
interface SearchAnswerData {
  id?: string
  prompt?: string
  answer?: string
  results?: Source[]
}

const props = defineProps<{
  answer: SearchAnswerData
  uiSettings?: { user_fideback?: boolean }
  t?: Record<string, string>
}>()

const emit = defineEmits<{
  refine: [question: string]
}>()

const theme = computed<string>(() => {
  const proxy = getCurrentInstance()?.appContext.config.globalProperties as { $theme?: string }
  return proxy?.$theme ?? 'default'
})

const showFeedback = ref(false)
const showFeedbackConfirm = ref(false)
const feedback = ref<boolean | null>(null)

const mergedT = computed(() => ({ ...DEFAULT_T, ...(props.t ?? {}) }))

const hasReacted = computed(() => typeof feedback.value === 'boolean')
const liked = computed(() => feedback.value === true)
const disliked = computed(() => feedback.value === false)

const mainAnswer = computed(() => ({
  id: props.answer.id,
  text: props.answer.answer,
  hasAnswers: !!props.answer.results?.length,
}))
const mainAnswerSources = computed(() => props.answer.results ?? [])

function score(text: number | string | undefined): string {
  return Number.parseFloat(String(text ?? 0)).toFixed(2)
}

async function copy() {
  try {
    await copyToClipboard(mainAnswer.value.text || '')
    notify.copied()
  } catch {
    notify.error('Failed to copy')
  }
}

function refine(question: string) {
  emit('refine', question)
}

function like() {
  feedback.value = true
  showFeedbackConfirm.value = true
}
function dislike() {
  feedback.value = false
  showFeedback.value = true
}

function react({ like: isLike }: { like: boolean }) {
  showFeedbackConfirm.value = false
  feedback.value = isLike
  showFeedbackConfirm.value = true
}
</script>

<template>
  <SearchFeedback v-model:modal="showFeedback" @on-submit="react" />
  <SearchFeedbackConfirm v-model:modal="showFeedbackConfirm" />

  <article class="search-answer stack" data-gap="md" :data-theme="theme">
    <header class="search-answer__question cluster gap-md" data-wrap="no">
      <span v-if="theme === 'default'" class="search-answer__icon">
        <KmGlyph name="user" size="20px" tone="brand-soft" />
      </span>
      <span v-else class="search-answer__avatar search-answer__avatar--user">
        <KmGlyph name="user" size="14px" />
      </span>

      <div class="search-answer__question-body cluster gap-sm" data-wrap="no" data-justify="between">
        <p class="search-answer__prompt">{{ answer.prompt }}</p>
        <KmBtn
          v-if="theme === 'default'"
          flat
          icon="edit"
          icon-size="16px"
          size="sm"
          :tooltip="mergedT.refine"
          @click="refine(answer.prompt ?? '')"
        />
        <KmBtn
          v-else
          flat
          icon="edit"
          icon-size="12px"
          size="xs"
          :tooltip="mergedT.refine"
          @click="refine(answer.prompt ?? '')"
        />
      </div>
    </header>

    <section class="search-answer__answer cluster gap-md" data-wrap="no" data-align="start">
      <span class="search-answer__icon">
        <KmIcon v-if="theme === 'default'" name="magnet" width="20" height="22" />
        <span v-else class="search-answer__avatar search-answer__avatar--ai">
          <KmGlyph name="robot" size="14px" />
        </span>
      </span>

      <div class="search-answer__answer-body">
        <KmMarkdown :source="mainAnswer.text" class="search-answer__markdown" />

        <div class="cluster gap-md" data-align="center">
          <template v-if="theme === 'default'">
            <KmIconBtn
              v-if="uiSettings?.user_fideback"
              icon="thumbs-up"
              icon-size="16px"
              :tone="liked ? 'brand' : undefined"
              :disabled="hasReacted"
              @click="like"
            />
            <KmIconBtn
              v-if="uiSettings?.user_fideback"
              icon="thumbs-down"
              icon-size="16px"
              :tone="disliked ? 'brand' : undefined"
              :disabled="hasReacted"
              @click="dislike"
            />
            <span class="search-answer__spacer" />
            <KmBtn flat icon="copy" icon-size="16px" size="sm" :tooltip="mergedT.copy" @click="copy" />
          </template>
          <template v-else>
            <KmBtn
              v-if="uiSettings?.user_fideback"
              flat
              icon="thumbs-up"
              icon-size="16px"
              size="xs"
              :class="{ 'search-answer__feedback-active--like': feedback === true }"
              :disable="hasReacted"
              @click="like"
            />
            <KmBtn
              v-if="uiSettings?.user_fideback"
              flat
              icon="thumbs-down"
              icon-size="16px"
              size="xs"
              :class="{ 'search-answer__feedback-active--dislike': feedback === false }"
              :disable="hasReacted"
              @click="dislike"
            />
            <span class="search-answer__spacer" />
            <KmBtn flat icon="copy" icon-size="16px" size="xs" :tooltip="mergedT.copy" @click="copy" />
          </template>
        </div>

        <div v-if="mainAnswer.hasAnswers" class="search-answer__sources stack" data-gap="sm">
          <p class="search-answer__sources-intro">{{ mergedT.sourcesIntro }}</p>

          <template v-for="(source, index) in mainAnswerSources" :key="index">
            <div class="search-answer__source cluster gap-md" data-align="center">
              <span class="search-answer__source-icon">
                <template v-if="theme === 'default'">
                  <KmGlyph
                    :name="source.metadata?.type === 'video' ? 'video' : source.metadata?.type === 'pdf' ? 'file-pdf' : 'file-text'"
                  />
                </template>
                <template v-else>
                  <KmGlyph
                    :name="source.metadata?.type === 'video' ? 'video' : source.metadata?.type === 'pdf' ? 'file-pdf' : 'file'"
                    size="18px"
                  />
                </template>
              </span>

              <div class="search-answer__source-meta">
                <a
                  v-if="source.metadata?.source"
                  class="search-answer__title"
                  :href="source.metadata.source"
                  target="_blank"
                >
                  {{ source.metadata.title }}
                  <span v-if="source.metadata.pageNumber || source.metadata.page">
                    | Page {{ source.metadata.pageNumber || source.metadata.page }}
                  </span>
                </a>
                <span v-else class="search-answer__title search-answer__title--missing">
                  {{ source.metadata?.title || mergedT.unknownSource }}
                </span>
              </div>

              <KmChip tone="score" :label="score(source.score)" :tooltip="`Score: ${score(source.score)}`" />
            </div>

            <div v-if="source.metadata?.type === 'video'" class="search-answer__video-wrap">
              <iframe
                :src="source.metadata.source"
                width="100%"
                height="100%"
                frameborder="0"
                scrolling="no"
                allowfullscreen
              />
            </div>
          </template>
        </div>
      </div>
    </section>
  </article>
</template>

<style scoped>
.search-answer {
  inline-size: 100%;
  min-inline-size: 450px;
  max-inline-size: 800px;
  padding: var(--ds-space-md);
  border-radius: var(--ds-radius-xl);
}
.search-answer[data-theme='default'] { background: var(--ds-color-white); }

@media (max-width: 500px) {
  .search-answer { min-inline-size: unset; max-inline-size: unset; }
}

.search-answer__icon { padding-block-start: var(--ds-space-2xs); flex: none; }
.search-answer__avatar {
  inline-size: 28px;
  block-size: 28px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.search-answer__avatar--user { background: var(--ds-color-secondary-bg); }
.search-answer__avatar--ai    { background: var(--ds-color-primary); }

.search-answer__question-body { flex: 1; min-inline-size: 0; }
.search-answer__prompt {
  font-size: var(--ds-font-size-label);
  font-weight: var(--ds-font-weight-medium);
  margin: 0;
  white-space: pre-wrap;
  overflow-wrap: break-word;
  flex: 1;
}

.search-answer__answer-body { flex: 1; min-inline-size: 0; overflow: hidden; }
.search-answer__markdown { overflow-wrap: break-word; }

.search-answer__spacer { flex: 1 0 0; }

.search-answer__sources {
  border-block-start: 1px solid var(--ds-color-border);
  padding-block-start: var(--ds-space-md);
  margin-block-start: var(--ds-space-sm);
}
.search-answer__sources-intro {
  font-size: var(--ds-font-size-caption);
  color: var(--ds-color-text-grey);
  margin: 0;
}
.search-answer__source { padding-block: var(--ds-space-xs); }
.search-answer__source-icon { flex: none; align-self: flex-start; padding-block-start: var(--ds-space-2xs); }
.search-answer__source-meta { flex: 1; min-inline-size: 0; }
.search-answer__title {
  font-weight: var(--ds-font-weight-semibold);
  word-break: break-all;
  color: var(--ds-color-primary);
  text-decoration: none;
}
.search-answer__title:hover { text-decoration: underline; }
.search-answer__title--missing { color: var(--ds-color-text-grey); }

.search-answer__video-wrap {
  inline-size: 100%;
  margin-block-start: var(--ds-space-sm);
  border-radius: var(--ds-radius-xl);
  overflow: hidden;
  position: relative;
  padding-block-end: 60%;
}
.search-answer__video-wrap iframe { position: absolute; inset: 0; }

.search-answer__feedback-active--like { background: var(--ds-color-like-bg); border-radius: var(--ds-radius-md); }
.search-answer__feedback-active--dislike { background: var(--ds-color-dislike-bg); border-radius: var(--ds-radius-md); }
</style>
