<template>
  <div class="cluster overflow-hidden full-height" data-wrap="no">
    <div class="flex-1 flex full-height overflow-hidden" style="justify-content: center; flex-wrap: nowrap">
      <div class="flex-none full-width">
        <div class="full-height pb-md relative-position px-md">
          <!-- Graph Header Card -->
          <div class="kg-header-card mt-lg mb-sm">
            <div class="kg-header-content">
              <!-- Graph Icon & Info Section -->
              <div class="kg-header-main">
                <div class="kg-icon-wrapper">
                  <km-glyph name="graph" size="22px" tone="brand" />
                </div>
                <div class="kg-info-section">
                  <div class="kg-name-row">
                    <km-input-flat
                      class="kg-name-input km-heading-4 text-black"
                      :placeholder="m.knowledgeGraph_namePlaceholder()"
                      :model-value="name"
                      @change="onNameChange"
                    />
                  </div>
                  <div class="kg-description-row">
                    <km-input-flat
                      class="kg-description-input km-description text-secondary-text"
                      :placeholder="m.knowledgeGraph_descriptionPlaceholder()"
                      :model-value="description"
                      @change="onDescriptionChange"
                    />
                  </div>
                </div>
              </div>

              <!-- System Name & Actions -->
              <div class="kg-header-actions">
                <div class="kg-system-name-section">
                  <div class="kg-system-name-label">
                    <km-glyph name="o_key" size="12px" class="mr-xs" />
                    <span>{{ m.knowledgeGraph_systemId() }}</span>
                    <km-glyph name="info" size="12px" class="kg-info-icon">
                      <km-tooltip class="bg-white block-shadow text-secondary-text km-description" self="top middle" :offset="[0, 8]">
                        {{ m.knowledgeGraph_systemNameHint() }}
                      </km-tooltip>
                    </km-glyph>
                  </div>
                  <km-input-flat
                    class="kg-system-name-input km-description text-black"
                    :placeholder="m.placeholder_enterSystemName()"
                    :model-value="systemName"
                    @change="onSystemNameChange"
                    @focus="showInfo = true"
                    @blur="showInfo = false"
                  />
                  <transition name="kg-fade">
                    <div v-if="showInfo" class="kg-system-name-hint">
                      <km-glyph name="o_lightbulb" size="11px" />
                      <span>{{ m.knowledgeGraph_setOnce() }}</span>
                    </div>
                  </transition>
                </div>

                <div class="kg-action-divider" />

                <button class="test-retrieval-btn" @click="openRetrievalDrawer">
                  <span class="btn-label">{{ m.knowledgeGraph_testRetrieval() }}</span>
                  <km-glyph name="arrow_forward" size="16px" class="btn-arrow" />
                </button>
              </div>
            </div>
          </div>
          <!-- Missing Embedding Model Warning -->
          <div
            v-if="!hasEmbeddingModel && !loading"
            class="cluster no-wrap mt-md bg-red-1 text-red-9 px-sm py-md border-radius-8 cursor-pointer mb-md ba-error"
            data-wrap="no"
            @click="goToSettings"
          >
            <km-glyph name="warning" size="xs" class="mr-sm" />
            <div class="text-caption text-weight-medium">{{ m.knowledgeGraph_noEmbeddingModel() }}</div>
            <div class="km-space" />
            <div class="cluster" data-gap="xs" style="color: var(--km-red-8)">
              <span class="text-caption">{{ m.common_goToSettings() }}</span>
              <km-glyph name="chevron_right" size="xs" />
            </div>
          </div>
          <div class="stack no-wrap ba-border bg-white border-radius-12 p-lg" data-gap="0" style="min-inline-size: 300px; block-size: calc(100vb - 190px)">
            <div class="cluster bb-border pb-sm">
              <km-tabs
                :model-value="activeTab"
                class="flex-1"
                narrow-indicator
                dense
                align="left"
                no-caps
                content-class="km-tabs"
                @update:model-value="onTabAttemptChange"
              >
                <km-tab name="sources" :label="m.knowledgeGraph_sources()" />
                <km-tab name="explorer" :label="m.knowledgeGraph_dataExplorer()" />
                <km-tab name="metadata" :label="m.knowledgeGraph_metadataStudio()" :alert="metadataUnsaved" alert-color="orange-9" />
                <km-tab name="entityExtraction" :label="m.knowledgeGraph_entityExtraction()" />
                <km-tab name="contentProfiles" :label="m.knowledgeGraph_contentProfiles()" />
                <km-tab name="retrieval" :label="m.knowledgeGraph_retrieval()" :alert="retrievalUnsaved" alert-color="orange-9" />
                <km-tab name="settings" :label="m.common_settings()" :alert="!hasEmbeddingModel && !loading" alert-color="orange-9" />
              </km-tabs>
            </div>

            <div class="flex-1 overflow-auto mt-lg" style="min-block-size: 0">
              <sources-tab
                v-show="activeTab === 'sources'"
                v-if="graphDetails"
                ref="sourcesRef"
                :graph-id="graphId"
                :graph-details="graphDetails"
                @refresh="handleSourcesRefresh"
              />
              <settings-tab
                v-show="activeTab === 'settings'"
                v-if="graphDetails"
                :graph-id="graphId"
                :graph-details="graphDetails"
                @refresh="fetchGraphDetails"
              />
              <content-profiles-tab
                v-show="activeTab === 'contentProfiles'"
                v-if="graphDetails"
                :graph-id="graphId"
                :graph-details="graphDetails"
                @refresh="fetchGraphDetails"
              />
              <data-explorer-tab
                v-if="graphDetails && activeTab === 'explorer'"
                ref="explorerRef"
                :graph-id="graphId"
                :graph-details="graphDetails"
              />
              <retrieval-tab
                v-show="activeTab === 'retrieval'"
                v-if="graphDetails"
                ref="retrievalRef"
                :graph-id="graphId"
                :graph-details="graphDetails"
                @unsaved-change="retrievalUnsaved = $event"
                @update-graph="updateGraph"
              />
              <metadata-tab
                v-show="activeTab === 'metadata'"
                v-if="graphDetails"
                ref="metadataRef"
                :graph-id="graphId"
                :graph-details="graphDetails"
                @unsaved-change="metadataUnsaved = $event"
                @refresh="fetchGraphDetails"
              />
              <entity-extraction-tab
                v-show="activeTab === 'entityExtraction'"
                v-if="graphDetails"
                :graph-id="graphId"
                :graph-details="graphDetails"
                @refresh="fetchGraphDetails"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="flex-none">
      <retrieval-test-drawer
        v-show="drawerOpen && drawerType === 'retrieval'"
        :graph-id="graphId"
        :output-format="retrievalOutputFormat"
        :is-active="drawerOpen && drawerType === 'retrieval'"
        @close="drawerOpen = false"
      />
    </div>
  </div>

  <!-- Drag-and-Drop Overlay -->
  <div v-if="isDragging" class="kg-dnd-overlay">
    <div class="kg-dnd-content">
      <div class="kg-dnd-icon-wrapper">
        <km-glyph name="cloud_upload" class="kg-dnd-icon" />
      </div>
      <div class="kg-dnd-title">{{ m.knowledgeGraph_dropFilesHere() }}</div>
      <div class="kg-dnd-subtitle">{{ m.knowledgeGraph_releaseToUpload() }}</div>
    </div>
  </div>

  <!-- Leave Retrieval Tab Confirmation -->
  <km-popup-confirm
    :visible="showRetrievalLeaveDialog"
    :confirm-button-label="m.common_saveAndSwitch()"
    :confirm-button-label2="m.common_dontSave()"
    confirm-button-type2="secondary"
    :cancel-button-label="m.knowledgeGraph_stayOnRetrieval()"
    notification-icon="warning"
    @confirm="handleRetrievalSaveAndSwitch"
    @confirm2="handleRetrievalDiscard"
    @cancel="handleRetrievalStay"
  >
    <div class="cluster km-heading-7 mb-md" data-justify="center">{{ m.common_unsavedChanges() }}</div>
    <div class="cluster text-center" data-justify="center">{{ m.knowledgeGraph_unsavedRetrievalChanges() }}</div>
  </km-popup-confirm>

  <!-- Leave Metadata Tab Confirmation -->
  <km-popup-confirm
    :visible="showMetadataLeaveDialog"
    :confirm-button-label="m.common_saveAndSwitch()"
    :confirm-button-label2="m.common_dontSave()"
    confirm-button-type2="secondary"
    :cancel-button-label="m.knowledgeGraph_stayOnMetadata()"
    notification-icon="warning"
    @confirm="handleMetadataSaveAndSwitch"
    @confirm2="handleMetadataDiscard"
    @cancel="handleMetadataStay"
  >
    <div class="cluster km-heading-7 mb-md" data-justify="center">{{ m.common_unsavedChanges() }}</div>
    <div class="cluster text-center" data-justify="center">{{ m.knowledgeGraph_unsavedMetadataChanges() }}</div>
  </km-popup-confirm>
