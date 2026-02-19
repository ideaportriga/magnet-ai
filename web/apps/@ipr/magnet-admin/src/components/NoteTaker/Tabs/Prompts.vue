<template lang="pug">
.full-width

  km-section(
    title='Post-transcription processing',
    subTitle='Prompt template to post-process the transcript (map speakers to names).'
  )
    .column.q-gap-12
      .row.items-baseline
        .col-auto.q-mr-sm
          q-toggle(v-model='postTranscriptionEnabled', color='primary', dense)
        .col Post-transcription processing
      .row.q-gap-8.q-pl-8.items-end(v-if='postTranscriptionEnabled')
        .col
          .km-field.text-secondary-text.q-pb-xs.q-pl-8 Prompt template
          .row.items-center.q-gap-8.no-wrap
            km-select(
              v-model='postTranscriptionPromptTemplate',
              :options='promptTemplates',
              option-label='name',
              option-value='system_name',
              emit-value,
              map-options,
              hasDropdownSearch,
              height='30px'
              placeholder='Select prompt template'
            )
            km-btn(
              v-if='postTranscriptionPromptTemplate',
              icon='open_in_new',
              flat,
              dense,
              @click='navigateToPrompt(postTranscriptionPromptTemplate)'
            )

  q-separator.q-my-lg

  km-section(
    title='Create Chapters',
    subTitle='Prompt template for chapters.'
  )
    .column.q-gap-12
      .row.items-baseline
        .col-auto.q-mr-sm
          q-toggle(v-model='createChaptersEnabled', color='primary', dense)
        .col Create Chapters
      .row.q-gap-8.q-pl-8.items-end(v-if='createChaptersEnabled')
        .col
          .km-field.text-secondary-text.q-pb-xs.q-pl-8 Prompt template
          .row.items-center.q-gap-8.no-wrap
            km-select(
              v-model='createChaptersPromptTemplate',
              :options='promptTemplates',
              option-label='name',
              option-value='system_name',
              emit-value,
              map-options,
              hasDropdownSearch,
              height='30px'
              placeholder='Select prompt template'
            )
            km-btn(
              v-if='createChaptersPromptTemplate',
              icon='open_in_new',
              flat,
              dense,
              @click='navigateToPrompt(createChaptersPromptTemplate)'
            )

  q-separator.q-my-lg

  km-section(
    title='Create Summary',
    subTitle='Prompt template for summary.'
  )
    .column.q-gap-12
      .row.items-baseline
        .col-auto.q-mr-sm
          q-toggle(v-model='createSummaryEnabled', color='primary', dense)
        .col Create Summary
      .row.q-gap-8.q-pl-8.items-end(v-if='createSummaryEnabled')
        .col
          .km-field.text-secondary-text.q-pb-xs.q-pl-8 Prompt template
          .row.items-center.q-gap-8.no-wrap
            km-select(
              v-model='createSummaryPromptTemplate',
              :options='promptTemplates',
              option-label='name',
              option-value='system_name',
              emit-value,
              map-options,
              hasDropdownSearch,
              height='30px'
              placeholder='Select prompt template'
            )
            km-btn(
              v-if='createSummaryPromptTemplate',
              icon='open_in_new',
              flat,
              dense,
              @click='navigateToPrompt(createSummaryPromptTemplate)'
            )

  q-separator.q-my-lg

  km-section(
    title='Create Insights',
    subTitle='Prompt template for insights.'
  )
    .column.q-gap-12
      .row.items-baseline
        .col-auto.q-mr-sm
          q-toggle(v-model='createInsightsEnabled', color='primary', dense)
        .col Create Insights
      .row.q-gap-8.q-pl-8.items-end(v-if='createInsightsEnabled')
        .col
          .km-field.text-secondary-text.q-pb-xs.q-pl-8 Prompt template
          .row.items-center.q-gap-8.no-wrap
            km-select(
              v-model='createInsightsPromptTemplate',
              :options='promptTemplates',
              option-label='name',
              option-value='system_name',
              emit-value,
              map-options,
              hasDropdownSearch,
              height='30px'
              placeholder='Select prompt template'
            )
            km-btn(
              v-if='createInsightsPromptTemplate',
              icon='open_in_new',
              flat,
              dense,
              @click='navigateToPrompt(createInsightsPromptTemplate)'
            )
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'

const store = useStore()
const router = useRouter()

const promptTemplates = computed(() => {
  return store.getters['chroma/promptTemplates']?.items || []
})

const postTranscriptionEnabled = computed({
  get: () => store.getters.noteTakerSettings?.post_transcription?.enabled ?? false,
  set: (value: boolean) => {
    store.dispatch('updateNoteTakerSetting', { path: 'post_transcription.enabled', value })
  },
})

const postTranscriptionPromptTemplate = computed({
  get: () => store.getters.noteTakerSettings?.post_transcription?.prompt_template || '',
  set: (value: string) => {
    store.dispatch('updateNoteTakerSetting', { path: 'post_transcription.prompt_template', value })
  },
})

const createChaptersEnabled = computed({
  get: () => store.getters.noteTakerSettings?.chapters?.enabled ?? false,
  set: (value: boolean) => {
    store.dispatch('updateNoteTakerSetting', { path: 'chapters.enabled', value })
  },
})

const createChaptersPromptTemplate = computed({
  get: () => store.getters.noteTakerSettings?.chapters?.prompt_template || '',
  set: (value: string) => {
    store.dispatch('updateNoteTakerSetting', { path: 'chapters.prompt_template', value })
  },
})

const createSummaryEnabled = computed({
  get: () => store.getters.noteTakerSettings?.summary?.enabled ?? false,
  set: (value: boolean) => {
    store.dispatch('updateNoteTakerSetting', { path: 'summary.enabled', value })
  },
})

const createSummaryPromptTemplate = computed({
  get: () => store.getters.noteTakerSettings?.summary?.prompt_template || '',
  set: (value: string) => {
    store.dispatch('updateNoteTakerSetting', { path: 'summary.prompt_template', value })
  },
})

const createInsightsEnabled = computed({
  get: () => store.getters.noteTakerSettings?.insights?.enabled ?? false,
  set: (value: boolean) => {
    store.dispatch('updateNoteTakerSetting', { path: 'insights.enabled', value })
  },
})

const createInsightsPromptTemplate = computed({
  get: () => store.getters.noteTakerSettings?.insights?.prompt_template || '',
  set: (value: string) => {
    store.dispatch('updateNoteTakerSetting', { path: 'insights.prompt_template', value })
  },
})

const navigateToPrompt = (systemName: string) => {
  const prompt = promptTemplates.value.find((p: any) => p.system_name === systemName)
  if (prompt) {
    window.open(router.resolve({ path: `/prompt-templates/${prompt.id}` }).href, '_blank')
  }
}
</script>
