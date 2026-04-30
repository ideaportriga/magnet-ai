<template>
  <div>
    <km-section title="Transcript Enhancement" sub-title="Enable speaker mapping and transcript improvement">
      <div class="cluster" data-justify="between">
        <div class="km-field text-secondary-text pl-sm">Transcript Enhancement</div>
        <km-toggle v-model="postTranscriptionEnabled" />
      </div>
      <div class="km-description text-secondary-text pt-xs pl-sm">Highly recommended to keep enabled, because this feature drives speaker mapping</div>
      <template v-if="postTranscriptionEnabled">
        <div class="mt-md">
          <div class="km-field text-secondary-text pb-xs pl-sm">Transcript Enhancement Prompt</div>
          <div class="cluster" data-gap="sm">
            <div class="flex-1">
              <km-select v-model="postTranscriptionPromptTemplate" :options="promptTemplates" option-label="name" option-value="system_name" emit-value map-options has-dropdown-search height="auto" min-height="36px" />
            </div>
            <div v-if="postTranscriptionPromptTemplate" class="flex-none">
              <km-btn icon="external-link" flat dense @click="navigateToPrompt(postTranscriptionPromptTemplate)" />
            </div>
          </div>
        </div>
      </template>
    </km-section>
    <km-separator class="my-lg" />
    <km-section title="Summarization" sub-title="Enable output summarization at different level of detail">
      <div class="cluster" data-justify="between">
        <div class="km-field text-secondary-text pl-sm">Chapters</div>
        <km-toggle v-model="createChaptersEnabled" />
      </div>
      <div class="km-description text-secondary-text pt-xs pl-sm">Chapters are a more readable version of original transcript</div>
      <template v-if="createChaptersEnabled">
        <div class="mt-md">
          <div class="km-field text-secondary-text pb-xs pl-sm">Chapters Prompt Template</div>
          <div class="cluster" data-gap="sm">
            <div class="flex-1">
              <km-select v-model="createChaptersPromptTemplate" :options="promptTemplates" option-label="name" option-value="system_name" emit-value map-options has-dropdown-search height="auto" min-height="36px" />
            </div>
            <div v-if="createChaptersPromptTemplate" class="flex-none">
              <km-btn icon="external-link" flat dense @click="navigateToPrompt(createChaptersPromptTemplate)" />
            </div>
          </div>
        </div>
      </template>
      <km-separator class="my-lg" />
      <div class="cluster" data-justify="between">
        <div class="km-field text-secondary-text pl-sm">Summary</div>
        <km-toggle v-model="createSummaryEnabled" />
      </div>
      <div class="km-description text-secondary-text pt-xs pl-sm">Summary is transcript processed according to your template</div>
      <template v-if="createSummaryEnabled">
        <div class="mt-md">
          <div class="km-field text-secondary-text pb-xs pl-sm">Summary Prompt Template</div>
          <div class="cluster" data-gap="sm">
            <div class="flex-1">
              <km-select v-model="createSummaryPromptTemplate" :options="promptTemplates" option-label="name" option-value="system_name" emit-value map-options has-dropdown-search height="auto" min-height="36px" />
            </div>
            <div v-if="createSummaryPromptTemplate" class="flex-none">
              <km-btn icon="external-link" flat dense @click="navigateToPrompt(createSummaryPromptTemplate)" />
            </div>
          </div>
        </div>
      </template>
      <km-separator class="my-lg" />
      <div class="cluster" data-justify="between">
        <div class="km-field text-secondary-text pl-sm">Insights</div>
        <km-toggle v-model="createInsightsEnabled" />
      </div>
      <div class="km-description text-secondary-text pt-xs pl-sm">Insights are key items extracted from the transcript - e.g. to-do items, contacts, tasks etc</div>
      <template v-if="createInsightsEnabled">
        <div class="mt-md">
          <div class="km-field text-secondary-text pb-xs pl-sm">Insights Prompt Template</div>
          <div class="cluster" data-gap="sm">
            <div class="flex-1">
              <km-select v-model="createInsightsPromptTemplate" :options="promptTemplates" option-label="name" option-value="system_name" emit-value map-options has-dropdown-search height="auto" min-height="36px" />
            </div>
            <div v-if="createInsightsPromptTemplate" class="flex-none">
              <km-btn icon="external-link" flat dense @click="navigateToPrompt(createInsightsPromptTemplate)" />
            </div>
          </div>
        </div>
      </template>
    </km-section>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { m } from '@/paraglide/messages'
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
  if (prompt) router.push(`/prompt-templates/${prompt.id}`)
}
</script>
