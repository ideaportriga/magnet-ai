<script setup lang="ts">
/**
 * Retrieval answer card — shows the original question, sources and the
 * resulting prompt details modal. Rewritten on `@ds`. Quasar dependencies
 * are gone: `q-icon`/`q-spinner-dots` → `KmGlyph` + custom dots loader,
 * clipboard via `@ds/utils/clipboard`.
 */

import { computed, ref } from 'vue'
import { copyToClipboard } from '@ds/utils/clipboard'
import { notify } from '@shared/utils/notify'
import KmBtn from '@ds/components/domain/KmBtn.vue'
import KmChip from '@ds/components/domain/KmChip.vue'
import KmGlyph from '@ds/components/domain/KmGlyph.vue'
import KmIcon from '@ds/components/domain/KmIcon.vue'
import KmInput from '@ds/components/domain/KmInput.vue'
import KmPopupConfirm from '@ds/components/domain/KmPopupConfirm.vue'
import SearchFeedback from '../Search/Feedback.vue'
import SearchFeedbackConfirm from '../Search/FeedbackConfirm.vue'

const DEFAULT_T = {
  refine: 'Refine',
  unknownSource: 'Unknown source',
  resultingPromptDetails: 'Resulting prompt details',
  copyToClipboard: 'Copy to clipboard',
  cancel: 'Cancel',
}

interface SourceMetadata {
  type?: 'video' | 'pdf' | string
  source?: string
  title?: string
  pageNumber?: number
  page?: number
}
interface AnswerSource {
  score?: number
  content?: string
  metadata?: SourceMetadata
}
interface RetrievalAnswer {
  id?: string
  prompt?: string
  answer?: string
  loading?: boolean
  results?: AnswerSource[]
  feedback?: { like?: boolean }
}

const props = defineProps<{
  answer: RetrievalAnswer
  uiSettings?: Record<string, unknown>
  t?: Record<string, string>
}>()

const emit = defineEmits<{
  refine: [question: string]
  feedback: [payload: { id?: string; like: boolean; comment?: string }]
  selectAnswer: [source: AnswerSource]
}>()

const showFeedback = ref(false)
const showFeedbackConfirm = ref(false)
const showResultingPrompt = ref(false)

const mergedT = computed(() => ({ ...DEFAULT_T, ...(props.t ?? {}) }))

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

async function react({ like, comment = '' }: { like: boolean; comment?: string }) {
  showFeedbackConfirm.value = false
  emit('feedback', { id: props.answer.id, like, comment })
  if (!like && comment) showFeedbackConfirm.value = true
}

defineExpose({ copy })
</script>

