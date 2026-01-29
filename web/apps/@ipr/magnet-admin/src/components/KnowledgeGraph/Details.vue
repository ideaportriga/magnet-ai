<template>
  <div class="row no-wrap overflow-hidden full-height">
    <div class="col row no-wrap full-height justify-center overflow-hidden">
      <div class="col-auto full-width">
        <div class="full-height q-pb-md relative-position q-px-md">
          <!-- Graph Header Card -->
          <div class="kg-header-card q-mt-lg q-mb-sm">
            <div class="kg-header-content">
              <!-- Graph Icon & Info Section -->
              <div class="kg-header-main">
                <div class="kg-icon-wrapper">
                  <q-icon name="o_hub" size="22px" color="primary" />
                </div>
                <div class="kg-info-section">
                  <div class="kg-name-row">
                    <km-input-flat
                      class="kg-name-input km-heading-4 text-black"
                      placeholder="Knowledge Graph Name"
                      :model-value="name"
                      @change="onNameChange"
                    />
                  </div>
                  <div class="kg-description-row">
                    <km-input-flat
                      class="kg-description-input km-description text-secondary-text"
                      placeholder="Add a description..."
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
                    <q-icon name="o_key" size="12px" class="q-mr-xs" />
                    <span>System ID</span>
                    <q-icon name="o_info" size="12px" class="kg-info-icon">
                      <q-tooltip class="bg-white block-shadow text-secondary-text km-description" self="top middle" :offset="[0, 8]">
                        System name serves as a unique identifier for this knowledge graph
                      </q-tooltip>
                    </q-icon>
                  </div>
                  <km-input-flat
                    class="kg-system-name-input km-description text-black"
                    placeholder="enter-system-name"
                    :model-value="systemName"
                    @change="onSystemNameChange"
                    @focus="showInfo = true"
                    @blur="showInfo = false"
                  />
                  <transition name="kg-fade">
                    <div v-if="showInfo" class="kg-system-name-hint">
                      <q-icon name="o_lightbulb" size="11px" />
                      <span>Set once and avoid changing later</span>
                    </div>
                  </transition>
                </div>

                <div class="kg-action-divider" />

                <button class="test-retrieval-btn" @click="openRetrievalDrawer">
                  <span class="btn-label">Test Retrieval</span>
                  <q-icon name="arrow_forward" size="16px" class="btn-arrow" />
                </button>
              </div>
            </div>
          </div>
          <!-- Missing Embedding Model Warning -->
          <div
            v-if="!hasEmbeddingModel && !loading"
            class="row items-center no-wrap q-mt-md bg-red-1 text-red-9 q-px-sm q-py-md border-radius-8 cursor-pointer q-mb-md"
            style="border: 1px solid #ffcdd2"
            @click="goToSettings"
          >
            <q-icon name="o_warning" size="xs" class="q-mr-sm" />
            <div class="text-caption text-weight-medium">No embedding model configured.</div>
            <q-space />
            <div class="row items-center q-gutter-xs text-red-8">
              <span class="text-caption">Go to Settings</span>
              <q-icon name="chevron_right" size="xs" />
            </div>
          </div>
          <div class="column no-wrap ba-border bg-white border-radius-12 q-pa-16" style="min-width: 300px; height: calc(100vh - 190px)">
            <div class="row items-center bb-border q-pb-sm">
              <q-tabs
                :model-value="activeTab"
                class="col"
                narrow-indicator
                dense
                align="left"
                active-color="primary"
                indicator-color="primary"
                active-bg-color="white"
                no-caps
                content-class="km-tabs"
                @update:model-value="onTabAttemptChange"
              >
                <q-tab name="sources" label="Sources" />
                <q-tab name="explorer" label="Data Explorer" />
                <q-tab name="retrieval" label="Retrieval Agent" :alert="retrievalUnsaved" alert-color="orange-9" />
                <q-tab name="metadata" label="Metadata Studio" :alert="metadataUnsaved" alert-color="orange-9" />
                <q-tab name="contentProfiles" label="Content Profiles" />
                <q-tab name="settings" label="Settings" :alert="!hasEmbeddingModel && !loading" alert-color="orange-9" />
              </q-tabs>
              <div class="col-auto">
                <km-btn
                  icon="refresh"
                  label="Refresh"
                  icon-color="icon"
                  hover-color="primary"
                  label-class="km-title"
                  flat
                  icon-size="16px"
                  hover-bg="primary-bg"
                  size="sm"
                  @click="handleRefreshAll"
                />
              </div>
            </div>

            <div class="column no-wrap q-gap-16 full-height full-width overflow-auto q-mt-lg">
              <div class="row q-gap-16 full-height full-width no-wrap">
                <div class="col full-height full-width">
                  <div class="column items-center full-height full-width q-gap-16 overflow-auto">
                    <div class="col-auto full-width">
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
                      <explorer-tab
                        v-show="activeTab === 'explorer'"
                        v-if="graphDetails"
                        ref="explorerRef"
                        :graph-id="graphId"
                        :graph-details="graphDetails"
                        @select-chunk="openChunkDrawer"
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
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="col-auto">
      <chunk-drawer v-if="drawerOpen && drawerType === 'chunk'" :chunk="selectedChunk" @close="drawerOpen = false" />
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
        <q-icon name="cloud_upload" class="kg-dnd-icon" />
      </div>
      <div class="kg-dnd-title">Drop your files here</div>
      <div class="kg-dnd-subtitle">Release to upload to this knowledge graph</div>
    </div>
  </div>

  <!-- Leave Retrieval Tab Confirmation -->
  <km-popup-confirm
    :visible="showRetrievalLeaveDialog"
    confirm-button-label="Save & Switch"
    confirm-button-label2="Don't save"
    confirm-button-type2="secondary"
    cancel-button-label="Stay on Retrieval"
    notification-icon="fas fa-triangle-exclamation"
    @confirm="handleRetrievalSaveAndSwitch"
    @confirm2="handleRetrievalDiscard"
    @cancel="handleRetrievalStay"
  >
    <div class="row item-center justify-center km-heading-7 q-mb-md">Unsaved Changes</div>
    <div class="row text-center justify-center">You have unsaved changes in Retrieval. What would you like to do before switching tabs?</div>
  </km-popup-confirm>

  <!-- Leave Metadata Tab Confirmation -->
  <km-popup-confirm
    :visible="showMetadataLeaveDialog"
    confirm-button-label="Save & Switch"
    confirm-button-label2="Don't save"
    confirm-button-type2="secondary"
    cancel-button-label="Stay on Metadata"
    notification-icon="fas fa-triangle-exclamation"
    @confirm="handleMetadataSaveAndSwitch"
    @confirm2="handleMetadataDiscard"
    @cancel="handleMetadataStay"
  >
    <div class="row item-center justify-center km-heading-7 q-mb-md">Unsaved Changes</div>
    <div class="row text-center justify-center">You have unsaved changes in Metadata Schema. What would you like to do before switching tabs?</div>
  </km-popup-confirm>
