<template lang="pug">
div
  km-section(title='Transcript Enhancement', subTitle='Enable speaker mapping and transcript improvement')
    .row.items-center.justify-between
      .km-field.text-secondary-text.q-pl-8 Transcript Enhancement
      q-toggle(v-model='postTranscriptionEnabled', color='primary')
    .km-description.text-secondary-text.q-pt-xs.q-pl-8 Highly recommended to keep enabled, because this feature drives speaker mapping
    template(v-if='postTranscriptionEnabled')
      .q-mt-md
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Transcript Enhancement Prompt
        .row.items-center.q-gutter-sm
          .col
            km-select(
              v-model='postTranscriptionPromptTemplate',
              :options='promptTemplates',
              option-label='name',
              option-value='system_name',
              emit-value, map-options, hasDropdownSearch,
              height='auto', minHeight='36px'
            )
          .col-auto(v-if='postTranscriptionPromptTemplate')
            km-btn(icon='open_in_new', flat, dense, @click='navigateToPrompt(postTranscriptionPromptTemplate)')

  q-separator.q-my-lg

  km-section(title='Summarization', subTitle='Enable output summarization at different level of detail')
    //- Chapters
    .row.items-center.justify-between
      .km-field.text-secondary-text.q-pl-8 Chapters
      q-toggle(v-model='createChaptersEnabled', color='primary')
    .km-description.text-secondary-text.q-pt-xs.q-pl-8 Chapters are a more readable version of original transcript
    template(v-if='createChaptersEnabled')
      .q-mt-md
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Chapters Prompt Template
        .row.items-center.q-gutter-sm
          .col
            km-select(
              v-model='createChaptersPromptTemplate',
              :options='promptTemplates',
              option-label='name',
              option-value='system_name',
              emit-value, map-options, hasDropdownSearch,
              height='auto', minHeight='36px'
            )
          .col-auto(v-if='createChaptersPromptTemplate')
            km-btn(icon='open_in_new', flat, dense, @click='navigateToPrompt(createChaptersPromptTemplate)')

    q-separator.q-my-lg

    //- Summary
    .row.items-center.justify-between
      .km-field.text-secondary-text.q-pl-8 Summary
      q-toggle(v-model='createSummaryEnabled', color='primary')
    .km-description.text-secondary-text.q-pt-xs.q-pl-8 Summary is transcript processed according to your template
    template(v-if='createSummaryEnabled')
      .q-mt-md
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Summary Prompt Template
        .row.items-center.q-gutter-sm
          .col
            km-select(
              v-model='createSummaryPromptTemplate',
              :options='promptTemplates',
              option-label='name',
              option-value='system_name',
              emit-value, map-options, hasDropdownSearch,
              height='auto', minHeight='36px'
            )
          .col-auto(v-if='createSummaryPromptTemplate')
            km-btn(icon='open_in_new', flat, dense, @click='navigateToPrompt(createSummaryPromptTemplate)')

    q-separator.q-my-lg

    //- Insights
    .row.items-center.justify-between
      .km-field.text-secondary-text.q-pl-8 Insights
      q-toggle(v-model='createInsightsEnabled', color='primary')
    .km-description.text-secondary-text.q-pt-xs.q-pl-8 Insights are key items extracted from the transcript - e.g. to-do items, contacts, tasks etc
    template(v-if='createInsightsEnabled')
      .q-mt-md
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Insights Prompt Template
        .row.items-center.q-gutter-sm
          .col
            km-select(
              v-model='createInsightsPromptTemplate',
              :options='promptTemplates',
              option-label='name',
              option-value='system_name',
              emit-value, map-options, hasDropdownSearch,
              height='auto', minHeight='36px'
            )
          .col-auto(v-if='createInsightsPromptTemplate')
            km-btn(icon='open_in_new', flat, dense, @click='navigateToPrompt(createInsightsPromptTemplate)')
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
