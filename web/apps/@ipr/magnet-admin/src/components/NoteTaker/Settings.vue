<template lang="pug">
.row.no-wrap.overflow-hidden.full-height(v-if='loading', style='min-width: 1200px')
  q-inner-loading(:showing='loading')
    q-spinner-gears(size='50px', color='primary')
.row.no-wrap.overflow-hidden.full-height(v-else)
  q-scroll-area.fit
    .row.no-wrap.full-height.justify-center.fit
      .col(style='max-width: 1200px; min-width: 600px')
        .full-height.q-pb-md.relative-position.q-px-md
          .row.items-center.q-gap-12.no-wrap.full-width.q-mt-lg.q-mb-sm.bg-white.border-radius-8.q-py-12.q-px-16
            .col
              .row.items-center
                .col
                  km-input-flat.km-heading-4.full-width.text-black(
                    placeholder='Name',
                    :modelValue='recordName',
                    @input='recordName = $event'
                  )
              .row.items-center.q-mt-sm
                .col
                  km-input-flat.km-description.full-width.text-black(
                    placeholder='Description',
                    :modelValue='recordDescription',
                    @input='recordDescription = $event'
                  )
              .row.items-center.q-pl-6.q-mt-sm
                q-icon.col-auto(name='o_info', color='text-secondary')
                  q-tooltip.bg-white.block-shadow.text-black.km-description(self='top middle', :offset='[-50, -50]') System name serves as unique record id
                .col
                  km-input-flat.km-description.full-width(
                    placeholder='Enter system name',
                    :modelValue='recordSystemName',
                    @input='recordSystemName = $event'
                  )
          .ba-border.bg-white.border-radius-12.q-pa-16.q-my-16
            .column.no-wrap.q-gap-24.full-height.full-width
              .col-auto.full-width
                .km-heading-6.q-mb-md General Settings
                .q-gutter-md
                  .km-field.q-mt-lg
                    .text-secondary-text.q-pb-xs.km-title Set the subscription for recordings ready
                    q-toggle(v-model='subscriptionRecordingsReady', color='primary')
                    .km-description.text-secondary-text.q-pt-2 Automatically create recordings-ready subscriptions for meetings.

              q-separator

              .col-auto.full-width
                .km-heading-6.q-mb-md Prompts
                .q-gutter-md
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
                            emit-value,
                            map-options,
                            hasDropdownSearch,
                            height='30px'
                          )
                        .col-auto(v-if='createChaptersPromptTemplate')
                          km-btn(
                            icon='open_in_new',
                            flat,
                            dense,
                            @click='navigateToPrompt(createChaptersPromptTemplate)'
                          )
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
                            emit-value,
                            map-options,
                            hasDropdownSearch,
                            height='30px'
                          )
                        .col-auto(v-if='createSummaryPromptTemplate')
                          km-btn(
                            icon='open_in_new',
                            flat,
                            dense,
                            @click='navigateToPrompt(createSummaryPromptTemplate)'
                          )
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
                            emit-value,
                            map-options,
                            hasDropdownSearch,
                            height='30px'
                          )
                        .col-auto(v-if='createInsightsPromptTemplate')
                          km-btn(
                            icon='open_in_new',
                            flat,
                            dense,
                            @click='navigateToPrompt(createInsightsPromptTemplate)'
                          )
                    .km-description.text-secondary-text.q-pt-2(v-if='createInsightsEnabled') Prompt template for insights.

                  q-separator

                  .km-heading-6 Knowledge Graph

                  .km-field
                    .row.items-center.justify-between
                      .text-secondary-text.q-pb-xs.km-heading-8 Create Knowledge Graph Embedding
                      q-toggle(v-model='createKnowledgeGraphEmbedding', color='primary')
                    .q-gutter-sm(v-if='createKnowledgeGraphEmbedding')
                      .row.items-center.q-gutter-sm
                        .col
                          km-select(
                            v-model='knowledgeGraphSystemName',
                            :options='knowledgeGraphs',
                            option-label='name',
                            option-value='system_name',
                            emit-value,
                            map-options,
                            hasDropdownSearch,
                            height='30px'
                          )
                        .col-auto(v-if='selectedKnowledgeGraph?.id')
                          km-btn(
                            icon='open_in_new',
                            flat,
                            dense,
                            @click='router.push(`/knowledge-graph/${selectedKnowledgeGraph.id}`)'
                          )
                    .km-description.text-secondary-text.q-pt-2(v-if='createKnowledgeGraphEmbedding') Select the knowledge graph to embed when enabled.

              q-separator

              .col-auto.full-width
                .km-heading-6.q-mb-md Salesforce Integration
                .q-gutter-md
                  .km-field
                    .row.items-center.justify-between
                      .text-secondary-text.q-pb-xs.km-title Send transcript to Salesforce
                      q-toggle(v-model='sendTranscriptToSalesforce', color='primary')
                    .km-description.text-secondary-text.q-pt-2 Push completed transcripts to Salesforce.

                  .q-gutter-md(v-if='sendTranscriptToSalesforce')
                    .km-field
                      .text-secondary-text.q-pb-xs API Server
                      .row.items-center.q-gutter-sm
                        .col
                          km-select(
                            v-model='salesforceApiServer',
                            :options='apiServers',
                            option-label='name',
                            option-value='system_name',
                            emit-value,
                            map-options,
                            height='30px',
                            clearable
                          )
                        .col-auto(v-if='salesforceApiServer')
                          km-btn(
                            icon='open_in_new',
                            flat,
                            dense,
                            @click='navigateToApiServer(salesforceApiServer)'
                          )
                      .km-description.text-secondary-text.q-pt-2 API server for Salesforce tool calls.

                    .km-field
                      .text-secondary-text.q-pb-xs STT Recording Tool
                      .row.items-center.q-gutter-sm
                        .col
                          km-select(
                            v-model='salesforceSttRecordingTool',
                            :options='availableTools',
                            option-label='label',
                            option-value='value',
                            emit-value,
                            map-options,
                            height='30px',
                            clearable
                          )
                        .col-auto(v-if='salesforceSttRecordingTool')
                          km-btn(
                            icon='open_in_new',
                            flat,
                            dense,
                            @click='navigateToTool(salesforceApiServer, salesforceSttRecordingTool)'
                          )
                      .km-description.text-secondary-text.q-pt-2 Tool for creating STT recordings in Salesforce.