</template>

<script setup lang="ts">
import { fetchData } from '@shared'
import { m } from '@/paraglide/messages'
import { computed, onActivated, onBeforeUnmount, onMounted, provide, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/stores/appStore'
import { useEntityQueries } from '@/queries/entities'
import { useNotify } from '@/composables/useNotify'
import ContentProfilesTab from './ContentProfiles/ContentProfilesTab.vue'
import DataExplorerTab from './DataExplorer/DataExplorerTab.vue'
import EntityExtractionTab from './EntityExtraction/EntityExtractionTab.vue'
import MetadataTab from './Metadata/MetadataTab.vue'
import RetrievalTestDrawer from './Playground/RetrievalTestDrawer.vue'
import RetrievalTab from './Retrieval/RetrievalTab.vue'
import SettingsTab from './Settings/SettingsTab.vue'
import SourcesTab from './Sources/SourcesTab.vue'
import type { KnowledgeGraphDetails } from './types'

const route = useRoute()
const appStore = useAppStore()
const queries = useEntityQueries()
const { notifySuccess, notifyError, notifyWarning } = useNotify()

const graphId = ref(route.params.id)
const graphDetails = ref<KnowledgeGraphDetails | null>(null)
const activeTab = ref<'sources' | 'settings' | 'contentProfiles' | 'explorer' | 'retrieval' | 'metadata' | 'entityExtraction'>('sources')
const name = ref('')
const description = ref('')
const systemName = ref('')
const showInfo = ref(false)

// TanStack Query: fetch graph detail (auto-fetches when graphId changes)
const { data: graphData, isLoading: loading, refetch: refetchGraph } = queries.knowledge_graph.useDetail(graphId)
// Sync TQ data into local refs consumed by child components
watch(
  graphData,
  (newData) => {
    if (newData) {
      graphDetails.value = newData as KnowledgeGraphDetails
      name.value = newData.name || ''
      systemName.value = newData.system_name || ''
      description.value = newData.description || ''
    }
  },
  { immediate: true }
)

onActivated(() => {
  graphId.value = route.params.id
  // Re-sync local refs from TanStack Query data when KeepAlive reactivates this component (multi-tab support)
  if (graphData.value) {
    graphDetails.value = graphData.value as KnowledgeGraphDetails
    name.value = graphData.value.name || ''
    systemName.value = graphData.value.system_name || ''
    description.value = graphData.value.description || ''
  }
})

// TanStack Query: update mutation
const { mutateAsync: updateGraphMutation } = queries.knowledge_graph.useUpdate()

// Check if the knowledge graph has an embedding model configured
const hasEmbeddingModel = computed(() => {
  return !!graphDetails.value?.settings?.indexing?.embedding_model
})

// Get output format from retrieval settings (defaults to markdown)
const retrievalOutputFormat = computed(() => {
  return graphDetails.value?.settings?.retrieval_tools?.exit?.outputFormat || 'markdown'
})

// Navigate to settings tab when warning banner is clicked
const goToSettings = () => {
  activeTab.value = 'settings'
}
const retrievalUnsaved = ref(false)
const metadataUnsaved = ref(false)
const intendedTab = ref<'sources' | 'settings' | 'contentProfiles' | 'explorer' | 'retrieval' | 'metadata' | 'entityExtraction' | null>(null)
const showRetrievalLeaveDialog = ref(false)
const showMetadataLeaveDialog = ref(false)
const retrievalRef = ref<any>(null)
const metadataRef = ref<any>(null)

const onTabAttemptChange = async (
  nextTab: 'sources' | 'settings' | 'contentProfiles' | 'explorer' | 'retrieval' | 'metadata' | 'entityExtraction'
) => {
  // Guard when leaving Retrieval tab with unsaved changes
  if (activeTab.value === 'retrieval' && retrievalUnsaved.value && nextTab !== 'retrieval') {
    intendedTab.value = nextTab
    showRetrievalLeaveDialog.value = true
    return
  }
  // Guard when leaving Metadata tab with unsaved changes
  if (activeTab.value === 'metadata' && metadataUnsaved.value && nextTab !== 'metadata') {
    intendedTab.value = nextTab
    showMetadataLeaveDialog.value = true
    return
  }
  activeTab.value = nextTab
}

// Handlers for unsaved changes dialog
const handleRetrievalSaveAndSwitch = async () => {
  await retrievalRef.value?.save?.()
  retrievalUnsaved.value = false
  activeTab.value = intendedTab.value || activeTab.value
  intendedTab.value = null
  showRetrievalLeaveDialog.value = false
}

const handleRetrievalDiscard = () => {
  retrievalRef.value?.discard?.()
  retrievalUnsaved.value = false
  activeTab.value = intendedTab.value || activeTab.value
  intendedTab.value = null
  showRetrievalLeaveDialog.value = false
}

const handleRetrievalStay = () => {
  intendedTab.value = null
  showRetrievalLeaveDialog.value = false
}

// Handlers for metadata unsaved changes dialog
const handleMetadataSaveAndSwitch = async () => {
  await metadataRef.value?.save?.()
  metadataUnsaved.value = false
  activeTab.value = intendedTab.value || activeTab.value
  intendedTab.value = null
  showMetadataLeaveDialog.value = false
}

const handleMetadataDiscard = () => {
  metadataRef.value?.discard?.()
  metadataUnsaved.value = false
  activeTab.value = intendedTab.value || activeTab.value
  intendedTab.value = null
  showMetadataLeaveDialog.value = false
}

const handleMetadataStay = () => {
  intendedTab.value = null
  showMetadataLeaveDialog.value = false
}

const sourcesRef = ref<any>(null)
const explorerRef = ref<any>(null)
const drawerOpen = ref(false)
const drawerType = ref<'source' | 'retrieval'>('source')

// Kept as thin wrapper so child components can still call @refresh="fetchGraphDetails"
const fetchGraphDetails = () => refetchGraph()

const handleSourcesRefresh = async () => {
  await fetchGraphDetails()
  explorerRef.value?.refresh?.()
  metadataRef.value?.refresh?.()
}

// Drag-and-drop upload state
const isDragging = ref(false)
const dragCounter = ref(0)
let dragHideTimeout: number | undefined

// Provide a global uploading flag for child cells to react to
const kgUploading = ref(false)
provide('kgUploading', kgUploading)

// Provide a flag to disable global DnD when modal dialogs (e.g., Upload) are open
const kgDndDisabled = ref(false)
provide('kgDndDisabled', kgDndDisabled)

const refreshSources = () => {
  sourcesRef.value?.refresh?.()
}
provide('kgRefreshSources', refreshSources)

// When DnD is disabled, immediately hide overlay and reset counters
watch(
  kgDndDisabled,
  (disabled) => {
    if (disabled) {
      if (dragHideTimeout !== undefined) window.clearTimeout(dragHideTimeout)
      isDragging.value = false
      dragCounter.value = 0
    }
  },
  { flush: 'sync' }
)

// Watch for upload completion to refresh data (handles both DnD and UploadDialog)
watch(kgUploading, (uploading) => {
  if (!uploading) {
    refreshSources()
    explorerRef.value?.refresh?.()
    metadataRef.value?.refresh?.()
    fetchGraphDetails()
  }
})

const openRetrievalDrawer = () => {
  drawerType.value = 'retrieval'
  drawerOpen.value = true
}

const updateGraph = async (payload: Record<string, any>) => {
  if (!graphId.value) return
  try {
    await updateGraphMutation({ id: graphId.value, data: payload })
    // TanStack Query invalidates + refetches the detail query automatically on success
  } catch (e) {
    notifyError(m.knowledgeGraph_failedToSaveChanges())
  }
}

const onNameChange = async (val: string) => {
  name.value = typeof val === 'string' ? val.trim() : val
  await updateGraph({ name: name.value })
}

const onDescriptionChange = async (val: string) => {
  description.value = typeof val === 'string' ? val.trim() : val
  await updateGraph({ description: description.value })
}

const onSystemNameChange = async (val: string) => {
  systemName.value = typeof val === 'string' ? val.trim() : val
  await updateGraph({ system_name: systemName.value })
}

onMounted(() => {
  // Check if tab query parameter is set
  if (route.query.tab === 'explorer') {
    activeTab.value = 'explorer'
  } else if (route.query.tab === 'retrieval') {
    activeTab.value = 'retrieval'
  } else if (route.query.tab === 'metadata') {
    activeTab.value = 'metadata'
  }
  // Window-level drag and drop listeners to avoid child element churn flicker
  window.addEventListener('dragenter', onDragEnter, { passive: false })
  window.addEventListener('dragover', onDragOver, { passive: false })
  window.addEventListener('dragleave', onDragLeave as EventListener, { passive: false })
  window.addEventListener('drop', onDrop, { passive: false })
})

onBeforeUnmount(() => {
  window.removeEventListener('dragenter', onDragEnter as EventListener)
  window.removeEventListener('dragover', onDragOver as EventListener)
  window.removeEventListener('dragleave', onDragLeave as EventListener)
  window.removeEventListener('drop', onDrop as EventListener)
  if (dragHideTimeout !== undefined) {
    window.clearTimeout(dragHideTimeout)
  }
})

// Drag and Drop Helpers + Handlers
const eventHasFiles = (e: DragEvent) => {
  const types = e.dataTransfer?.types
  return !!types && Array.from(types).includes('Files')
}

const onDragEnter = (event: DragEvent) => {
  if (kgDndDisabled.value) {
    event.preventDefault()
    return
  }
  if (!eventHasFiles(event)) return
  event.preventDefault()
  dragCounter.value += 1
  isDragging.value = true
}

const onDragOver = (event: DragEvent) => {
  if (kgDndDisabled.value) {
    event.preventDefault()
    return
  }
  if (!eventHasFiles(event)) return
  event.preventDefault()
  if (event.dataTransfer) event.dataTransfer.dropEffect = 'copy'
  // keep overlay visible while moving
  if (dragHideTimeout !== undefined) window.clearTimeout(dragHideTimeout)
}

const onDragLeave = (event: DragEvent) => {
  if (kgDndDisabled.value) {
    event.preventDefault()
    return
  }
  if (!eventHasFiles(event)) return
  event.preventDefault()
  dragCounter.value = Math.max(0, dragCounter.value - 1)
  if (dragCounter.value === 0) {
    if (dragHideTimeout !== undefined) window.clearTimeout(dragHideTimeout)
    dragHideTimeout = window.setTimeout(() => {
      isDragging.value = false
    }, 80)
  }
}

const uploadFiles = async (files: File[]) => {
  if (!files || files.length === 0) return

  // Toggle uploading state to show spinner in Sources table
  kgUploading.value = true

  try {
    const endpoint = appStore.config.api.aiBridge.urlAdmin
    const results: any[] = []
    let successCount = 0
    let errorCount = 0
    let errorMessage = ''

    for (const file of files) {
      try {
        const formData = new FormData()
        formData.append('data', file)

        const response = await fetchData({
          endpoint,
          service: `knowledge_graphs/${graphId.value}/upload`,
          method: 'POST',
          credentials: 'include',
          body: formData,
          headers: {},
        })

        if (response.ok) {
          const result = await response.json()
          results.push(result)
          successCount++
          // Refresh sources after first successful upload to show the new source immediately
          if (successCount === 1) {
            refreshSources()
          }
        } else {
          errorCount++

          const error = JSON.parse(response.error.message).error
          if (error && !errorMessage) {
            errorMessage = error
          } else if (error && errorMessage && errorMessage !== error) {
            errorMessage = 'Failed to upload one or more files. Please try again.'
          }
        }
      } catch (err) {
        errorCount++
      }
    }

    // Show success or error notification
    if (errorCount === 0) {
      notifySuccess(successCount > 1 ? m.knowledgeGraph_uploadedFilesPlural({ count: String(successCount) }) : m.knowledgeGraph_uploadedFiles({ count: String(successCount) }))
    } else if (successCount > 0) {
      notifyWarning(`Uploaded ${successCount} file${successCount > 1 ? 's' : ''}, ${errorCount} failed`)
    } else {
      notifyError(errorMessage || m.knowledgeGraph_failedToUploadFiles())
    }

    // Refresh sources, explorer, and details to reflect uploaded docs
    if (successCount > 0) {
      refreshSources()
      explorerRef.value?.refresh?.()
      fetchGraphDetails()
    }
  } catch (error) {
    notifyError(m.knowledgeGraph_failedToUploadFiles())
  } finally {
    kgUploading.value = false
  }
}

const onDrop = async (event: DragEvent) => {
  if (kgDndDisabled.value) {
    event.preventDefault()
    return
  }
  if (!eventHasFiles(event)) return
  event.preventDefault()
  if (dragHideTimeout !== undefined) window.clearTimeout(dragHideTimeout)
  isDragging.value = false
  dragCounter.value = 0
  const dt = event.dataTransfer
  if (!dt) return
  const files: File[] = dt.files ? Array.from(dt.files) : []
  if (files.length > 0) {
    await uploadFiles(files)
  }
}
</script>

<style scoped>
.kg-dnd-overlay {
  position: fixed;
  inset: 0;
  z-index: 5000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(7, 14, 30, 0.45); /* intentional dark overlay */
  backdrop-filter: blur(6px);
  pointer-events: none;
  animation: kg-overlay-fade-in 0.15s ease-out;
  will-change: opacity;
}
@keyframes kg-overlay-fade-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.kg-dnd-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  inline-size: 480px;
  max-inline-size: calc(100vi - 48px);
  padding: 48px 32px;
  border-radius: 20px;
  background: var(--ds-color-white);
  border: none;
  outline: 3px dashed color-mix(in srgb, var(--ds-color-primary) 60%, transparent);
  outline-offset: -12px;
  box-shadow:
    0 20px 50px rgba(0, 0, 0, 0.2),
    inset 0 0 0 1px var(--ds-color-primary-light);
  animation: kg-content-scale-in 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
  transform-origin: center;
  will-change: transform, opacity;
  transform: translateZ(0);
  backface-visibility: hidden;
}
@keyframes kg-content-scale-in {
  from {
    transform: scale(0.9);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}

.kg-dnd-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  inline-size: 96px;
  block-size: 96px;
  border-radius: var(--ds-radius-full);
  background: linear-gradient(
    135deg,
    color-mix(in srgb, var(--ds-color-primary) 8%, transparent) 0%,
    color-mix(in srgb, var(--ds-color-primary) 15%, transparent) 100%
  );
  margin-block-end: 8px;
}