</template>

<script setup lang="ts">
import { fetchData } from '@shared'
import { useQuasar } from 'quasar'
import { computed, onBeforeUnmount, onMounted, provide, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useStore } from 'vuex'
import ChunkDrawer from './DataExplorer/ChunkDrawer.vue'
import ExplorerTab from './DataExplorer/ExplorerTab.vue'
import MetadataTab from './Metadata/MetadataTab.vue'
import RetrievalTab from './Retrieval/RetrievalTab.vue'
import RetrievalTestDrawer from './Retrieval/RetrievalTestDrawer.vue'
import ContentProfilesTab from './Settings/ContentProfilesTab.vue'
import SettingsTab from './Settings/SettingsTab.vue'
import SourcesTab from './Sources/SourcesTab.vue'

const route = useRoute()
const store = useStore()
const $q = useQuasar()

const graphId = computed(() => route.params.id as string)
const graphDetails = ref<any>(null)
const activeTab = ref<'sources' | 'settings' | 'contentProfiles' | 'explorer' | 'retrieval' | 'metadata'>('sources')
const loading = ref(false)

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
const name = ref('')
const description = ref('')
const systemName = ref('')
const showInfo = ref(false)
const retrievalUnsaved = ref(false)
const metadataUnsaved = ref(false)
const intendedTab = ref<'sources' | 'settings' | 'contentProfiles' | 'explorer' | 'retrieval' | 'metadata' | null>(null)
const showRetrievalLeaveDialog = ref(false)
const showMetadataLeaveDialog = ref(false)
const retrievalRef = ref<any>(null)
const metadataRef = ref<any>(null)

