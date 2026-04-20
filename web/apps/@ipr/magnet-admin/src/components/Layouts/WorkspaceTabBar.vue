<template lang="pug">
.workspace-tab-bar(v-if='tabs.length > 0', ref='tabBarRef')
  .workspace-scroll-btn.workspace-scroll-btn--left(v-if='showScrollLeft', @click='scrollLeftBy')
    q-icon(name='chevron_left', size='16px')
  .workspace-tabs(ref='tabsContainerRef')
    .workspace-tab(
      v-for='(tab, index) in tabs',
      :key='tab.id',
      :class='tabClass(tab)',
      :draggable='!tab.pinned',
      @click='activateTab(tab)',
      @mousedown.middle.prevent='requestClose(tab)',
      @contextmenu.prevent='onContextMenu($event, tab)',
      @dragstart='onDragStart($event, index)',
      @dragover.prevent='onDragOver($event, index)',
      @dragend='onDragEnd',
      :data-index='index',
      :data-tab-id='tab.id'
    )
      q-icon.workspace-tab-icon(:name='entityIcon(tab)', size='14px')
      .workspace-tab-label {{ tab.label }}
      q-tooltip(v-if='isLabelTruncated(tab)', anchor='top middle', self='bottom middle', :delay='600') {{ getTooltip(tab) }}
      q-icon.workspace-tab-pin-badge(v-if='tab.pinned', name='fas fa-thumbtack', size='8px')
      .workspace-tab-dirty(v-if='tab.dirty && !tab.pinned')
        .dirty-dot
      q-icon.workspace-tab-close(
        v-if='!tab.pinned',
        name='close',
        size='12px',
        @click.stop='requestClose(tab)'
      )
  .workspace-scroll-btn.workspace-scroll-btn--right(v-if='showScrollRight', @click='scrollRightBy')
    q-icon(name='chevron_right', size='16px')

  //- Context menu. Mount only while open (`v-if`) so Quasar's
  //- `pickAnchorEl` never sees a null `:target` on the initial mount —
  //- it used to throw "Anchor: target 'null' not found" at app startup,
  //- which cascaded into Quasar's event-listener state and silently
  //- suppressed subsequent clicks on the tab bar.
  q-menu(v-if='contextMenuVisible', v-model='contextMenuVisible', :target='contextMenuTarget', context-menu, no-parent-event)
    q-list(dense, style='min-width: 180px')
      q-item(clickable, v-close-popup, @click='requestClose(contextMenuTab)')
        q-item-section
          .row.items-center.q-gap-sm
            q-icon(name='close', size='14px')
            span {{ m.workspace_close() }}
      q-separator
      q-item(clickable, v-close-popup, @click='togglePin(contextMenuTab)')
        q-item-section
          .row.items-center.q-gap-sm
            q-icon(:name='contextMenuTab?.pinned ? "fas fa-thumbtack" : "fas fa-thumbtack"', size='14px')
            span {{ contextMenuTab?.pinned ? m.workspace_unpin() : m.workspace_pinTab() }}
      q-separator
      q-item(clickable, v-close-popup, @click='closeOtherTabs')
        q-item-section {{ m.workspace_closeOthers() }}
      q-item(clickable, v-close-popup, @click='closeTabsToRight')
        q-item-section {{ m.workspace_closeToRight() }}
      q-item(clickable, v-close-popup, @click='closeTabsToLeft')
        q-item-section {{ m.workspace_closeToLeft() }}
      q-separator
      q-item(clickable, v-close-popup, @click='closeAllTabs')
        q-item-section {{ m.workspace_closeAll() }}

//- Dirty confirmation dialog
km-popup-confirm(
  :visible='showDirtyConfirm',
  :confirmButtonLabel='m.common_closeWithoutSaving()',
  :cancelButtonLabel='m.common_cancel()',
  notificationIcon='fas fa-triangle-exclamation',
  @confirm='confirmCloseTab',
  @cancel='showDirtyConfirm = false'
)
  .row.item-center.justify-center.km-heading-7.q-mb-md {{ m.workspace_unsavedChanges() }}
  .row.text-center.justify-center {{ m.workspace_unsavedTabMessage() }}
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
  agents: 'fa fa-robot',
  promptTemplates: 'fa fa-comment-dots',
  rag_tools: 'fas fa-file-circle-question',
  retrieval: 'fas fa-file-circle-question',
  ai_apps: 'fas fa-wand-magic-sparkles',
  api_servers: 'fas fa-arrow-right-arrow-left',
  mcp_servers: 'fas fa-server',
  collections: 'fas fa-book',
  provider: 'fas fa-circle-nodes',
  model: 'fas fa-circle-nodes',
  evaluation_sets: 'fas fa-table-list',
  evaluation_jobs: 'fas fa-clipboard-check',
  assistant_tools: 'fas fa-wrench',
  knowledge_graph: 'o_hub',
  observability_traces: 'fas fa-shoe-prints',
  api_keys: 'fas fa-lock',
  note_taker: 'fas fa-microphone',
}

