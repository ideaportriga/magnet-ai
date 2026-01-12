<template>
  <div class="doc-details">
    <!-- Left Navigation Panel -->
    <div class="doc-nav-panel">
      <!-- Tab Switcher -->
      <div class="nav-tabs-wrapper">
        <q-btn-toggle
          v-model="activeNavTab"
          no-caps
          unelevated
          toggle-color="primary"
          :options="[
            { label: 'Contents', value: 'toc' },
            { label: 'Chunks', value: 'chunks' },
          ]"
          class="nav-tabs-toggle"
        />
      </div>

      <!-- Search -->
      <div class="nav-search">
        <km-input v-model="treeFilter" placeholder="Filter..." icon-before="search" clearable dense />
      </div>

      <!-- TOC / Chunks List -->
      <div class="nav-list">
        <template v-if="activeNavTab === 'toc'">
          <div v-if="loading" class="nav-loading">
            <q-spinner size="24px" color="primary" />
          </div>
          <template v-else-if="hasToc">
            <div class="nav-list-actions">
              <km-btn flat size="sm" color="primary" :label="isAllExpanded ? 'Collapse all' : 'Expand all'" @click="toggleExpandCollapseAll" />
            </div>
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
              class="nav-tree"
            >
              <template #default-header="prop">
                <div
                  class="tree-node-item"
                  :class="{ 'tree-node-item--chunk': prop.node.type === 'chunk' }"
                  @click.stop="onTreeNodeClick(prop.node.id)"
                >
                  <q-icon :name="getIconForNode(prop.node)" size="16px" class="tree-node-icon" />
                  <span class="tree-node-text">{{ prop.node.label }}</span>
                </div>
              </template>
            </q-tree>
          </template>
          <div v-else class="nav-empty">
            <q-icon name="folder_off" size="28px" color="grey-5" />
            <span class="text-grey-6 km-description">No table of contents</span>
          </div>
        </template>

        <template v-else-if="activeNavTab === 'chunks'">
          <div v-if="loading" class="nav-loading">
            <q-spinner size="24px" color="primary" />
          </div>
          <div v-else-if="filteredChunks.length === 0" class="nav-empty">
            <q-icon name="layers" size="28px" color="grey-5" />
            <span class="text-grey-6 km-description">{{ chunks.length === 0 ? 'No chunks' : 'No matches' }}</span>
          </div>
          <div v-else class="chunks-nav-list">
            <div
              v-for="(ch, idx) in filteredChunks"
              :key="ch.id"
              :data-chunk-id="ch.id"
              class="chunk-nav-item"
              :class="{ 'chunk-nav-item--active': selectedChunk?.id === ch.id }"
              @click="onChunkNavClick(ch)"
            >
              <span class="chunk-nav-index">{{ idx + 1 }}</span>
              <q-icon :name="getIconForChunk(ch)" size="16px" class="chunk-nav-icon" />
              <span class="chunk-nav-title">{{ ch.title || ch.name || 'Chunk' }}</span>
              <q-badge v-if="ch.page" color="grey-4" text-color="grey-8" class="chunk-nav-badge">{{ ch.page }}</q-badge>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- Main Content -->
    <div class="doc-main-content">
      <!-- Document Header -->
      <div class="doc-header-card">
        <div class="doc-header-row">
          <div class="doc-header-left">
            <div class="doc-header-info">
              <div class="doc-header-title-row">
                <div class="doc-header-title km-heading-5">{{ document?.title || document?.name || 'Document' }}</div>
                <div class="chunk-counter">
                  <q-icon name="layers" size="14px" />
                  <span class="chunk-counter-value">{{ document?.chunks_count || chunks.length }}</span>
                  <span class="chunk-counter-label">chunks</span>
                </div>
              </div>
              <div class="doc-header-subtitle km-description text-secondary-text">{{ document?.name }}</div>
            </div>
          </div>
          <div class="doc-header-right">
            <q-btn
              flat
              round
              dense
              icon="info"
              :color="metadataPanelOpen ? 'primary' : 'grey-7'"
              class="metadata-toggle-btn"
              @click="metadataPanelOpen = !metadataPanelOpen"
            >
              <q-tooltip>Document Info</q-tooltip>
            </q-btn>
          </div>
        </div>
      </div>

      <!-- Scrollable Content Area with Continuous Chunks -->
      <div ref="scrollAreaRef" class="doc-scroll-area" @scroll="onScrollAreaScroll">
        <!-- Continuous Chunks View -->
        <div v-if="sortedChunks.length > 0" class="chunks-continuous-container">
          <div
            v-for="(chunk, index) in sortedChunks"
            :key="chunk.id"
            :ref="(el) => setChunkRef(chunk.id, el as HTMLElement)"
            :data-chunk-id="chunk.id"
            class="doc-section doc-section--chunk"
            :class="{ 'doc-section--chunk-active': selectedChunk?.id === chunk.id }"
          >
            <div class="section-header section-header--chunk" @click="onChunkHeaderClick(chunk)">
              <span class="chunk-index-badge">{{ index + 1 }}</span>
              <span class="section-title">{{ chunk.title || chunk.name || 'Chunk Content' }}</span>
              <q-space />
              <q-badge v-if="chunk.page" color="secondary" text-color="white" class="chunk-page-badge">Page {{ chunk.page }}</q-badge>
            </div>
            <div class="section-body section-body--chunk">
              <div class="chunk-content-wrapper">
                <div class="chunk-content markdown-content" v-html="getRenderedContent(chunk)" />
              </div>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else-if="!loading" class="doc-section doc-section--empty">
          <div class="empty-placeholder">
            <q-icon name="layers" size="40px" color="grey-4" />
            <div class="km-heading-7 text-grey-6 q-mt-md">No chunks available</div>
            <div class="km-description text-grey-5">This document has no content chunks</div>
          </div>
        </div>

        <!-- Loading State -->
        <div v-else class="doc-section doc-section--empty">
          <div class="empty-placeholder">
            <q-spinner size="40px" color="primary" />
            <div class="km-heading-7 text-grey-6 q-mt-md">Loading chunks...</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Right Metadata Panel -->
    <MetadataPanel
      :open="metadataPanelOpen"
      :summary="document?.summary ?? null"
      :file-metadata="fileMetadata"
      :source-metadata="sourceMetadata"
      :llm-metadata="llmMetadata"
      @close="metadataPanelOpen = false"
    />
  </div>