</template>

<script setup lang="ts">
import { computed, watch, ref, onMounted } from 'vue'
import { useStore } from 'vuex'
import { useRouter, useRoute } from 'vue-router'
import { fetchData } from '@shared'

const store = useStore()
const router = useRouter()
const route = useRoute()

const knowledgeGraphs = ref<any[]>([])

const promptTemplates = computed(() => {
  return store.getters['chroma/promptTemplates']?.items || []
})

const configId = computed(() => route.params.id as string)
const activeRecord = computed(() => store.getters.noteTakerSettingsActiveRecord)
const loading = computed(() => store.getters.noteTakerLoading || !activeRecord.value)

const recordName = computed({
  get: () => activeRecord.value?.name || '',
  set: (value: string) => {
    store.dispatch('updateNoteTakerRecordMeta', { name: value })
  },
})

const recordDescription = computed({
  get: () => activeRecord.value?.description || '',
  set: (value: string) => {
    store.dispatch('updateNoteTakerRecordMeta', { description: value })
  },
})

const recordSystemName = computed({
  get: () => activeRecord.value?.system_name || '',
  set: (value: string) => {
    store.dispatch('updateNoteTakerRecordMeta', { system_name: value })
  },
})

const subscriptionRecordingsReady = computed({
  get: () => store.getters.noteTakerSettings?.subscription_recordings_ready ?? false,
  set: (value: boolean) => {
    store.dispatch('updateNoteTakerSetting', { path: 'subscription_recordings_ready', value })
  },
})

const sendTranscriptToSalesforce = computed({
  get: () => store.getters.noteTakerSettings?.integration?.salesforce?.send_transcript_to_salesforce ?? false,
  set: (value: boolean) => {
    store.dispatch('updateNoteTakerSetting', { path: 'integration.salesforce.send_transcript_to_salesforce', value })
  },
})

