<template lang="pug">
.q-gutter-md
  .km-field
    .row.items-center.justify-between
      .text-secondary-text.q-pb-xs.km-title Post-transcription processing
      q-toggle(v-model='postTranscriptionEnabled', color='primary')
    .q-gutter-sm(v-if='postTranscriptionEnabled')
      .row.items-center.q-gutter-sm
        .col
          km-select(
            v-model='postTranscriptionPromptTemplate',
            :options='promptTemplates',
            option-label='name',
            option-value='system_name',
            emit-value, map-options, hasDropdownSearch, height='30px'
          )
        .col-auto(v-if='postTranscriptionPromptTemplate')
          km-btn(icon='open_in_new', flat, dense, @click='navigateToPrompt(postTranscriptionPromptTemplate)')
    .km-description.text-secondary-text.q-pt-2(v-if='postTranscriptionEnabled') Prompt template to post-process the transcript (map speakers to names).

  .km-field
    .row.items-center.justify-between
      .text-secondary-text.q-pb-xs.km-title Create Chapters
      q-toggle(v-model='createChaptersEnabled', color='primary')
    .q-gutter-sm(v-if='createChaptersEnabled')
      .row.items-center.q-gutter-sm
        .col
          km-select(
            v-model='createChaptersPromptTemplate',
            :options='promptTemplates',
            option-label='name',
            option-value='system_name',
            emit-value, map-options, hasDropdownSearch, height='30px'
          )
        .col-auto(v-if='createChaptersPromptTemplate')
          km-btn(icon='open_in_new', flat, dense, @click='navigateToPrompt(createChaptersPromptTemplate)')
    .km-description.text-secondary-text.q-pt-2(v-if='createChaptersEnabled') Prompt template for chapters.

  .km-field
    .row.items-center.justify-between
      .text-secondary-text.q-pb-xs.km-title Create Summary
      q-toggle(v-model='createSummaryEnabled', color='primary')
    .q-gutter-sm(v-if='createSummaryEnabled')
      .row.items-center.q-gutter-sm
        .col
          km-select(
            v-model='createSummaryPromptTemplate',
            :options='promptTemplates',
            option-label='name',
            option-value='system_name',
            emit-value, map-options, hasDropdownSearch, height='30px'
          )
        .col-auto(v-if='createSummaryPromptTemplate')
          km-btn(icon='open_in_new', flat, dense, @click='navigateToPrompt(createSummaryPromptTemplate)')
    .km-description.text-secondary-text.q-pt-2(v-if='createSummaryEnabled') Prompt template for summary.

  .km-field
    .row.items-center.justify-between
      .text-secondary-text.q-pb-xs.km-title Create Insights
      q-toggle(v-model='createInsightsEnabled', color='primary')
    .q-gutter-sm(v-if='createInsightsEnabled')
      .row.items-center.q-gutter-sm
        .col
          km-select(
            v-model='createInsightsPromptTemplate',
            :options='promptTemplates',
            option-label='name',
            option-value='system_name',
            emit-value, map-options, hasDropdownSearch, height='30px'
          )
        .col-auto(v-if='createInsightsPromptTemplate')
          km-btn(icon='open_in_new', flat, dense, @click='navigateToPrompt(createInsightsPromptTemplate)')
    .km-description.text-secondary-text.q-pt-2(v-if='createInsightsEnabled') Prompt template for insights.
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useNoteTakerStore } from '@/stores/noteTakerStore'
import { useRouter } from 'vue-router'
import { useEntityQueries } from '@/queries/entities'

const ntStore = useNoteTakerStore()
const router = useRouter()
const queries = useEntityQueries()

const { data: promptTemplatesListData } = queries.promptTemplates.useList()
const promptTemplates = computed(() => promptTemplatesListData.value?.items || [])

const setting = (path: string, fallback: any = false) => computed({
  get: () => path.split('.').reduce((o: any, k) => o?.[k], ntStore.settings) ?? fallback,
  set: (v: any) => ntStore.updateSetting( { path, value: v }),
})

const postTranscriptionEnabled = setting('post_transcription.enabled')
const postTranscriptionPromptTemplate = setting('post_transcription.prompt_template', '')
const createChaptersEnabled = setting('chapters.enabled')
const createChaptersPromptTemplate = setting('chapters.prompt_template', '')
const createSummaryEnabled = setting('summary.enabled')
const createSummaryPromptTemplate = setting('summary.prompt_template', '')
const createInsightsEnabled = setting('insights.enabled')
const createInsightsPromptTemplate = setting('insights.prompt_template', '')

const navigateToPrompt = (systemName: string) => {
  const prompt = promptTemplates.value.find((p: any) => p.system_name === systemName)
  if (prompt) window.open(router.resolve({ path: `/prompt-templates/${prompt.id}` }).href, '_blank')
}
</script>
