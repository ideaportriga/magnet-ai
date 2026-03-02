<template lang="pug">
.row.no-wrap.overflow-hidden.full-height(v-if='loading', style='min-width: 1200px')
  q-inner-loading(:showing='loading')
    q-spinner-gears(size='50px', color='primary')
layouts-details-layout(
  v-else,
  v-model:name='recordName',
  v-model:description='recordDescription',
  v-model:systemName='recordSystemName',
  :contentContainerStyle='{ maxWidth: "1200px", minWidth: "600px", margin: "0 auto" }'
).full-width
  template(#content)
    q-tabs.bb-border.full-width(
      v-model='tab',
      narrow-indicator,
      dense,
      align='left',
      active-color='primary',
      indicator-color='primary',
      active-bg-color='white',
      no-caps,
      content-class='km-tabs'
    )
      template(v-for='t in tabs')
        q-tab(:name='t.name', :label='t.label')
    .column.no-wrap.q-gap-16.full-height.full-width.overflow-auto.q-pt-lg.q-pb-lg(style='max-height: calc(100vh - 300px) !important')
      .row.q-gap-16.full-height.full-width
        .col.full-height.full-width
          .column.full-height.full-width.q-gap-16.overflow-auto.no-wrap
            note-taker-tabs-general-settings(v-if='tab === "general"')
            note-taker-tabs-prompts(v-if='tab === "prompts"')
            note-taker-tabs-integration(v-if='tab === "integration"')
            note-taker-tabs-knowledge-graph(
              v-if='tab === "knowledge_graph"',
              :knowledge-graphs='knowledgeGraphs'
            )

  template(#drawer)
    note-taker-drawer
</template>

<script setup lang="ts">
import { computed, watch, ref } from 'vue'
import { useStore } from 'vuex'
import { useRouter, useRoute } from 'vue-router'
import { fetchData } from '@shared'

const store = useStore()
const router = useRouter()
const route = useRoute()

const knowledgeGraphs = ref<any[]>([])

const configId = computed(() => route.params.id as string)
const activeRecord = computed(() => store.getters.noteTakerSettingsActiveRecord)
const loading = computed(() => store.getters.noteTakerLoading || !activeRecord.value)

const tab = ref('general')
const tabs = [
  { name: 'general', label: 'General Settings' },
  { name: 'prompts', label: 'Prompts' },
  { name: 'integration', label: 'Integration' },
  { name: 'knowledge_graph', label: 'Knowledge Graph' },
]

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

const apiReady = computed(() => Boolean(store.getters.config?.api?.aiBridge?.urlAdmin))

const loadRecord = async () => {
  if (!configId.value || !apiReady.value) return
  const record = await store.dispatch('fetchNoteTakerSettingsById', configId.value)
  if (!record) {
    router.push('/note-taker')
  }
}

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
</script>
