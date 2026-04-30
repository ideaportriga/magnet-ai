<template>
  <div v-if="tabs.length &gt; 0" ref="tabBarRef" class="workspace-tab-bar" data-test="workspace-tab-bar">
    <div v-if="showScrollLeft" class="workspace-scroll-btn workspace-scroll-btn--left" @click="scrollLeftBy">
      <km-glyph name="chevron_left" size="16px" />
    </div>
    <div ref="tabsContainerRef" class="workspace-tabs">
      <ds-context-menu v-for="(tab, index) in tabs" :key="tab.id">
        <ds-context-menu-trigger as-child>
          <div class="workspace-tab" :class="tabClass(tab)" :draggable="!tab.pinned" :data-index="index" :data-tab-id="tab.id" @click="activateTab(tab)" @mousedown.middle.prevent="requestClose(tab)" @dragstart="onDragStart($event, index)" @dragover.prevent="onDragOver($event, index)" @dragend="onDragEnd">
            <km-glyph class="workspace-tab-icon" :name="entityIcon(tab)" size="14px" />
            <div class="workspace-tab-label">{{ tab.label }}</div>
            <km-tooltip v-if="isLabelTruncated(tab)" anchor="top middle" self="bottom middle" :delay="600">{{ getTooltip(tab) }}</km-tooltip>
            <km-glyph v-if="tab.pinned" class="workspace-tab-pin-badge" name="pin" size="8px" />
            <div v-if="tab.dirty &amp;&amp; !tab.pinned" class="workspace-tab-dirty">
              <div class="dirty-dot" />
            </div>
            <div v-if="!tab.pinned" class="workspace-tab-close" @click.stop="requestClose(tab)">
              <km-glyph name="close" size="12px" />
            </div>
          </div>
        </ds-context-menu-trigger>
        <ds-context-menu-content data-test="tab-context-menu">
          <ds-context-menu-item @select="requestClose(tab)">
            <km-glyph name="close" size="14px" /><span>{{ m.workspace_close() }}</span>
          </ds-context-menu-item>
          <ds-context-menu-separator />
          <ds-context-menu-item @select="togglePin(tab)">
            <km-glyph name="pin" size="14px" /><span>{{ tab.pinned ? m.workspace_unpin() : m.workspace_pinTab() }}</span>
          </ds-context-menu-item>
          <ds-context-menu-separator />
          <ds-context-menu-item @select="closeOtherTabs(tab)">{{ m.workspace_closeOthers() }}</ds-context-menu-item>
          <ds-context-menu-item @select="closeTabsToRight(tab)">{{ m.workspace_closeToRight() }}</ds-context-menu-item>
          <ds-context-menu-item @select="closeTabsToLeft(tab)">{{ m.workspace_closeToLeft() }}</ds-context-menu-item>
          <ds-context-menu-separator />
          <ds-context-menu-item @select="closeAllTabs">{{ m.workspace_closeAll() }}</ds-context-menu-item>
        </ds-context-menu-content>
      </ds-context-menu>
    </div>
    <div v-if="showScrollRight" class="workspace-scroll-btn workspace-scroll-btn--right" @click="scrollRightBy">
      <km-glyph name="chevron_right" size="16px" />
    </div>
  </div>
  <km-popup-confirm :visible="showDirtyConfirm" :confirm-button-label="m.common_closeWithoutSaving()" :cancel-button-label="m.common_cancel()" notification-icon="warning" @confirm="confirmCloseTab" @cancel="showDirtyConfirm = false">
    <div class="cluster km-heading-7 mb-md" data-justify="center">{{ m.workspace_unsavedChanges() }}</div>
    <div class="cluster" data-justify="center">{{ m.workspace_unsavedTabMessage() }}</div>
  </km-popup-confirm>
</template>

<script setup lang="ts">
import { m } from '@/paraglide/messages'
import { ref, computed, nextTick, onMounted, onBeforeUnmount, watch, watchEffect } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useWorkspaceStore, type WorkspaceTab } from '@/stores/workspaceStore'
import { useEditBufferStore } from '@/stores/editBufferStore'
import { storeToRefs } from 'pinia'

const router = useRouter()
const route = useRoute()
const workspace = useWorkspaceStore()
const editBuffer = useEditBufferStore()
const { tabs, activeTabId } = storeToRefs(workspace)

// Clear active tab highlight when navigating away from a detail page
watch(
  () => route.fullPath,
  () => {
    const active = tabs.value.find((t) => t.id === activeTabId.value)
    if (!active) return
    const tabRoute = getRouteForTab(active)
    if (!tabRoute || !route.path.startsWith(tabRoute)) {
      workspace.clearActiveTab()
    }
  },
)

