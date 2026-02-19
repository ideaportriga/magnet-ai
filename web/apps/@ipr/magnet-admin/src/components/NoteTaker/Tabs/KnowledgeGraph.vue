<template lang="pug">
.full-width

  km-section(
    title='Create Knowledge Graph Embedding',
    subTitle='Select the knowledge graph to embed when enabled.'
  )
    .column.q-gap-12
      .row.items-baseline
        .col-auto.q-mr-sm
          q-toggle(v-model='createKnowledgeGraphEmbedding', color='primary', dense)
        .col Create Knowledge Graph Embedding
      .row.q-gap-8.items-end(v-if='createKnowledgeGraphEmbedding')
        .col
          .km-field.text-secondary-text.q-pb-xs.q-pl-8 Knowledge graph
          .row.items-center.q-gap-8.no-wrap
            km-select(
              v-model='knowledgeGraphSystemName',
              :options='props.knowledgeGraphs || []',
              option-label='name',
              option-value='system_name',
              emit-value,
              map-options,
              hasDropdownSearch,
              height='30px'
              placeholder='Select knowledge graph'
            )
            km-btn(
              v-if='selectedKnowledgeGraph?.id',
              icon='open_in_new',
              flat,
              dense,
              @click='router.push(`/knowledge-graph/${selectedKnowledgeGraph.id}`)'
            )
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'

const store = useStore()
const router = useRouter()

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

const props = defineProps<{ knowledgeGraphs: any[] }>()

const selectedKnowledgeGraph = computed(() => {
  return (props.knowledgeGraphs || []).find(
    (graph: any) => graph.system_name === knowledgeGraphSystemName.value
  )
})
</script>