function entityIcon(tab: WorkspaceTab): string {
  return entityIconMap[tab.entityType] || tab.icon || 'fas fa-file'
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
const contextMenuVisible = ref(false)
const contextMenuTarget = ref<EventTarget | null>(null)
const contextMenuTab = ref<WorkspaceTab | null>(null)
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

// Context menu. Every right-click sets a fresh target before opening, so
// we never show the menu against a stale ref — no null-target needed on
// close. (We tried nulling `contextMenuTarget` on close before; that made
// q-menu throw "Anchor: target 'null' not found" on every menu dismiss,
// which left Quasar's event listeners in a partial state that silently
// swallowed subsequent clicks on the tab bar — the "tabs stop working"
// bug reported by users. Leaving the previous target in place is safe
// because the next open always overwrites it.)
const onContextMenu = (event: MouseEvent, tab: WorkspaceTab) => {
  contextMenuTab.value = tab
  contextMenuTarget.value = event.target as EventTarget
  contextMenuVisible.value = true
}

const togglePin = (tab: WorkspaceTab | null) => {
  if (!tab) return
  if (tab.pinned) {
    workspace.unpinTab(tab.id)
  } else {
    workspace.pinTab(tab.id)
  }
}

const closeOtherTabs = () => {
  const current = contextMenuTab.value
  if (!current) return
  const others = tabs.value.filter((t) => t.id !== current.id && !t.pinned)
  for (const tab of others) {
    if (!tab.dirty) doCloseTab(tab)
  }
}

const closeTabsToRight = () => {
  const current = contextMenuTab.value
  if (!current) return
  const idx = tabs.value.findIndex((t) => t.id === current.id)
  const toClose = tabs.value.slice(idx + 1).filter((t) => !t.pinned)
  for (const tab of toClose) {
    if (!tab.dirty) doCloseTab(tab)
  }
}

const closeTabsToLeft = () => {
  const current = contextMenuTab.value
  if (!current) return
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

<style lang="stylus" scoped>
.workspace-tab-bar
  display flex
  align-items center
  height 38px
  min-height 38px
  background var(--q-background)
  border-bottom 1px solid rgba(0, 0, 0, 0.08)
  padding 0 16px
  overflow-x auto
  overflow-y hidden
  scrollbar-width none
  &::-webkit-scrollbar
    height 0

.workspace-tabs
  display flex
  align-items center
  gap 1px
  height 100%

.workspace-tab
  display flex
  align-items center
  gap 6px
  height 100%
  padding 0 10px 0 12px
  background transparent
  cursor pointer
  white-space nowrap
  max-width 200px
  min-width 0
  font-size var(--km-font-size-caption)
  color var(--q-secondary-text)
  transition color 0.15s ease, opacity 0.15s ease
  position relative
  user-select none
  &:hover
    color var(--q-primary)
    .workspace-tab-icon
      color var(--q-primary)
      opacity 1
    .workspace-tab-close
      opacity 0.5
  &.active
    color var(--q-primary)
    border-bottom 2px solid var(--q-primary)
    font-weight 500
    .workspace-tab-icon
      color var(--q-primary)
      opacity 1
    .workspace-tab-close
      opacity 0.3
  &.dirty .workspace-tab-label
    font-style italic
  &.pinned
    max-width 160px
    padding 0 8px 0 10px
    .workspace-tab-label
      font-size 11px
  &.dragging
    opacity 0.4

.workspace-tab-pin-badge
  flex-shrink 0
  color var(--q-primary)
  opacity 0.5
  transform rotate(-45deg)

.workspace-tab-icon
  flex-shrink 0
  opacity 0.6

.workspace-tab-label
  overflow hidden
  text-overflow ellipsis
  white-space nowrap
  flex 1
  min-width 0

.workspace-tab-dirty
  flex-shrink 0
  .dirty-dot
    width 6px
    height 6px
    border-radius 50%
    background var(--q-warning)

.workspace-tab-close
  flex-shrink 0
  opacity 0
  transition opacity 0.15s ease
  border-radius 4px
  padding 2px
  &:hover
    opacity 1 !important
    background rgba(0, 0, 0, 0.08)

.workspace-scroll-btn
  flex-shrink 0
  display flex
  align-items center
  justify-content center
  width 24px
  height 30px
  cursor pointer
  opacity 0.5
  transition opacity 0.15s ease
  &:hover
    opacity 1
</style>