</template>

<script setup lang="ts">
import { fetchData } from '@shared'
import MarkdownIt from 'markdown-it'
import MarkdownItAbbr from 'markdown-it-abbr'
import MarkdownItAnchor from 'markdown-it-anchor'
import MarkdownItFootnote from 'markdown-it-footnote'
import MarkdownItHighlightjs from 'markdown-it-highlightjs'
import MarkdownItSub from 'markdown-it-sub'
import MarkdownItSup from 'markdown-it-sup'
import MarkdownItTasklists from 'markdown-it-task-lists'
import MarkdownItTOC from 'markdown-it-toc-done-right'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useStore } from 'vuex'
import MetadataPanel from './MetadataPanel.vue'
import { Chunk, Document, TocNode, TreeNode } from './models'

type MetadataOrigin = 'file' | 'source' | 'llm'
type MetadataValueKind = 'string' | 'number' | 'boolean' | 'date' | 'json'

interface MetadataItem {
  origin: MetadataOrigin
  key: string
  label: string
  kind: MetadataValueKind
  value: string
}

const route = useRoute()
const store = useStore()

const graphId = computed(() => route.params.id as string)
const documentId = computed(() => route.params.documentId as string)

const document = ref<Document | null>(null)
const chunks = ref<Chunk[]>([])
const loading = ref(true)
const selectedChunk = ref<Chunk | null>(null)
const metadataPanelOpen = ref(false)
const activeNavTab = ref<'toc' | 'chunks'>('toc')

// Tree state
const expandedKeys = ref<string[]>([])
const selectedKey = ref<string>('')
const treeFilter = ref('')

// Continuous scrolling state
const scrollAreaRef = ref<HTMLElement | null>(null)
const chunkRefs = ref<Map<string, HTMLElement>>(new Map())
const activeChunkId = ref<string | null>(null)
const isScrollingProgrammatically = ref(false)
type ChunkScrollPosition = { id: string; top: number; bottom: number }
const chunkScrollPositions = ref<ChunkScrollPosition[]>([])
const ACTIVE_AREA_HEIGHT_PX = 120

let scrollRafId: number | null = null
let recomputePositionsTimer: number | null = null