// Entity type → sidebar icon mapping
const entityIconMap: Record<string, string> = {
  agents: 'robot',
  promptTemplates: 'chat',
  rag_tools: 'file-question',
  retrieval: 'file-question',
  ai_apps: 'magic',
  api_servers: 'swap',
  mcp_servers: 'server',
  collections: 'book',
  provider: 'graph',
  model: 'graph',
  evaluation_sets: 'table-list',
  evaluation_jobs: 'clipboard-check',
  assistant_tools: 'wrench',
  knowledge_graph: 'o_hub',
  observability_traces: 'steps',
  api_keys: 'lock',
  note_taker: 'microphone',
}

function entityIcon(tab: WorkspaceTab): string {
  return entityIconMap[tab.entityType] || tab.icon || 'file'
}

const entityLabelMap: Record<string, string> = {
  agents: 'Agent',
  promptTemplates: 'Prompt Template',
  rag_tools: 'RAG Tool',
  retrieval: 'Retrieval Tool',
  ai_apps: 'AI App',
  api_servers: 'API Server',
  mcp_servers: 'MCP Server',
  collections: 'Knowledge Source',
  provider: 'Model Provider',
  model: 'Model',
  evaluation_sets: 'Test Set',
  evaluation_jobs: 'Evaluation',
  assistant_tools: 'Assistant Tool',
  knowledge_graph: 'Knowledge Graph',
  observability_traces: 'Trace',
  api_keys: 'API Key',
  note_taker: 'Note Taker',
}

function entityLabel(tab: WorkspaceTab): string {
  return entityLabelMap[tab.entityType] || tab.entityType
}

function getTooltip(tab: WorkspaceTab): string {
  return `${entityLabel(tab)}: ${tab.label}`
}

function isLabelTruncated(tab: WorkspaceTab): boolean {
  const el = tabsContainerRef.value?.querySelector(`[data-tab-id="${tab.id}"] .workspace-tab-label`) as HTMLElement
  if (!el) return true
  return el.scrollWidth > el.clientWidth
}

const showDirtyConfirm = ref(false)
const pendingCloseTab = ref<WorkspaceTab | null>(null)
const tabBarRef = ref<HTMLElement | null>(null)
const tabsContainerRef = ref<HTMLElement | null>(null)
const showScrollRight = ref(false)
const showScrollLeft = ref(false)

// Drag state
const dragIndex = ref<number | null>(null)
const dragOverIndex = ref<number | null>(null)

/** Clear *all* drag state — DOM classes + refs. Called from local `dragend`,
 *  from the global safety handler below, and from `onBeforeUnmount`. Without
 *  this, a cancelled/lost drag can leave the browser in a state where the
 *  next mousedown on any tab is still interpreted as drag-continuation and
 *  clicks silently never fire. */
function resetDragState() {
  dragIndex.value = null
  dragOverIndex.value = null
  document.querySelectorAll('.workspace-tab.dragging').forEach((el) => el.classList.remove('dragging'))
}

const tabClass = (tab: WorkspaceTab) => ({
  active: tab.id === activeTabId.value,
  dirty: tab.dirty,
  pinned: tab.pinned,
  'drag-over': dragOverIndex.value !== null && dragIndex.value !== null && dragOverIndex.value !== dragIndex.value,
})

// Scroll detection
function checkScroll() {
  const el = tabBarRef.value
  if (!el) return
  showScrollRight.value = el.scrollWidth > el.clientWidth + el.scrollLeft + 10
  showScrollLeft.value = el.scrollLeft > 10
}

function scrollRightBy() {
  tabBarRef.value?.scrollBy({ left: 200, behavior: 'smooth' })
}

function scrollLeftBy() {
  tabBarRef.value?.scrollBy({ left: -200, behavior: 'smooth' })
}

// Scroll the active tab into view. Called from `activateTab` AND from a
// watcher on `activeTabId` so route-driven navigation (sidebar click,
// back/forward, deep-link) also centers the active tab when there are
// many tabs and the current one is scrolled off-screen.
function scrollActiveIntoView() {
  nextTick(() => {
    const activeEl = tabBarRef.value?.querySelector('.workspace-tab.active') as HTMLElement | null
    activeEl?.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'nearest' })
  })
}