const onTabAttemptChange = async (nextTab: 'sources' | 'settings' | 'contentProfiles' | 'explorer' | 'retrieval' | 'metadata') => {
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
const drawerType = ref<'source' | 'chunk' | 'retrieval'>('source')
const selectedChunk = ref<any>(null)

const handleSourcesRefresh = async () => {
  await fetchGraphDetails()
  explorerRef.value?.refresh?.()
  metadataRef.value?.refresh?.()
}

const handleRefreshAll = async () => {
  // Refresh all tabs that might be affected by sync
  sourcesRef.value?.refresh?.()
  await handleSourcesRefresh()
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

const openChunkDrawer = (chunk: any) => {
  selectedChunk.value = chunk
  drawerType.value = 'chunk'
  drawerOpen.value = true
}

const openRetrievalDrawer = () => {
  drawerType.value = 'retrieval'
  drawerOpen.value = true
}

const fetchGraphDetails = async () => {
  if (!graphId.value) return
  loading.value = true
  try {
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
    const response = await fetchData({
      endpoint,
      service: `knowledge_graphs//${graphId.value}`,
      method: 'GET',
      credentials: 'include',
    })

    if (response.ok) {
      graphDetails.value = await response.json()
      name.value = graphDetails.value?.name || ''
      systemName.value = graphDetails.value?.system_name || ''
      description.value = graphDetails.value?.description || ''
    }
  } catch (error) {
    console.error('Error fetching graph details:', error)
  } finally {
    loading.value = false
  }
}

const updateGraph = async (payload: Record<string, any>) => {
  if (!graphId.value) return
  try {
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
    await fetchData({
      endpoint,
      service: `knowledge_graphs//${graphId.value}`,
      method: 'PATCH',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    // Refresh details to reflect latest server state
    await fetchGraphDetails()
  } catch (e) {
    console.error('Failed to update graph:', e)
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
  fetchGraphDetails()
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

watch(graphId, () => {
  if (graphId.value) {
    fetchGraphDetails()
  }
})

watch(
  graphDetails,
  () => {
    if (graphDetails.value) {
      name.value = graphDetails.value?.name || ''
      systemName.value = graphDetails.value?.system_name || ''
    }
  },
  { deep: true }
)

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
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
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
          console.error(`Failed to upload: ${file.name}`)
          const error = JSON.parse(response.error.message).error
          if (error && !errorMessage) {
            errorMessage = error
          } else if (error && errorMessage && errorMessage !== error) {
            errorMessage = 'Failed to upload one or more files. Please try again.'
          }
        }
      } catch (err) {
        errorCount++
        console.error(`Upload error for ${file.name}:`, err)
      }
    }

    // Show success or error notification
    if (errorCount === 0) {
      $q.notify({
        message: `Successfully uploaded ${successCount} file${successCount > 1 ? 's' : ''}`,
        position: 'top',
        color: 'positive',
        textColor: 'black',
        timeout: 3000,
      })
    } else if (successCount > 0) {
      $q.notify({
        type: 'warning',
        message: `Uploaded ${successCount} file${successCount > 1 ? 's' : ''}, ${errorCount} failed`,
        position: 'top',
        timeout: 5000,
      })
    } else {
      $q.notify({
        message: errorMessage || 'Failed to upload files. Please try again.',
        position: 'top',
        color: 'error-text',
        timeout: 5000,
      })
    }

    // Refresh sources, explorer, and details to reflect uploaded docs
    if (successCount > 0) {
      refreshSources()
      explorerRef.value?.refresh?.()
      fetchGraphDetails()
    }
  } catch (error) {
    console.error('Upload error:', error)
    $q.notify({
      message: 'Failed to upload files. Please try again.',
      position: 'top',
      color: 'error-text',
      timeout: 5000,
    })
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
  background: rgba(7, 14, 30, 0.45);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
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
  width: 480px;
  max-width: calc(100vw - 48px);
  padding: 48px 32px;
  border-radius: 20px;
  background: white;
  border: none;
  outline: 3px dashed rgba(25, 118, 210, 0.6);
  outline-offset: -12px;
  box-shadow:
    0 20px 50px rgba(0, 0, 0, 0.2),
    inset 0 0 0 1px rgba(240, 245, 250, 1);
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
  width: 96px;
  height: 96px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(25, 118, 210, 0.08) 0%, rgba(25, 118, 210, 0.15) 100%);
  margin-bottom: 8px;
}

.kg-dnd-icon {
  font-size: 48px !important;
  color: #1976d2;
}

.kg-dnd-title {
  font-size: 26px;
  font-weight: 600;
  color: #0b132b;
  letter-spacing: -0.3px;
  margin: 0;
  line-height: 1.2;
}

.kg-dnd-subtitle {
  font-size: 15px;
  color: #6b7b8a;
  margin: 0;
  font-weight: 400;
  letter-spacing: 0.1px;
}

/* ============================================
   Knowledge Graph Header Card Styles
   ============================================ */

.kg-header-card {
  background: linear-gradient(135deg, #ffffff 0%, #fafbfd 100%);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 14px;
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
  min-width: 0;
}

.kg-icon-wrapper {
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: var(--q-primary-bg);
  display: flex;
  align-items: center;
  justify-content: center;
}

.kg-info-section {
  flex: 1;
  min-width: 0;
  padding-top: 2px;
}

.kg-name-row {
  margin-bottom: 2px;
}

.kg-name-input {
  font-weight: 600 !important;
  letter-spacing: -0.3px;
}
.kg-name-input :deep(input) {
  font-weight: 600 !important;
}

.kg-description-row {
  margin-bottom: 0;
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
  padding-top: 4px;
}

.kg-system-name-section {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  min-width: 160px;
}

.kg-system-name-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #8b95a5;
  padding-right: 4px;
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
  text-align: right;
  font-family: 'SF Mono', 'Consolas', 'Monaco', monospace;
  font-size: 12px !important;
  letter-spacing: 0.2px;
  color: #5a6779 !important;
}
.kg-system-name-input :deep(input) {
  text-align: right;
  font-family: inherit;
  color: inherit;
}

.kg-system-name-hint {
  position: absolute;
  top: 100%;
  right: 0;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  color: #f59e0b;
  padding-right: 4px;
  margin-top: 4px;
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
  width: 1px;
  height: 36px;
  background: linear-gradient(180deg, transparent 0%, rgba(0, 0, 0, 0.08) 20%, rgba(0, 0, 0, 0.08) 80%, transparent 100%);
}

/* Test Retrieval Button */
.test-retrieval-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 18px;
  border: none;
  border-radius: 10px;
  background-color: var(--q-primary);
  color: #ffffff;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.2px;
  cursor: pointer;
  white-space: nowrap;
  box-shadow: 0 2px 8px color-mix(in srgb, var(--q-primary) 35%, transparent);
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
  box-shadow: 0 4px 14px color-mix(in srgb, var(--q-primary) 45%, transparent);
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
  box-shadow: 0 1px 4px color-mix(in srgb, var(--q-primary) 30%, transparent);
  transform: translateY(0);
}
.test-retrieval-btn:focus-visible {
  outline: 2px solid var(--q-primary);
  outline-offset: 2px;
}
</style>