const setChunkRef = (chunkId: string, el: HTMLElement | null) => {
  if (el) {
    chunkRefs.value.set(chunkId, el)
  } else {
    chunkRefs.value.delete(chunkId)
  }
}

// Markdown renderer
const markdown = new MarkdownIt({ html: true, breaks: true, linkify: true })
  .use(MarkdownItAbbr)
  .use(MarkdownItAnchor)
  .use(MarkdownItFootnote)
  .use(MarkdownItHighlightjs)
  .use(MarkdownItSub)
  .use(MarkdownItSup)
  .use(MarkdownItTasklists)
  .use(MarkdownItTOC)

// Cache for rendered chunk content
const renderedContentCache = new Map<string, string>()

const getRenderedContent = (chunk: Chunk): string => {
  if (!chunk?.content) return ''

  const cacheKey = `${chunk.id}-${chunk.content_format}`
  if (renderedContentCache.has(cacheKey)) {
    return renderedContentCache.get(cacheKey)!
  }

  let rendered: string
  if (chunk.content_format === 'html') {
    rendered = chunk.content
  } else {
    rendered = markdown.render(chunk.content)
  }

  renderedContentCache.set(cacheKey, rendered)
  return rendered
}

const hasToc = computed(() => {
  const toc = document.value?.toc
  return Array.isArray(toc) && toc.length > 0
})

const metadataByOrigin = computed<Record<MetadataOrigin, MetadataItem[]>>(() => {
  const metaAny = (document.value?.metadata ?? null) as any
  if (!metaAny || typeof metaAny !== 'object' || Array.isArray(metaAny)) {
    return { file: [], source: [], llm: [] }
  }

  const hasGroupedOrigins = 'file' in metaAny || 'source' in metaAny || 'llm' in metaAny
  if (!hasGroupedOrigins) {
    // Backward compatibility: treat unknown metadata shapes as file metadata.
    return { file: toMetadataItems(metaAny, 'file'), source: [], llm: [] }
  }

  return {
    file: toMetadataItems(metaAny?.file, 'file'),
    source: toMetadataItems(metaAny?.source, 'source'),
    llm: toMetadataItems(metaAny?.llm, 'llm'),
  }
})

const fileMetadata = computed(() => metadataByOrigin.value.file)
const sourceMetadata = computed(() => metadataByOrigin.value.source)
const llmMetadata = computed(() => metadataByOrigin.value.llm)

function toMetadataItems(meta: unknown, origin: MetadataOrigin): MetadataItem[] {
  if (!meta || typeof meta !== 'object' || Array.isArray(meta)) return []

  const items: MetadataItem[] = []
  for (const [rawKey, rawVal] of Object.entries(meta as Record<string, unknown>)) {
    if (rawVal === undefined || rawVal === null || rawVal === '') continue
    const { kind, value } = formatMetadataValue(rawVal)
    items.push({
      origin,
      key: rawKey,
      label: formatKey(rawKey),
      kind,
      value,
    })
  }

  items.sort((a, b) => a.label.localeCompare(b.label))
  return items
}