.kg-dnd-icon {
  font-size: 48px !important;
  color: var(--ds-color-primary);
}

.kg-dnd-title {
  font-size: 26px;
  font-weight: 600;
  color: var(--ds-color-black);
  letter-spacing: -0.3px;
  margin: 0;
  line-height: 1.2;
}

.kg-dnd-subtitle {
  font-size: 15px;
  color: var(--ds-color-label);
  margin: 0;
  font-weight: 400;
  letter-spacing: 0.1px;
}

/* ============================================
   Knowledge Graph Header Card Styles
   ============================================ */

.kg-header-card {
  background: linear-gradient(135deg, var(--ds-color-white) 0%, var(--ds-color-background) 100%);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: var(--ds-radius-xl);
  padding: 16px 24px;
  transition: border-color 0.25s ease;
}
.kg-header-card:hover {
  border-color: rgba(0, 0, 0, 0.1);
}

.kg-header-content {
  display: flex;
  align-items: flex-start;
  gap: 20px;
}

.kg-header-main {
  flex: 1;
  display: flex;
  align-items: flex-start;
  gap: 16px;
  min-inline-size: 0;
}

.kg-icon-wrapper {
  flex-shrink: 0;
  inline-size: 44px;
  block-size: 44px;
  border-radius: var(--ds-radius-xl);
  background: var(--ds-color-primary-bg);
  display: flex;
  align-items: center;
  justify-content: center;
}

