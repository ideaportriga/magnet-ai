<template>
  <div class="row no-wrap overflow-hidden full-height">
    <div class="row no-wrap full-height justify-center fit">
      <div class="col-auto full-width">
        <div class="column no-wrap full-height q-pb-md relative-position q-px-md">
          <div class="col-auto column full-width q-mt-lg q-mb-sm bg-white border-radius-8">
            <div class="row items-center no-wrap full-width q-py-12 q-px-16">
              <q-btn flat dense round icon="arrow_back" class="q-mr-sm" @click="goBack">
                <q-tooltip>Back to Explorer</q-tooltip>
              </q-btn>
              <div class="col">
                <div class="row items-center no-wrap" style="height: 32px">
                  <div class="km-heading-4 text-black q-mr-md">{{ document?.title || document?.name || 'Document' }}</div>
                  <kg-file-type-badge v-if="document?.type" :type="document.type" class="q-mx-xs" />
                  <q-chip dense outline square color="grey-7" icon="menu_book" class="q-ml-sm q-px-md q-py-12" style="font-size: 12px">
                    {{ document?.total_pages || 0 }} pages
                  </q-chip>
                  <q-chip dense outline square color="grey-7" icon="splitscreen" class="q-ml-sm q-px-md q-py-12" style="font-size: 12px">
                    {{ document?.chunks_count || chunks.length }} chunks
                  </q-chip>
                </div>
                <div class="km-description text-secondary-text q-mt-xs">
                  {{ document.name }}
                </div>
              </div>
              <div class="col-auto row items-center q-gutter-sm">
                <q-btn
                  v-if="document?.summary"
                  flat
                  dense
                  round
                  :icon="summaryExpanded ? 'expand_less' : 'expand_more'"
                  color="primary"
                  @click="summaryExpanded = !summaryExpanded"
                >
                  <q-tooltip>{{ summaryExpanded ? 'Hide Summary' : 'Show Summary' }}</q-tooltip>
                </q-btn>
              </div>
            </div>

            <!-- Expandable Summary Section -->
            <div v-if="summaryExpanded && document?.summary" class="q-px-16 q-pb-md">
              <q-separator class="q-mb-md" />
              <div class="km-heading-8 text-weight-medium q-mb-sm q-pl-md">Summary</div>
              <div class="text-body2 text-grey-8 q-pl-md" style="line-height: 1.65; white-space: pre-wrap; max-height: 300px; overflow-y: auto">
                {{ document.summary }}
              </div>
            </div>
          </div>

          <div class="col column no-wrap ba-border bg-white border-radius-12 q-px-32 q-py-24" style="min-width: 300px">
            <div class="row items-center q-mb-sm">
              <div class="col">
                <div class="km-heading-7">Table of Contents</div>
                <div class="km-description text-secondary-text">Navigate the structure and sections of selected document</div>
              </div>
              <div class="col-auto row items-center q-gutter-md">
                <km-btn
                  v-if="treeNodes.length > 0"
                  flat
                  color="primary"
                  :label="isAllExpanded ? 'Collapse all' : 'Expand all'"
                  @click="toggleExpandCollapseAll"
                />
                <km-input v-model="treeFilter" placeholder="Filter sections or chunks" icon-before="search" clearable style="width: 250px" />
              </div>
            </div>
            <q-separator class="q-mt-sm" />

            <div v-if="!loading && treeNodes.length === 0" class="q-mt-md">
              <div class="text-center q-pa-lg">
                <q-icon name="article" size="64px" color="grey-5" />
                <div class="km-heading-7 text-grey-7 q-mt-md">No content found</div>
                <div class="km-description text-grey-6">This document has no TOC or chunks yet</div>
              </div>
            </div>
            <q-linear-progress v-if="loading" indeterminate color="primary" />

            <div v-else-if="!loading" class="q-mt-md q-pb-md" style="flex: 1; overflow: auto">
              <q-tree
                v-model:expanded="expandedKeys"
                v-model:selected="selectedKey"
                :nodes="treeNodes"
                node-key="id"
                :filter="treeFilter"
                :filter-method="filterMethod"
                no-selection-unset
                no-transition
                no-connectors
                selected-color="primary"
                dense
              >
                <template #default-header="prop">
                  <div class="row items-center no-wrap full-width q-pa-xs" @click.stop="onTreeNodeClick(prop.node.id)">
                    <q-icon :name="getIconForNode(prop.node)" size="20px" class="q-mr-sm text-grey-7" />
                    <div class="text-body2 q-mr-md">{{ prop.node.label }}</div>
                    <template v-if="prop.node.type === 'chunk'">
                      <q-badge v-if="prop.node.chunk?.page" color="secondary" text-color="white" outline class="q-py-4">
                        page {{ prop.node.chunk?.page }}
                      </q-badge>
                    </template>
                  </div>
                </template>
              </q-tree>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-if="drawerOpen && selectedChunk" class="col-auto">
      <chunk-drawer :chunk="selectedChunk" @close="drawerOpen = false" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { fetchData } from '@shared'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStore } from 'vuex'