function formatKey(key: string): string {
  return String(key || '')
    .trim()
    .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
    .replace(/[_-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

function formatMetadataValue(val: unknown): { kind: MetadataValueKind; value: string } {
  if (val === null || val === undefined) return { kind: 'string', value: '' }

  if (typeof val === 'boolean') return { kind: 'boolean', value: val ? 'Yes' : 'No' }

  if (typeof val === 'number') {
    return { kind: 'number', value: Number.isFinite(val) ? val.toLocaleString() : String(val) }
  }

  if (val instanceof Date) {
    return { kind: 'date', value: val.toLocaleString() }
  }

  if (typeof val === 'string') {
    const s = val.trim()
    if (looksLikeDateString(s)) {
      const d = new Date(s)
      if (!Number.isNaN(d.getTime())) {
        const hasTime = /[T\s]\d{2}:\d{2}/.test(s)
        return {
          kind: 'date',
          value: hasTime
            ? d.toLocaleString(undefined, { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
            : d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' }),
        }
      }
    }
    return { kind: 'string', value: val }
  }

  if (Array.isArray(val)) {
    const display = val
      .filter((x) => x !== null && x !== undefined && x !== '')
      .map((x) => (typeof x === 'string' ? x : JSON.stringify(x)))
      .join(', ')
    return { kind: 'json', value: display }
  }

  if (typeof val === 'object') {
    try {
      return { kind: 'json', value: JSON.stringify(val) }
    } catch (e) {
      return { kind: 'json', value: String(val) }
    }
  }

  return { kind: 'string', value: String(val) }
}

function looksLikeDateString(s: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}/.test(s)) return false
  const parsed = Date.parse(s)
  return !Number.isNaN(parsed)
}

// Build tree nodes from document TOC
const treeNodes = computed<TreeNode[]>(() => {
  const docToc = (document.value?.toc || []) as TocNode[]
  const nodes: TreeNode[] = []
  const idMap = new Map<string, TreeNode>()
  const nameKeyToId = new Map<string, string>()
  const numKeyToId = new Map<string, string>()

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
      const node: TreeNode = { id, label: t.name || 'Untitled', type: 'toc', children: [] }
      registerTocNode(node, t.name || '')
      if (t.children && t.children.length) {
        node.children = buildToc(t.children, id)
      }
      return node
    })
  }

  const tocNodes = buildToc(docToc)
  nodes.push(...tocNodes)

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
        parent.children.push({ id: `chunk-${ch.id}`, label: ch.title || ch.name || 'Chunk', type: 'chunk', chunk: ch })
      } else {
        orphanChunks.push(ch)
      }
    } else {
      orphanChunks.push(ch)
    }
  }

  if (orphanChunks.length) {
    nodes.push({
      id: 'group-uncategorized',
      label: 'Uncategorized',
      type: 'group',
      children: orphanChunks
        .sort((a, b) => (a.page || 0) - (b.page || 0))
        .map((ch) => ({ id: `chunk-${ch.id}`, label: ch.title || ch.name || 'Chunk', type: 'chunk', chunk: ch })),
    })
  }

  const sortChildren = (node: TreeNode) => {
    if (!node.children || node.children.length === 0) return

    const chunkChildren = node.children.filter((c) => c.type === 'chunk')
    const otherChildren = node.children.filter((c) => c.type !== 'chunk')
    chunkChildren.sort((a, b) => (a.chunk?.page || 0) - (b.chunk?.page || 0))
    node.children = [...otherChildren, ...chunkChildren]

    node.children.forEach(sortChildren)
  }
  for (const n of nodes) sortChildren(n)

  return nodes
})