const salesforceApiServer = computed({
  get: () => store.getters.noteTakerSettings?.integration?.salesforce?.salesforce_api_server || '',
  set: (value: string) => {
    store.dispatch('updateNoteTakerSetting', { path: 'integration.salesforce.salesforce_api_server', value })
  },
})

const salesforceSttRecordingTool = computed({
  get: () => store.getters.noteTakerSettings?.integration?.salesforce?.salesforce_stt_recording_tool || '',
  set: (value: string) => {
    store.dispatch('updateNoteTakerSetting', { path: 'integration.salesforce.salesforce_stt_recording_tool', value })
  },
})

const createKnowledgeGraphEmbedding = computed({
  get: () => store.getters.noteTakerSettings?.create_knowledge_graph_embedding ?? false,
  set: (value: boolean) => {
    store.dispatch('updateNoteTakerSetting', { path: 'create_knowledge_graph_embedding', value })
  },
})

const knowledgeGraphSystemName = computed({
  get: () => store.getters.noteTakerSettings?.knowledge_graph_system_name || '',
  set: (value: string) => {
    store.dispatch('updateNoteTakerSetting', { path: 'knowledge_graph_system_name', value })
  },
})

const selectedKnowledgeGraph = computed(() => {
  return knowledgeGraphs.value.find((graph: any) => graph.system_name === knowledgeGraphSystemName.value)
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

const apiReady = computed(() => Boolean(store.getters.config?.api?.aiBridge?.urlAdmin))
const apiServers = computed(() => {
  return store.getters['chroma/api_servers']?.items || []
})

const loadRecord = async () => {
  if (!configId.value || !apiReady.value) return
  const record = await store.dispatch('fetchNoteTakerSettingsById', configId.value)
  if (!record) {
    router.push('/note-taker')
  }
}

const availableTools = computed(() => {
  const serverName = salesforceApiServer.value
  if (!serverName) return []
  const server = apiServers.value.find((s: any) => s.system_name === serverName)
  return server?.tools?.map((t: any) => ({
    label: t.name,
    value: t.system_name,
  })) || []
})

const fetchKnowledgeGraphs = async () => {
  const endpoint = store.getters.config?.api?.aiBridge?.urlAdmin
  if (!endpoint) return

  try {
    const response = await fetchData({
      method: 'GET',
      endpoint,
      service: 'knowledge_graphs/',
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    })
    if (!response?.ok) {
      console.error('Failed to fetch knowledge graphs:', response?.error)
      return
    }
    const data = await response.json()
    knowledgeGraphs.value = Array.isArray(data) ? data : (data?.items || data?.data || [])
  } catch (error) {
    console.error('Error fetching knowledge graphs:', error)
  }
}

watch(
  apiReady,
  (ready) => {
    if (!ready) return
    if (!store.getters['chroma/promptTemplates']?.items?.length) {
      store.dispatch('chroma/get', { entity: 'promptTemplates' })
    }
    if (!store.getters['chroma/api_servers']?.items?.length) {
      store.dispatch('chroma/get', { entity: 'api_servers' })
    }
    fetchKnowledgeGraphs()
    loadRecord()
  },
  { immediate: true }
)

watch(
  () => configId.value,
  () => {
    loadRecord()
  }
)

const navigateToPrompt = (systemName: string) => {
  const prompt = promptTemplates.value.find((p: any) => p.system_name === systemName)
  if (prompt) {
    window.open(router.resolve({ path: `/prompt-templates/${prompt.id}` }).href, '_blank')
  }
}

const navigateToApiServer = (systemName: string) => {
  const server = apiServers.value.find((s: any) => s.system_name === systemName)
  if (server) {
    window.open(router.resolve({ path: `/api-servers/${server.id}` }).href, '_blank')
  }
}

const navigateToTool = (serverSystemName: string, toolName: string) => {
  const server = apiServers.value.find((s: any) => s.system_name === serverSystemName)
  if (server) {
    window.open(
      router.resolve({ path: `/api-servers/${server.id}/tools/${toolName}` }).href,
      '_blank'
    )
  }
}
</script>