<template>
  <SearchFeedback v-model:modal="showFeedback" @on-submit="react" />
  <SearchFeedbackConfirm v-model:modal="showFeedbackConfirm" />

  <article class="retrieval-answer stack" data-gap="md">
    <header class="retrieval-answer__question cluster gap-md" data-wrap="no">
      <span class="retrieval-answer__icon">
        <KmGlyph name="user" size="20px" tone="brand-soft" />
      </span>
      <div class="retrieval-answer__question-body cluster gap-sm" data-justify="between" data-wrap="no">
        <p class="retrieval-answer__prompt">{{ answer.prompt }}</p>
        <KmBtn
          v-if="!answer.loading"
          flat
          icon="edit"
          icon-size="16px"
          size="sm"
          :tooltip="mergedT.refine"
          @click="refine(answer.prompt ?? '')"
        />
      </div>
    </header>

    <section class="retrieval-answer__answer cluster gap-md" data-wrap="no" data-align="start">
      <span class="retrieval-answer__icon">
        <KmIcon name="magnet" width="20" height="22" />
      </span>
      <div class="stack gap-sm" style="flex: 1; min-inline-size: 0">
        <span v-if="answer.loading" class="retrieval-answer__dots">
          <span class="retrieval-answer__dot" />
          <span class="retrieval-answer__dot" />
          <span class="retrieval-answer__dot" />
        </span>
        <template v-else-if="mainAnswer.hasAnswers">
          <div
            v-for="(source, index) in mainAnswerSources"
            :key="index"
            class="retrieval-answer__source cluster gap-md"
            data-align="center"
          >
            <span class="retrieval-answer__source-icon">
              <KmGlyph
                :name="source.metadata?.type === 'video' ? 'video' : source.metadata?.type === 'pdf' ? 'file-pdf' : 'file-text'"
              />
            </span>

            <div class="retrieval-answer__source-meta">
              <template v-if="source.metadata?.source">
                <a class="retrieval-answer__title" @click="$emit('selectAnswer', source)">
                  {{ source.metadata.title }}
                  <span v-if="source.metadata.pageNumber || source.metadata.page">
                    | Page {{ source.metadata.pageNumber || source.metadata.page }}
                  </span>
                </a>
                <p class="retrieval-answer__excerpt">{{ source.content }}</p>
              </template>
              <template v-else>
                <span class="retrieval-answer__title retrieval-answer__title--missing">
                  {{ source.metadata?.title || mergedT.unknownSource }}
                </span>
              </template>
            </div>

            <KmChip
              :tooltip="`Score: ${score(source.score)}`"
              tone="score"
              :label="score(source.score)"
              label-class="retrieval-answer__score-label retrieval-answer__score"
            />

            <div v-if="source.metadata?.type === 'video'" class="retrieval-answer__video">
              <iframe
                :src="source.metadata.source"
                width="100%"
                height="100%"
                frameborder="0"
                scrolling="no"
                allowfullscreen
              />
            </div>
          </div>
        </template>
      </div>
    </section>

    <KmPopupConfirm
      :visible="showResultingPrompt"
      :title="mergedT.resultingPromptDetails"
      :confirm-button-label="mergedT.copyToClipboard"
      :cancel-button-label="mergedT.cancel"
      @confirm="copy"
      @cancel="showResultingPrompt = false"
    >
      <div class="stack" data-gap="sm">
        <span class="retrieval-answer__messages-label">Messages</span>
        <KmInput :readonly="true" :rows="10" autogrow />
      </div>
    </KmPopupConfirm>
  </article>
</template>

<style scoped>
.retrieval-answer {
  background: var(--ds-color-white);
  border-radius: var(--ds-radius-xl);
  padding: var(--ds-space-md);
  inline-size: 100%;
  min-inline-size: 450px;
  max-inline-size: 800px;
}

.retrieval-answer__icon { padding-block-start: var(--ds-space-2xs); flex: none; }

.retrieval-answer__question-body { flex: 1; min-inline-size: 0; }
.retrieval-answer__prompt {
  font-size: var(--ds-font-size-label);
  font-weight: var(--ds-font-weight-medium);
  margin: 0;
  white-space: pre-wrap;
  overflow-wrap: break-word;
  flex: 1;
}

.retrieval-answer__source { padding-block: var(--ds-space-sm); border-block-end: 1px solid var(--ds-color-border); }
.retrieval-answer__source:last-child { border-block-end: 0; }
.retrieval-answer__source-icon { flex: none; align-self: flex-start; padding-block-start: var(--ds-space-2xs); }
.retrieval-answer__source-meta { flex: 1; min-inline-size: 0; }
.retrieval-answer__title {
  font-weight: var(--ds-font-weight-semibold);
  word-break: break-all;
  color: var(--ds-color-primary);
  cursor: pointer;
}
.retrieval-answer__title--missing { color: var(--ds-color-text-grey); cursor: default; }
.retrieval-answer__excerpt {
  font-size: var(--ds-font-size-caption);
  color: var(--ds-color-secondary-text);
  margin: var(--ds-space-2xs) 0 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: normal;
}

.retrieval-answer__score { flex: none; }

.retrieval-answer__video {
  inline-size: 100%;
  margin-block-start: var(--ds-space-sm);
  border-radius: var(--ds-radius-xl);
  overflow: hidden;
  position: relative;
  padding-block-end: 60%;
}
.retrieval-answer__video iframe { position: absolute; inset: 0; }

.retrieval-answer__dots { display: inline-flex; gap: 6px; padding: var(--ds-space-sm) 0; }
.retrieval-answer__dot {
  inline-size: 8px;
  block-size: 8px;
  background: var(--ds-color-primary);
  border-radius: 50%;
  animation: ds-dot-pulse 1.1s var(--ds-ease-in-out) infinite;
}
.retrieval-answer__dot:nth-child(2) { animation-delay: 0.15s; }
.retrieval-answer__dot:nth-child(3) { animation-delay: 0.3s; }

.retrieval-answer__messages-label { font-size: var(--ds-font-size-caption); color: var(--ds-color-secondary-text); }
</style>
