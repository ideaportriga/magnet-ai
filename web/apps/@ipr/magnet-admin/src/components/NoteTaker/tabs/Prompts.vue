<template>
  <div class="stack" data-gap="md">
    <div class="km-field">
      <div class="cluster" data-justify="between">
        <div class="text-secondary-text pb-xs km-title">Post-transcription processing</div>
        <km-toggle v-model="postTranscriptionEnabled" />
      </div>
      <div v-if="postTranscriptionEnabled" class="gap-sm">
        <div class="cluster" data-gap="sm">
          <div class="flex-1">
            <km-select v-model="postTranscriptionPromptTemplate" :options="promptTemplates" option-label="name" option-value="system_name" emit-value map-options has-dropdown-search height="30px" />
          </div>
          <div v-if="postTranscriptionPromptTemplate" class="flex-none">
            <km-btn icon="external-link" flat dense @click="navigateToPrompt(postTranscriptionPromptTemplate)" />
          </div>
        </div>
      </div>
      <div v-if="postTranscriptionEnabled" class="km-description text-secondary-text pt-2xs">Prompt template to post-process the transcript (map speakers to names).</div>
    </div>
    <div class="km-field">
      <div class="cluster" data-justify="between">
        <div class="text-secondary-text pb-xs km-title">Create Chapters</div>
        <km-toggle v-model="createChaptersEnabled" />
      </div>
      <div v-if="createChaptersEnabled" class="gap-sm">
        <div class="cluster" data-gap="sm">
          <div class="flex-1">
            <km-select v-model="createChaptersPromptTemplate" :options="promptTemplates" option-label="name" option-value="system_name" emit-value map-options has-dropdown-search height="30px" />
          </div>
          <div v-if="createChaptersPromptTemplate" class="flex-none">
            <km-btn icon="external-link" flat dense @click="navigateToPrompt(createChaptersPromptTemplate)" />
          </div>
        </div>
      </div>
      <div v-if="createChaptersEnabled" class="km-description text-secondary-text pt-2xs">Prompt template for chapters.</div>
    </div>
    <div class="km-field">
      <div class="cluster" data-justify="between">
        <div class="text-secondary-text pb-xs km-title">Create Summary</div>
        <km-toggle v-model="createSummaryEnabled" />
      </div>
      <div v-if="createSummaryEnabled" class="gap-sm">
        <div class="cluster" data-gap="sm">
          <div class="flex-1">
            <km-select v-model="createSummaryPromptTemplate" :options="promptTemplates" option-label="name" option-value="system_name" emit-value map-options has-dropdown-search height="30px" />
          </div>
          <div v-if="createSummaryPromptTemplate" class="flex-none">
            <km-btn icon="external-link" flat dense @click="navigateToPrompt(createSummaryPromptTemplate)" />
          </div>
        </div>
      </div>
      <div v-if="createSummaryEnabled" class="km-description text-secondary-text pt-2xs">Prompt template for summary.</div>
    </div>
    <div class="km-field">
      <div class="cluster" data-justify="between">
        <div class="text-secondary-text pb-xs km-title">Create Insights</div>
        <km-toggle v-model="createInsightsEnabled" />
      </div>
      <div v-if="createInsightsEnabled" class="gap-sm">
        <div class="cluster" data-gap="sm">
          <div class="flex-1">
            <km-select v-model="createInsightsPromptTemplate" :options="promptTemplates" option-label="name" option-value="system_name" emit-value map-options has-dropdown-search height="30px" />
          </div>
          <div v-if="createInsightsPromptTemplate" class="flex-none">
            <km-btn icon="external-link" flat dense @click="navigateToPrompt(createInsightsPromptTemplate)" />
          </div>
        </div>
      </div>
      <div v-if="createInsightsEnabled" class="km-description text-secondary-text pt-2xs">Prompt template for insights.</div>
    </div>
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
