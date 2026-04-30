<template>
  <div>
    <km-section title="Embed into Knowledge Graph" sub-title="Embed Note Taker output to a Knowledge Graph for further semantic search">
      <div class="cluster" data-justify="between">
        <div class="km-field text-secondary-text pl-sm">Embed into Knowledge Graph</div>
        <km-toggle v-model="createKnowledgeGraphEmbedding" />
      </div>
      <template v-if="createKnowledgeGraphEmbedding">
        <div class="mt-md">
          <div class="km-field text-secondary-text pb-xs pl-sm">Knowledge Graph</div>
          <div class="cluster" data-gap="sm">
            <div class="flex-1">
              <km-select v-model="knowledgeGraphSystemName" :options="knowledgeGraphs" option-label="name" option-value="system_name" emit-value map-options has-dropdown-search height="auto" min-height="36px" />
            </div>
            <div v-if="selectedKnowledgeGraph?.id" class="flex-none">
              <km-btn icon="external-link" flat dense @click="router.push(`/knowledge-graph/${selectedKnowledgeGraph.id}`)" />
            </div>
          </div>
          <div class="km-description text-secondary-text pt-xs pl-sm">Select the knowledge graph to embed when enabled.</div>
        </div>
      </template>
    </km-section>
  </div>
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