const fetchDocument = async () => {
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

const findPathById = (nodes: TreeNode[], id: string, path: string[] = []): string[] | null => {
  for (const n of nodes) {
    const nextPath = [...path, n.id]
    if (n.id === id) return nextPath
    if (n.children) {
      const found = findPathById(n.children, id, nextPath)
      if (found) return found
    }
  }
  return null
}

const expandToNodeId = (id: string) => {
  const path = findPathById(treeNodes.value, id)
  if (!path) return

  const parents = path.slice(0, -1)
  if (parents.length === 0) return

  const next = new Set(expandedKeys.value)
  for (const p of parents) next.add(p)
  expandedKeys.value = Array.from(next)
}

const syncTreeSelectionToChunkId = (chunkId: string) => {
  const nodeId = `chunk-${chunkId}`
  selectedKey.value = nodeId
  if (findNodeById(treeNodes.value, nodeId)) {
    expandToNodeId(nodeId)
  }
}

const onTreeNodeClick = (nodeId: string) => {
  const node = findNodeById(treeNodes.value, nodeId)
  if (!node) return
  if (node.type === 'chunk' && node.chunk) {
    setChunkSelection(node.chunk, { source: 'toc-tree', scrollTo: true, scrollBehavior: 'smooth' })
    return
  }
  toggleNodeExpanded(node.id)
}

const getExpandableNodeIds = (nodes: TreeNode[]): string[] => {
  const ids: string[] = []
  const walk = (n: TreeNode) => {
    if (n.type !== 'chunk') ids.push(n.id)
    n.children?.forEach(walk)
  }
  nodes.forEach(walk)
  return ids
}

const expandAll = () => {
  expandedKeys.value = getExpandableNodeIds(treeNodes.value)
}

const collapseAll = () => {
  expandedKeys.value = []
}

const isAllExpanded = computed(() => {
  const keys = getExpandableNodeIds(treeNodes.value)
  if (keys.length === 0) return false
  return keys.every((k) => expandedKeys.value.includes(k))
})

const toggleExpandCollapseAll = () => {
  if (isAllExpanded.value) collapseAll()
  else expandAll()
}

const sortedChunks = computed<Chunk[]>(() => {
  const all = chunks.value || []
  return all
    .map((ch, idx) => ({ ch, idx }))
    .sort((a, b) => {
      const ap = a.ch.page ?? Number.MAX_SAFE_INTEGER
      const bp = b.ch.page ?? Number.MAX_SAFE_INTEGER
      if (ap !== bp) return ap - bp
      return a.idx - b.idx
    })
    .map((x) => x.ch)
})

const filteredChunks = computed<Chunk[]>(() => {
  const f = (treeFilter.value || '').trim().toLowerCase()
  if (!f) return sortedChunks.value
  return sortedChunks.value.filter((ch) => {
    const title = (ch.title || ch.name || '').toLowerCase()
    const content = (((ch as any).content ?? (ch as any).text ?? '') as string).toLowerCase()
    return title.includes(f) || content.includes(f)
  })
})

const filterMethod = (node: any, filter: string) => {
  if (!filter) return true
  const f = filter.toLowerCase()
  const label = (node.label || '').toLowerCase()
  if (label.includes(f)) return true
  if (node.type === 'chunk') {
    const content = ((node.chunk?.content ?? node.chunk?.text ?? '') as string).toLowerCase()
    const title = (node.chunk?.title || '').toLowerCase()
    const name = (node.chunk?.name || '').toLowerCase()
    return content.includes(f) || title.includes(f) || name.includes(f)
  }
  return false
}

const getIconForNode = (node: TreeNode) => {
  if (node.type === 'chunk') {
    const t = (node.chunk?.chunk_type || '').toLowerCase()
    if (t === 'table') return 'grid_on'
    return 'notes'
  }
  if (node.type === 'group') return 'folder'
  return 'bookmark'
}

const getIconForChunk = (chunk: Chunk) => {
  const t = (chunk.chunk_type || '').toLowerCase()
  if (t === 'table') return 'grid_on'
  return 'notes'
}

type ChunkSelectionSource = 'init' | 'scroll' | 'chunks-nav' | 'toc-tree' | 'content'
type ChunkSelectionOptions = {
  source: ChunkSelectionSource
  scrollTo?: boolean
  scrollBehavior?: ScrollBehavior
  navScrollBehavior?: ScrollBehavior
}

const setChunkSelection = (chunk: Chunk, opts: ChunkSelectionOptions) => {
  if (!chunk?.id) return
  const nextId = chunk.id

  selectedChunk.value = chunk
  activeChunkId.value = nextId

  syncTreeSelectionToChunkId(nextId)

  if (opts.scrollTo) {
    nextTick(() => {
      scrollToChunk(nextId, opts.scrollBehavior ?? 'smooth')
    })
  }

  nextTick(() => {
    scrollNavToChunk(nextId, opts.navScrollBehavior ?? (opts.source === 'chunks-nav' || opts.source === 'toc-tree' ? 'smooth' : 'auto'))
  })
}

const onChunkNavClick = (chunk: Chunk) => {
  setChunkSelection(chunk, { source: 'chunks-nav', scrollTo: true, scrollBehavior: 'smooth', navScrollBehavior: 'smooth' })
}

const onChunkHeaderClick = (chunk: Chunk) => {
  setChunkSelection(chunk, { source: 'content', scrollTo: false, navScrollBehavior: 'auto' })
}

// Scroll to a specific chunk in the content area
const scrollToChunk = (chunkId: string, behavior: ScrollBehavior = 'smooth') => {
  const el = chunkRefs.value.get(chunkId)
  if (el && scrollAreaRef.value) {
    isScrollingProgrammatically.value = behavior === 'smooth'
    el.scrollIntoView({ behavior, block: 'center' })

    // Reset flag after scroll animation and sync active chunk once settled.
    window.setTimeout(
      () => {
        isScrollingProgrammatically.value = false
        updateActiveChunkFromScroll()
      },
      behavior === 'smooth' ? 500 : 0
    )
  }
}

// Scroll navigation panel to show the active chunk
const scrollNavToChunk = (chunkId: string, behavior: ScrollBehavior = 'auto') => {
  const navItem = window.document.querySelector(`.chunk-nav-item[data-chunk-id="${chunkId}"]`) as HTMLElement
  if (navItem) {
    navItem.scrollIntoView({ behavior, block: 'nearest' })
  }
}

// Handle scroll in the main content area
const onScrollAreaScroll = () => {
  if (scrollRafId !== null) return
  scrollRafId = window.requestAnimationFrame(() => {
    scrollRafId = null
    updateActiveChunkFromScroll()
  })
}

const recomputeChunkScrollPositions = async () => {
  const container = scrollAreaRef.value
  if (!container) return

  // Allow DOM/layout to settle before measuring.
  await nextTick()

  const containerRect = container.getBoundingClientRect()
  const positions: ChunkScrollPosition[] = []

  for (const ch of sortedChunks.value) {
    const el = chunkRefs.value.get(ch.id)
    if (!el) continue
    const rect = el.getBoundingClientRect()
    const top = rect.top - containerRect.top + container.scrollTop
    positions.push({ id: ch.id, top, bottom: top + rect.height })
  }

  positions.sort((a, b) => a.top - b.top)
  chunkScrollPositions.value = positions

  // After recomputing (e.g., resize / layout changes), ensure selection matches current scroll position.
  updateActiveChunkFromScroll()
}

const scheduleRecomputeChunkScrollPositions = () => {
  if (recomputePositionsTimer !== null) {
    window.clearTimeout(recomputePositionsTimer)
  }
  recomputePositionsTimer = window.setTimeout(() => {
    recomputeChunkScrollPositions()
    recomputePositionsTimer = null
  }, 60)
}

const updateActiveChunkFromScroll = () => {
  if (isScrollingProgrammatically.value) return
  const container = scrollAreaRef.value
  if (!container) return

  const scrollTop = container.scrollTop
  const clientHeight = container.clientHeight
  const scrollHeight = container.scrollHeight

  let nextId: string | null = null

  // Exception: Start of scroll
  if (scrollTop < 20) {
    nextId = chunkScrollPositions.value[0]?.id || null
  }
  // Exception: End of scroll
  else if (scrollTop + clientHeight >= scrollHeight - 20) {
    nextId = chunkScrollPositions.value[chunkScrollPositions.value.length - 1]?.id || null
  }
  // Active Area Logic
  else {
    const areaTop = scrollTop + (clientHeight - ACTIVE_AREA_HEIGHT_PX) / 2
    const areaBottom = areaTop + ACTIVE_AREA_HEIGHT_PX
    const areaCenter = areaTop + ACTIVE_AREA_HEIGHT_PX / 2

    let maxOverlap = -1
    let minDistToCenter = Number.MAX_VALUE

    for (const pos of chunkScrollPositions.value) {
      if (pos.top > areaBottom) break // Optimization: chunks sorted by top

      const overlapTop = Math.max(areaTop, pos.top)
      const overlapBottom = Math.min(areaBottom, pos.bottom)
      const overlap = overlapBottom - overlapTop

      if (overlap > 0) {
        if (overlap > maxOverlap) {
          maxOverlap = overlap
          nextId = pos.id
          const chunkCenter = (pos.top + pos.bottom) / 2
          minDistToCenter = Math.abs(chunkCenter - areaCenter)
        } else if (Math.abs(overlap - maxOverlap) < 1) {
          // Tie-breaker: closest to center
          const chunkCenter = (pos.top + pos.bottom) / 2
          const dist = Math.abs(chunkCenter - areaCenter)
          if (dist < minDistToCenter) {
            minDistToCenter = dist
            nextId = pos.id
          }
        }
      }
    }
  }

  if (!nextId || nextId === activeChunkId.value) return

  const chunk = sortedChunks.value.find((c) => c.id === nextId)
  if (!chunk) return
  setChunkSelection(chunk, { source: 'scroll', scrollTo: false, navScrollBehavior: 'auto' })
}

const onWindowResize = () => scheduleRecomputeChunkScrollPositions()

// Watch for chunks loading and sync scroll positions + initial selection
watch(
  sortedChunks,
  (newChunks) => {
    if (newChunks.length > 0) {
      // Select first chunk if none selected
      // Keep scroll at the top on initial load; don't jump into the middle of the document.
      if (!selectedChunk.value) {
        setChunkSelection(newChunks[0], { source: 'init', scrollTo: false, navScrollBehavior: 'auto' })
      }
      scheduleRecomputeChunkScrollPositions()
    }
  },
  { immediate: true }
)

watch(metadataPanelOpen, () => {
  scheduleRecomputeChunkScrollPositions()
})

onMounted(async () => {
  await fetchDocument()
  await fetchAllChunks()
  if (hasToc.value) {
    activeNavTab.value = 'toc'
    expandAll()
  } else {
    activeNavTab.value = 'chunks'
  }

  window.addEventListener('resize', onWindowResize)

  // Ensure we start at the top when opening a document (avoids starting mid-scroll if the component is reused).
  await nextTick()
  if (scrollAreaRef.value) scrollAreaRef.value.scrollTop = 0

  scheduleRecomputeChunkScrollPositions()
})

onBeforeUnmount(() => {
  if (scrollRafId !== null) {
    window.cancelAnimationFrame(scrollRafId)
    scrollRafId = null
  }
  if (recomputePositionsTimer !== null) {
    window.clearTimeout(recomputePositionsTimer)
    recomputePositionsTimer = null
  }
  window.removeEventListener('resize', onWindowResize)
  renderedContentCache.clear()
})
</script>

<style scoped>
/* ============================================
   Layout
   ============================================ */
.doc-details {
  display: flex;
  height: 100%;
  background: #f5f6f8;
  gap: 16px;
  padding: 16px;
}

@media (max-width: 1024px) {
  .doc-details {
    position: relative;
  }
}

/* ============================================
   Navigation Panel
   ============================================ */
.doc-nav-panel {
  width: 280px;
  min-width: 280px;
  background: #fff;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.nav-tabs-wrapper {
  padding: 14px 12px 0;
}

.nav-tabs-toggle {
  width: 100%;
  border-radius: 4px;
  background: #f3f4f6;
}

.nav-tabs-toggle :deep(.q-btn) {
  flex: 1;
  font-size: 12px;
  font-weight: 500;
}

.nav-search {
  padding: 12px;
}

.nav-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px 12px;
}