.kg-info-section {
  flex: 1;
  min-inline-size: 0;
  padding-block-start: 2px;
}

.kg-name-row {
  margin-block-end: 2px;
}

.kg-name-input {
  font-weight: 600 !important;
  letter-spacing: -0.3px;
}
.kg-name-input :deep(input) {
  font-weight: 600 !important;
}

.kg-description-row {
  margin-block-end: 0;
}

.kg-description-input {
  opacity: 0.75;
  transition: opacity 0.2s ease;
}
.kg-description-input:hover,
.kg-description-input:focus-within {
  opacity: 1;
}

/* Remove background colors on focus for all header inputs */
.kg-header-card :deep(.flat-input:focus) {
  background: transparent !important;
}
.kg-header-card :deep(.flat-input:hover:not(:focus)) {
  background: transparent !important;
}

/* Header Actions Section */
.kg-header-actions {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 16px;
  padding-block-start: 4px;
}

.kg-system-name-section {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  min-inline-size: 160px;
}

.kg-system-name-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: var(--ds-font-size-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--ds-color-label);
  padding-inline-end: 4px;
}
.kg-system-name-label .kg-info-icon {
  opacity: 0.6;
  cursor: help;
  transition: opacity 0.15s ease;
}
.kg-system-name-label .kg-info-icon:hover {
  opacity: 1;
}