// §B.3 — watchEffect ties listener + ResizeObserver lifecycle to the ref itself,
// so if tabBarRef changes (HMR, keep-alive rerender) we clean up before re-binding.
watchEffect((onCleanup) => {
  const el = tabBarRef.value
  if (!el) return
  checkScroll()
  el.addEventListener('scroll', checkScroll)
  const ro = new ResizeObserver(checkScroll)
  ro.observe(el)
  onCleanup(() => {
    el.removeEventListener('scroll', checkScroll)
    ro.disconnect()
  })
})

// Auto-scroll the active tab into view on every activeTabId change —
// not only when the user clicks a tab. Covers route-driven updates
// (sidebar, back/forward, programmatic router.push).
watch(activeTabId, () => {
  scrollActiveIntoView()
})

// Global drag safety net. The per-element `dragend` handler can fail to
// fire if a drag is cancelled outside the window, dropped on an element
// with its own preventDefault-ing handlers, or interrupted by a route
// change that unmounts the tab. When that happens, Chromium keeps its
// internal "drag in progress" flag set and the next mousedown on any
// draggable tab is absorbed as drag-continuation — the click never fires,
// giving the "tabs stopped working" symptom. Listening for `dragend` /
// `drop` on the window guarantees we always reset our state.
onMounted(() => {
  window.addEventListener('dragend', resetDragState)
  window.addEventListener('drop', resetDragState)
})
onBeforeUnmount(() => {
  window.removeEventListener('dragend', resetDragState)
  window.removeEventListener('drop', resetDragState)
  resetDragState()
})

// Tab actions
const activateTab = (tab: WorkspaceTab) => {
  workspace.setActiveTab(tab.id)
  if (tab.entityId) {
    const route = getRouteForTab(tab)
    if (route) router.push(route)
  }
  scrollActiveIntoView()
}

const requestClose = (tab: WorkspaceTab | null) => {
  if (!tab) return
  if (tab.dirty) {
    pendingCloseTab.value = tab
    showDirtyConfirm.value = true
    return
  }
  doCloseTab(tab)
}

const confirmCloseTab = () => {
  if (pendingCloseTab.value) {
    doCloseTab(pendingCloseTab.value)
  }
  showDirtyConfirm.value = false
  pendingCloseTab.value = null
}

const doCloseTab = (tab: WorkspaceTab) => {
  const bufferKey = `${tab.entityType}:${tab.entityId}`
  editBuffer.removeBuffer(bufferKey)
  workspace.closeTab(tab.id)

  if (workspace.activeTab?.entityId) {
    const route = getRouteForTab(workspace.activeTab)
    if (route) router.push(route)
  } else if (tabs.value.length === 0) {
    router.push('/')
  }
  nextTick(checkScroll)
}

const togglePin = (tab: WorkspaceTab | null) => {
  if (!tab) return
  if (tab.pinned) {
    workspace.unpinTab(tab.id)
  } else {
    workspace.pinTab(tab.id)
  }
}

const closeOtherTabs = (current: WorkspaceTab) => {
  const others = tabs.value.filter((t) => t.id !== current.id && !t.pinned)
  for (const tab of others) {
    if (!tab.dirty) doCloseTab(tab)
  }
}

const closeTabsToRight = (current: WorkspaceTab) => {
  const idx = tabs.value.findIndex((t) => t.id === current.id)
  const toClose = tabs.value.slice(idx + 1).filter((t) => !t.pinned)
  for (const tab of toClose) {
    if (!tab.dirty) doCloseTab(tab)
  }
}

const closeTabsToLeft = (current: WorkspaceTab) => {
  const idx = tabs.value.findIndex((t) => t.id === current.id)
  const toClose = tabs.value.slice(0, idx).filter((t) => !t.pinned)
  for (const tab of toClose) {
    if (!tab.dirty) doCloseTab(tab)
  }
}

const closeAllTabs = () => {
  const allTabs = [...tabs.value].filter((t) => !t.pinned)
  for (const tab of allTabs) {
    if (!tab.dirty) doCloseTab(tab)
  }
}

// Drag and drop reorder
const onDragStart = (event: DragEvent, index: number) => {
  dragIndex.value = index
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', String(index))
  }
  // Add drag class after a tick so the dragged element shows properly
  nextTick(() => {
    const el = event.target as HTMLElement
    el.classList.add('dragging')
  })
}

const onDragOver = (_event: DragEvent, index: number) => {
  if (dragIndex.value === null) return
  dragOverIndex.value = index
}