.nav-list-actions {
  padding: 0 4px 8px;
}

.nav-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px;
}

.nav-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 32px 16px;
  text-align: center;
}

/* Tree Styling */
.nav-tree {
  font-size: 13px;
}

.nav-tree :deep(.q-tree__node-header) {
  padding: 0;
}

.tree-node-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 6px;
  cursor: pointer;
  width: 100%;
}

.tree-node-item:hover {
  background: #f3f4f6;
}

.nav-tree :deep(.q-tree__node--selected .tree-node-item) {
  background: var(--q-primary-bg);
}

.nav-tree :deep(.q-tree__node--selected .tree-node-text) {
  color: var(--q-primary);
  font-weight: 600;
}

.nav-tree :deep(.q-tree__node--selected .tree-node-icon) {
  color: var(--q-primary);
}

.tree-node-icon {
  color: #9ca3af;
  flex-shrink: 0;
}

.tree-node-item--chunk .tree-node-icon {
  color: var(--q-primary);
}

.tree-node-text {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #374151;
  font-size: 13px;
}

/* Chunks Nav List */
.chunks-nav-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.chunk-nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 6px;
  cursor: pointer;
}

.chunk-nav-item:hover {
  background: #f3f4f6;
}

.chunk-nav-item--active {
  background: var(--q-primary-bg);
}