import ChunkDrawer from './ChunkDrawer.vue'
import { KgFileTypeBadge } from '../common'
import { Chunk, Document, TocNode, TreeNode } from './models'

const route = useRoute()
const router = useRouter()
const store = useStore()

const graphId = computed(() => route.params.id as string)
const documentId = computed(() => route.params.documentId as string)

const document = ref<Document | null>(null)
const chunks = ref<Chunk[]>([])
const loading = ref(true)
const loadingDocument = ref(false)
const drawerOpen = ref(false)
const selectedChunk = ref<Chunk | null>(null)
const summaryExpanded = ref(false)

// Tree state
const expandedKeys = ref<string[]>([])
const selectedKey = ref<string>('')
const treeFilter = ref('')
// lookup map not required; we toggle by id only

// Build tree nodes from document TOC and link chunks via toc_reference
const treeNodes = computed<TreeNode[]>(() => {
  const docToc = (document.value?.toc || []) as TocNode[]
  const nodes: TreeNode[] = []
  const idMap = new Map<string, TreeNode>()
  const nameKeyToId = new Map<string, string>()
  const numKeyToId = new Map<string, string>()

  // Helpers
  const normalize = (s: string) => (s || '').toLowerCase().replace(/\s+/g, ' ').trim()
  const onlyWordChars = (s: string) => normalize(s).replace(/[^a-z0-9\.\- _]/g, '')
  const extractNumPrefix = (s: string): string => {
    const m = (s || '').match(/^\s*([0-9]+(?:\.[0-9]+)*)/)
    return m ? m[1] : ''
  }

  const registerTocNode = (node: TreeNode, tocName: string) => {
    const id = node.id
    idMap.set(id, node)
    const normalizedFull = onlyWordChars(tocName)
    if (normalizedFull) nameKeyToId.set(normalizedFull, id)
    const num = extractNumPrefix(tocName)
    if (num) numKeyToId.set(num, id)
  }

  const buildToc = (toc: TocNode[], parentId?: string): TreeNode[] => {
    return toc.map((t, idx) => {
      const id = parentId ? `${parentId}-${idx}` : `toc-${idx}`
      const node: TreeNode = {
        id,
        label: t.name || 'Untitled',
        type: 'toc',
        children: [],
        count: 0,
      }
      registerTocNode(node, t.name || '')
      if (t.children && t.children.length) {
        node.children = buildToc(t.children, id)
      }
      return node
    })
  }

  const tocNodes = buildToc(docToc)
  nodes.push(...tocNodes)

  // Link chunks to TOC nodes
  const orphanChunks: Chunk[] = []
  const allChunks = chunks.value || []
  for (const ch of allChunks) {
    const ref = ch.toc_reference || ''
    const normalizedRef = onlyWordChars(ref)
    const numRef = extractNumPrefix(ref)
    let targetId: string | undefined
    if (normalizedRef && nameKeyToId.has(normalizedRef)) targetId = nameKeyToId.get(normalizedRef)
    else if (numRef && numKeyToId.has(numRef)) targetId = numKeyToId.get(numRef)
    else {
      // fallback: try contains match on name keys
      for (const [k, v] of nameKeyToId.entries()) {
        if (k.includes(normalizedRef) && normalizedRef.length >= 3) {
          targetId = v
          break
        }
      }
    }

    if (targetId) {
      const parent = idMap.get(targetId)
      if (parent) {
        if (!parent.children) parent.children = []
        parent.children.push({
          id: `chunk-${ch.id}`,
          label: ch.title || ch.name || 'Chunk',
          type: 'chunk',
          chunk: ch,
        })
      } else {
        orphanChunks.push(ch)
      }
    } else {
      orphanChunks.push(ch)
    }
  }

  // Add Uncategorized group if needed
  if (orphanChunks.length) {
    nodes.push({
      id: 'group-uncategorized',
      label: 'Uncategorized',
      type: 'group',
      children: orphanChunks
        .sort((a, b) => (a.page || 0) - (b.page || 0))
        .map((ch) => ({
          id: `chunk-${ch.id}`,
          label: ch.title || ch.name || 'Chunk',
          type: 'chunk',
          chunk: ch,
        })),
    })
  }

  // Sort chunk children by page for each TOC node and compute counts
  const computeCounts = (node: TreeNode): number => {
    if (!node.children || node.children.length === 0) {
      return node.type === 'chunk' ? 1 : 0
    }
    // Sort chunk children by page
    const chunksChildren = node.children.filter((c) => c.type === 'chunk')
    const otherChildren = node.children.filter((c) => c.type !== 'chunk')
    chunksChildren.sort((a, b) => (a.chunk?.page || 0) - (b.chunk?.page || 0))
    node.children = [...otherChildren, ...chunksChildren]
    const total = node.children.reduce((acc, child) => acc + computeCounts(child), 0)
    if (node.type === 'toc') node.count = total
    return total
  }
  for (const n of nodes) computeCounts(n)

  return nodes
})

