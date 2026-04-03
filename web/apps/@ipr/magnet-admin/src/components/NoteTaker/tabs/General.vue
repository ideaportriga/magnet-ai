<template lang="pug">
.q-gutter-md
  .km-field
    .row.items-center.justify-between
      .text-secondary-text.q-pb-xs.km-title Set the subscription for recordings ready
      q-toggle(v-model='subscriptionRecordingsReady', color='primary')
    .km-description.text-secondary-text.q-pt-2 Automatically create recordings-ready subscriptions for meetings.

  .km-field
    .text-secondary-text.q-pb-xs.km-title Transcription model
    km-select(
      v-model='pipelineId',
      :options='pipelineOptions',
      option-label='label',
      option-value='value',
      emit-value,
      map-options,
      height='30px'
    )
    .km-description.text-secondary-text.q-pt-2 STT model system name. Empty = transcription service default.

  .km-field
    .row.items-center.justify-between
      .text-secondary-text.q-pb-xs.km-title Send number of speakers
      q-toggle(v-model='sendNumberOfSpeakers', color='primary')
    .km-description.text-secondary-text.q-pt-2 When enabled, Note Taker sends the invited participants count to the transcription backend (e.g. ElevenLabs num_speakers).

  .km-field
    .text-secondary-text.q-pb-xs.km-title Keyterms
    km-input.full-width(
      type='textarea',
      autogrow,
      placeholder='e.g. project names, one per line',
      v-model='keyterms'
    )
    .km-description.text-secondary-text.q-pt-2 Optional keyterms to improve the transcription accuracy (one per line).

  q-separator

  .km-heading-8 Knowledge Graph
  .km-field
    .row.items-center.justify-between
      .text-secondary-text.q-pb-xs.km-title Create Knowledge Graph Embedding
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
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { m } from '@/paraglide/messages'
import { useAppStore } from '@/stores/appStore'
import { useNoteTakerStore } from '@/stores/noteTakerStore'
import { useRouter } from 'vue-router'
import { fetchData } from '@shared'

const ntStore = useNoteTakerStore()
const appStore = useAppStore()
const router = useRouter()

const pipelineOptions = ref<{ label: string; value: string }[]>([
  { label: 'Default (auto)', value: '' },
])

const knowledgeGraphs = ref<any[]>([])

const subscriptionRecordingsReady = computed({
  get: () => ntStore.settings?.subscription_recordings_ready ?? false,
  set: (v: boolean) => ntStore.updateSetting( { path: 'subscription_recordings_ready', value: v }),
})
const pipelineId = computed({
  get: () => ntStore.settings?.pipeline_id ?? '',
  set: (v: string) => ntStore.updateSetting( { path: 'pipeline_id', value: v }),
})
const sendNumberOfSpeakers = computed({
  get: () => ntStore.settings?.send_number_of_speakers ?? false,
  set: (v: boolean) => ntStore.updateSetting( { path: 'send_number_of_speakers', value: v }),
})
const keyterms = computed({
  get: () => ntStore.settings?.keyterms || '',
  set: (v: string) => ntStore.updateSetting( { path: 'keyterms', value: v }),
})
const createKnowledgeGraphEmbedding = computed({
  get: () => ntStore.settings?.create_knowledge_graph_embedding ?? false,
  set: (v: boolean) => ntStore.updateSetting( { path: 'create_knowledge_graph_embedding', value: v }),
})
const knowledgeGraphSystemName = computed({
  get: () => ntStore.settings?.knowledge_graph_system_name || '',
  set: (v: string) => ntStore.updateSetting( { path: 'knowledge_graph_system_name', value: v }),
})
const selectedKnowledgeGraph = computed(() =>
  knowledgeGraphs.value.find((g: any) => g.system_name === knowledgeGraphSystemName.value)
)

const apiReady = computed(() => Boolean(appStore.config?.api?.aiBridge?.urlAdmin))

const fetchKnowledgeGraphs = async () => {
  const endpoint = appStore.config?.api?.aiBridge?.urlAdmin
  if (!endpoint) return
  try {
    const response = await fetchData({
      method: 'GET', endpoint, service: 'knowledge_graphs/',
      credentials: 'include', headers: { Accept: 'application/json' },
    })
    if (!response?.ok) return
    const data = await response.json()
    knowledgeGraphs.value = Array.isArray(data) ? data : (data?.items || data?.data || [])
  } catch { /* ignore */ }
}

const fetchSttModels = async () => {
  const endpoint = appStore.config?.api?.aiBridge?.urlAdmin
  if (!endpoint) return
  try {
    const response = await fetchData({
      method: 'GET', endpoint, service: 'models/?type=stt&pagination_size=100',
      credentials: 'include', headers: { Accept: 'application/json' },
    })
    if (!response?.ok) return
    const data = await response.json()
    const items: any[] = Array.isArray(data) ? data : (data?.items || data?.data || [])
    if (items.length > 0) {
      pipelineOptions.value = [
        { label: 'Default (auto)', value: '' },
        ...items.map((m: any) => ({ label: m.name || m.system_name, value: m.system_name })),
      ]
    }
  } catch { /* ignore */ }
}

watch(apiReady, (ready) => {
  if (ready) {
    fetchKnowledgeGraphs()
    fetchSttModels()
  }
}, { immediate: true })
</script>