.kg-system-name-input {
  text-align: end;
  font-family: var(--ds-font-mono);
  font-size: var(--ds-font-size-caption) !important;
  letter-spacing: 0.2px;
  color: var(--ds-color-secondary-text) !important;
}
.kg-system-name-input :deep(input) {
  text-align: end;
  font-family: inherit;
  color: inherit;
}

.kg-system-name-hint {
  position: absolute;
  inset-block-start: 100%;
  inset-inline-end: 0;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: var(--ds-font-size-xs);
  color: var(--ds-color-warning);
  padding-inline-end: 4px;
  margin-block-start: 4px;
  white-space: nowrap;
}

/* Fade transition for hint */
.kg-fade-enter-active,
.kg-fade-leave-active {
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
}
.kg-fade-enter-from,
.kg-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

/* Action Divider */
.kg-action-divider {
  inline-size: 1px;
  block-size: 36px;
  background: linear-gradient(180deg, transparent 0%, rgba(0, 0, 0, 0.08) 20%, rgba(0, 0, 0, 0.08) 80%, transparent 100%);
}

/* Test Retrieval Button */
.test-retrieval-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 18px;
  border: none;
  border-radius: var(--ds-radius-xl);
  background-color: var(--ds-color-primary);
  color: var(--ds-color-static-white);
  font-size: var(--ds-font-size-label);
  font-weight: 600;
  letter-spacing: 0.2px;
  cursor: pointer;
  white-space: nowrap;
  box-shadow: 0 2px 8px color-mix(in srgb, var(--ds-color-primary) 35%, transparent);
  transition:
    box-shadow 0.2s ease,
    transform 0.2s ease,
    filter 0.2s ease;
}
.test-retrieval-btn .btn-arrow {
  opacity: 0.7;
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
}
.test-retrieval-btn:hover {
  filter: brightness(1.1);
  box-shadow: 0 4px 14px color-mix(in srgb, var(--ds-color-primary) 45%, transparent);
  transform: translateY(-1px);
}
.test-retrieval-btn:hover .btn-icon {
  transform: rotate(-8deg) scale(1.05);
}
.test-retrieval-btn:hover .btn-arrow {
  opacity: 1;
  transform: translateX(3px);
}
.test-retrieval-btn:active {
  filter: brightness(0.9);
  box-shadow: 0 1px 4px color-mix(in srgb, var(--ds-color-primary) 30%, transparent);
  transform: translateY(0);
}
.test-retrieval-btn:focus-visible {
  outline: 2px solid var(--ds-color-primary);
  outline-offset: 2px;
}
</style>