const onDragEnd = () => {
  if (dragIndex.value !== null && dragOverIndex.value !== null && dragIndex.value !== dragOverIndex.value) {
    // Don't allow dropping unpinned tab before pinned tabs
    const fromTab = tabs.value[dragIndex.value]
    const toTab = tabs.value[dragOverIndex.value]
    const canDrop = !(fromTab && !fromTab.pinned && toTab?.pinned)
    if (canDrop) {
      workspace.moveTab(dragIndex.value, dragOverIndex.value)
    }
  }
  resetDragState()
}

function getRouteForTab(tab: WorkspaceTab): string | null {
  const entityRouteMap: Record<string, string> = {
    provider: '/model-providers',
    model: '/model',
    agents: '/agents',
    ai_apps: '/ai-apps',
    promptTemplates: '/prompt-templates',
    rag_tools: '/rag-tools',
    retrieval: '/retrieval',
    collections: '/knowledge-sources',
    evaluation_sets: '/evaluation-sets',
    evaluation_jobs: '/evaluation-jobs',
    assistant_tools: '/assistant-tools',
    api_servers: '/api-servers',
    mcp_servers: '/mcp',
    knowledge_graph: '/knowledge-graph',
    observability_traces: '/observability-traces',
    note_taker: '/note-taker',
  }
  const base = entityRouteMap[tab.entityType]
  if (!base || !tab.entityId) return null
  return `${base}/${tab.entityId}`
}
</script>

<style scoped>
.workspace-tab-bar {
  display: flex;
  align-items: center;
  block-size: 38px;
  min-block-size: 38px;
  background: var(--ds-color-background);
  border-block-end: 1px solid rgba(0,0,0,0.08);
  padding: 0 16px;
  overflow-inline: auto;
  overflow-block: hidden;
  scrollbar-width: none;
}
.workspace-tab-bar::-webkit-scrollbar {
  block-size: 0;
}
.workspace-tabs {
  display: flex;
  align-items: center;
  gap: 1px;
  block-size: 100%;
}
.workspace-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  block-size: 100%;
  padding: 0 10px 0 12px;
  background: transparent;
  cursor: pointer;
  white-space: nowrap;
  max-inline-size: 200px;
  min-inline-size: 0;
  font-size: var(--ds-font-size-caption);
  color: var(--ds-color-secondary-text);
  transition: color 0.15s ease, opacity 0.15s ease;
  position: relative;
  user-select: none;
}
.workspace-tab:hover {
  color: var(--ds-color-primary);
}
.workspace-tab:hover .workspace-tab-icon {
  color: var(--ds-color-primary);
  opacity: 1;
}
.workspace-tab:hover .workspace-tab-close {
  opacity: 0.5;
}
.workspace-tab.active {
  color: var(--ds-color-primary);
  border-block-end: 2px solid var(--ds-color-primary);
  font-weight: 500;
}
.workspace-tab.active .workspace-tab-icon {
  color: var(--ds-color-primary);
  opacity: 1;
}
.workspace-tab.active .workspace-tab-close {
  opacity: 0.3;
}
.workspace-tab.dirty .workspace-tab-label {
  font-style: italic;
}
.workspace-tab.pinned {
  max-inline-size: 160px;
  padding: 0 8px 0 10px;
}
.workspace-tab.pinned .workspace-tab-label {
  font-size: 11px;
}
.workspace-tab.dragging {
  opacity: 0.4;
}
.workspace-tab-pin-badge {
  flex-shrink: 0;
  color: var(--ds-color-primary);
  opacity: 0.5;
  transform: rotate(-45deg);
}
.workspace-tab-icon {
  flex-shrink: 0;
  opacity: 0.6;
  --km-glyph-color: currentColor;
}
.workspace-tab-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-inline-size: 0;
}
.workspace-tab-dirty {
  flex-shrink: 0;
}
.workspace-tab-dirty .dirty-dot {
  inline-size: 6px;
  block-size: 6px;
  border-radius: 50%;
  background: var(--ds-color-warning);
}
.workspace-tab-close {
  flex-shrink: 0;
  opacity: 0;
  transition: opacity 0.15s ease;
  border-radius: 4px;
  inline-size: 18px;
  block-size: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}
.workspace-tab-close:hover {
  opacity: 1 !important;
  background: rgba(0,0,0,0.08);
}
.workspace-scroll-btn {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  inline-size: 24px;
  block-size: 30px;
  cursor: pointer;
  opacity: 0.5;
  transition: opacity 0.15s ease;
}
.workspace-scroll-btn:hover {
  opacity: 1;
}
</style>
