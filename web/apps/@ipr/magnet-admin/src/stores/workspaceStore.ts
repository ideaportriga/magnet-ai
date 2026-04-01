import { defineStore } from 'pinia'
import { computed, ref, watch } from 'vue'
import { useEditBufferStore } from './editBufferStore'

const STORAGE_KEY = 'magnet-workspace-tabs'

export interface WorkspaceTab {
  id: string
  entityType: string
  entityId: string | null
  label: string
  icon?: string
  dirty: boolean
  pinned?: boolean
}

function loadPersistedTabs(): { tabs: WorkspaceTab[]; activeTabId: string | null } {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return { tabs: [], activeTabId: null }
    const parsed = JSON.parse(raw)
    // Reset dirty flags on restore — server state may have changed
    const tabs = (parsed.tabs ?? []).map((t: WorkspaceTab) => ({ ...t, dirty: false }))
    return { tabs, activeTabId: parsed.activeTabId ?? null }
  } catch {
    return { tabs: [], activeTabId: null }
  }
}

export const useWorkspaceStore = defineStore('workspace', () => {
  const persisted = loadPersistedTabs()
  const tabs = ref<WorkspaceTab[]>(persisted.tabs)
  const activeTabId = ref<string | null>(persisted.activeTabId)

  const activeTab = computed(() =>
    tabs.value.find((t) => t.id === activeTabId.value) ?? null,
  )

  function openTab(entityType: string, entityId: string | null, label: string, icon?: string): string {
    const existing = tabs.value.find(
      (t) => t.entityType === entityType && t.entityId === entityId,
    )
    if (existing) {
      activeTabId.value = existing.id
      return existing.id
    }

    const id = crypto.randomUUID()
    tabs.value.push({ id, entityType, entityId, label, icon, dirty: false })
    activeTabId.value = id
    return id
  }

  function closeTab(tabId: string): boolean {
    const idx = tabs.value.findIndex((t) => t.id === tabId)
    if (idx === -1) return false

    const tab = tabs.value[idx]
    const wasDirty = tab.dirty

    // Clean up editBuffer for this tab's entity to prevent orphaned entries
    if (tab.entityType && tab.entityId) {
      try {
        const editBuffer = useEditBufferStore()
        editBuffer.removeBuffer(`${tab.entityType}:${tab.entityId}`)
      } catch {
        // editBuffer not initialized yet — safe to ignore
      }
    }

    tabs.value.splice(idx, 1)

    if (activeTabId.value === tabId) {
      activeTabId.value = tabs.value[Math.min(idx, tabs.value.length - 1)]?.id ?? null
    }

    return wasDirty
  }

  function setActiveTab(tabId: string) {
    if (tabs.value.some((t) => t.id === tabId)) {
      activeTabId.value = tabId
    }
  }

  function markDirty(tabId: string, dirty: boolean) {
    const tab = tabs.value.find((t) => t.id === tabId)
    if (tab) tab.dirty = dirty
  }

  function updateTabLabel(tabId: string, label: string) {
    const tab = tabs.value.find((t) => t.id === tabId)
    if (tab) tab.label = label
  }

  function pinTab(tabId: string) {
    const idx = tabs.value.findIndex((t) => t.id === tabId)
    if (idx === -1) return
    tabs.value[idx].pinned = true
    // Move to end of pinned section
    const tab = tabs.value.splice(idx, 1)[0]
    const lastPinnedIdx = tabs.value.filter((t) => t.pinned).length
    tabs.value.splice(lastPinnedIdx, 0, tab)
  }

  function unpinTab(tabId: string) {
    const idx = tabs.value.findIndex((t) => t.id === tabId)
    if (idx === -1) return
    tabs.value[idx].pinned = false
    // Move to start of unpinned section
    const tab = tabs.value.splice(idx, 1)[0]
    const lastPinnedIdx = tabs.value.filter((t) => t.pinned).length
    tabs.value.splice(lastPinnedIdx, 0, tab)
  }

  function moveTab(fromIndex: number, toIndex: number) {
    if (fromIndex === toIndex) return
    if (fromIndex < 0 || toIndex < 0) return
    if (fromIndex >= tabs.value.length || toIndex >= tabs.value.length) return
    const tab = tabs.value.splice(fromIndex, 1)[0]
    tabs.value.splice(toIndex, 0, tab)
  }

  const hasDirtyTabs = computed(() => tabs.value.some((t) => t.dirty))

  // Persist to localStorage on any change
  watch(
    [tabs, activeTabId],
    () => {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify({
          tabs: tabs.value.map((t) => ({ ...t, dirty: false })),
          activeTabId: activeTabId.value,
        }))
      } catch {
        // localStorage full or unavailable
      }
    },
    { deep: true },
  )

  // Warn user before closing browser tab with unsaved changes
  function onBeforeUnload(event: BeforeUnloadEvent) {
    if (hasDirtyTabs.value) {
      event.preventDefault()
    }
  }

  if (typeof window !== 'undefined') {
    window.addEventListener('beforeunload', onBeforeUnload)
  }

  return {
    tabs,
    activeTabId,
    activeTab,
    hasDirtyTabs,
    openTab,
    closeTab,
    setActiveTab,
    markDirty,
    updateTabLabel,
    pinTab,
    unpinTab,
    moveTab,
  }
})