const goBack = () => {
  router.push({ path: `/knowledge-graph/${graphId.value}`, query: { tab: 'explorer' } })
}

const fetchDocument = async () => {
  loadingDocument.value = true
  try {
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
    const response = await fetchData({
      endpoint,
      service: `knowledge_graphs//${graphId.value}/documents/${documentId.value}`,
      method: 'GET',
      credentials: 'include',
    })

    if (response.ok) {
      document.value = await response.json()
    }
  } catch (error) {
    console.error('Error fetching document:', error)
  } finally {
    loadingDocument.value = false
  }
}

const fetchAllChunks = async () => {
  loading.value = true
  try {
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
    const limit = 500
    let offset = 0
    const all: Chunk[] = []
    let total = 0
    do {
      const response = await fetchData({
        endpoint,
        service: `knowledge_graphs//${graphId.value}/documents/${documentId.value}/chunks?limit=${limit}&offset=${offset}`,
        method: 'GET',
        credentials: 'include',
      })
      if (!response.ok) break
      const data = await response.json()
      const batch: Chunk[] = data.chunks || []
      total = data.total || 0
      all.push(...batch)
      offset += limit
      if (batch.length === 0) break
    } while (all.length < total)
    chunks.value = all
  } catch (error) {
    console.error('Error fetching chunks:', error)
  } finally {
    loading.value = false
  }
}

const toggleNodeExpanded = (id: string) => {
  const idx = expandedKeys.value.indexOf(id)
  if (idx >= 0) {
    expandedKeys.value = expandedKeys.value.filter((k) => k !== id)
  } else {
    expandedKeys.value = [...expandedKeys.value, id]
  }
}

const findNodeById = (nodes: TreeNode[], id: string): TreeNode | null => {
  for (const n of nodes) {
    if (n.id === id) return n
    if (n.children) {
      const found = findNodeById(n.children, id)
      if (found) return found
    }
  }
  return null
}

const onTreeNodeClick = (nodeId: string) => {
  const node = findNodeById(treeNodes.value, nodeId)
  if (!node) return

  if (node.type === 'chunk' && node.chunk) {
    selectedChunk.value = node.chunk
    drawerOpen.value = true
    return
  }
  // toggle expand/collapse on header click for TOC/group nodes
  toggleNodeExpanded(node.id)
}

const expandAll = () => {
  const keys: string[] = []
  const walk = (n: TreeNode) => {
    if (n.type !== 'chunk') keys.push(n.id)
    n.children?.forEach(walk)
  }
  treeNodes.value.forEach(walk)
  expandedKeys.value = keys
}

const collapseAll = () => {
  expandedKeys.value = []
}

const isAllExpanded = computed(() => {
  const keys: string[] = []
  const walk = (n: TreeNode) => {
    if (n.type !== 'chunk') keys.push(n.id)
    n.children?.forEach(walk)
  }
  treeNodes.value.forEach(walk)
  if (keys.length === 0) return false
  return keys.every((k) => expandedKeys.value.includes(k))
})

const toggleExpandCollapseAll = () => {
  if (isAllExpanded.value) collapseAll()
  else expandAll()
}

const filterMethod = (node: any, filter: string) => {
  if (!filter) return true
  const f = filter.toLowerCase()
  const label = (node.label || '').toLowerCase()
  if (label.includes(f)) return true
  if (node.type === 'chunk') {
    const t = (node.chunk?.text || '').toLowerCase()
    const title = (node.chunk?.title || '').toLowerCase()
    return t.includes(f) || title.includes(f)
  }
  return false
}

const getIconForNode = (node: TreeNode) => {
  if (node.type === 'chunk') {
    const t = (node.chunk?.chunk_type || '').toLowerCase()
    if (t === 'table') return 'grid_on'
    return 'title'
  }
  if (node.type === 'group') return 'folder'
  return 'subject'
}

onMounted(async () => {
  await fetchDocument()
  await fetchAllChunks()
})
</script>