.chunk-nav-icon {
  color: var(--q-primary);
  flex-shrink: 0;
}

.chunk-nav-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  color: #374151;
}

.chunk-nav-badge {
  font-size: 10px;
  padding: 2px 6px;
}

.chunk-nav-index {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  font-size: 10px;
  font-weight: 600;
  color: #9ca3af;
  background: #f3f4f6;
  border-radius: 4px;
  flex-shrink: 0;
}

.chunk-nav-item--active .chunk-nav-index {
  background: var(--q-primary);
  color: white;
}

/* ============================================
   Main Content
   ============================================ */
.doc-main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  gap: 16px;
}

/* Header Card */
.doc-header-card {
  background: linear-gradient(135deg, #ffffff 0%, #fafbfd 100%);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 12px;
  padding: 16px 20px;
}

.doc-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.doc-header-left {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}

.doc-header-info {
  min-width: 0;
}

.doc-header-title-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.doc-header-title {
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chunk-counter {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  background: #f3f4f6;
  border-radius: 6px;
  color: #4b5563;
  flex-shrink: 0;
}

.chunk-counter-value {
  font-size: 12px;
  font-weight: 600;
  color: #111827;
}

.chunk-counter-label {
  font-size: 12px;
  font-weight: 500;
  color: #6b7280;
}

.doc-header-subtitle {
  margin-top: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.doc-header-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.metadata-toggle-btn {
  font-size: 13px;
  font-weight: 500;
  padding: 6px 14px;
  border-radius: 8px;
  transition: all 0.15s ease;
}

/* Scroll Area */
.doc-scroll-area {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-bottom: 32px;
  padding-right: 8px;
}

/* Section Cards */
.doc-section {
  background: #fff;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 10px;
  overflow: hidden;
}

.section-header {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  user-select: none;
}

.section-header:hover {
  background: #fafafa;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
}

/* Continuous Chunks Container */
.chunks-continuous-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Chunk Viewer */
.doc-section--chunk {
  display: flex;
  flex-direction: column;
  min-height: 200px;
  scroll-margin-top: 8px;
  transition:
    box-shadow 0.2s ease,
    border-color 0.2s ease;
  border: 1px solid #9ca3af;
}

.chunk-index-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 24px;
  height: 24px;
  font-size: 11px;
  font-weight: 600;
  color: #6b7280;
  background: #f3f4f6;
  border-radius: 6px;
  margin-right: 8px;
  flex-shrink: 0;
}

.chunk-page-badge {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 6px;
}

.doc-section--chunk-active .chunk-index-badge {
  background: var(--q-primary);
  color: white;
}

.section-header--chunk {
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  cursor: default;
}

.section-header--chunk:hover {
  background: transparent;
}

.doc-section--chunk-active .section-header {
  background: var(--q-primary-bg);
}

.section-body--chunk {
  padding: 0;
  overflow: visible;
}

.chunk-content-wrapper {
  padding: 20px;
  min-height: 100%;
}

.chunk-content {
  max-width: 100%;
}

/* Empty State */
.doc-section--empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  border-style: dashed;
  min-height: 200px;
}

.empty-placeholder {
  text-align: center;
  padding: 32px;
}

/* ============================================
   Markdown Content
   ============================================ */
.markdown-content {
  line-height: 1.7;
  color: #374151;
  font-size: 14px;
}

.markdown-content :deep(h1) {
  font-size: 20px;
  font-weight: 600;
  margin: 20px 0 12px 0;
  color: #111827;
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 8px;
}

.markdown-content :deep(h2) {
  font-size: 17px;
  font-weight: 600;
  margin: 18px 0 10px 0;
  color: #1f2937;
}

.markdown-content :deep(h3) {
  font-size: 15px;
  font-weight: 600;
  margin: 14px 0 8px 0;
  color: #374151;
}

.markdown-content :deep(h4),
.markdown-content :deep(h5),
.markdown-content :deep(h6) {
  font-size: 14px;
  font-weight: 600;
  margin: 12px 0 6px 0;
  color: #4b5563;
}

.markdown-content :deep(p) {
  margin: 0 0 12px 0;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  margin: 8px 0 12px 0;
  padding-left: 24px;
}

.markdown-content :deep(li) {
  margin-bottom: 4px;
}

.markdown-content :deep(code) {
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'SF Mono', 'Consolas', monospace;
  font-size: 13px;
  color: #be185d;
}

.markdown-content :deep(pre) {
  background: #1f2937;
  border-radius: 8px;
  padding: 16px;
  overflow-x: auto;
  margin: 12px 0;
}

.markdown-content :deep(pre code) {
  background: transparent;
  color: #e5e7eb;
  padding: 0;
  font-size: 13px;
}

.markdown-content :deep(blockquote) {
  border-left: 3px solid var(--q-primary);
  padding: 8px 16px;
  margin: 12px 0;
  background: #f9fafb;
  color: #6b7280;
}

.markdown-content :deep(a) {
  color: var(--q-primary);
  text-decoration: none;
}

.markdown-content :deep(a:hover) {
  text-decoration: underline;
}

.markdown-content :deep(hr) {
  border: none;
  border-top: 1px solid #e5e7eb;
  margin: 20px 0;
}

.markdown-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 12px 0;
  font-size: 13px;
}

.markdown-content :deep(th) {
  background: #f9fafb;
  padding: 10px 12px;
  border: 1px solid #e5e7eb;
  font-weight: 600;
  text-align: left;
}

.markdown-content :deep(td) {
  padding: 10px 12px;
  border: 1px solid #e5e7eb;
}

.markdown-content :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 6px;
}
</style>
