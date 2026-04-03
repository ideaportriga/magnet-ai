<template lang="pug">
div
  km-section(title='Embed into Knowledge Graph', subTitle='Embed Note Taker output to a Knowledge Graph for further semantic search')
    .row.items-center.justify-between
      .km-field.text-secondary-text.q-pl-8 Embed into Knowledge Graph
      q-toggle(v-model='createKnowledgeGraphEmbedding', color='primary')
    template(v-if='createKnowledgeGraphEmbedding')
      .q-mt-md
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Knowledge Graph
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
              height='auto',
              minHeight='36px'
            )
          .col-auto(v-if='selectedKnowledgeGraph?.id')
            km-btn(
              icon='open_in_new',
              flat,
              dense,
              @click='router.push(`/knowledge-graph/${selectedKnowledgeGraph.id}`)'
            )
        .km-description.text-secondary-text.q-pt-xs.q-pl-8 Select the knowledge graph to embed when enabled.
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

const knowledgeGraphs = ref<any[]>([])

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

watch(apiReady, (ready) => {
  if (ready) fetchKnowledgeGraphs()
}, { immediate: true })
</script>
