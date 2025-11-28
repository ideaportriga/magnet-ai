<template>
  <div class="row no-wrap overflow-hidden full-height">
    <div class="row no-wrap full-height justify-center fit">
      <div class="col-auto full-width">
        <div class="full-height q-pb-md relative-position q-px-md">
          <div class="row items-center q-gap-12 no-wrap full-width q-mt-lg q-mb-sm bg-white border-radius-8 q-py-12 q-px-16">
            <div class="col">
              <div class="row items-center">
                <km-input-flat class="km-heading-4 full-width text-black" placeholder="Name" :model-value="name" @change="onNameChange" />
              </div>
              <div class="row items-center">
                <km-input-flat
                  class="km-description full-width text-black"
                  placeholder="Description"
                  :model-value="description"
                  @change="onDescriptionChange"
                />
              </div>
              <div class="row items-center q-pl-6">
                <q-icon class="col-auto" name="o_info" color="text-secondary">
                  <q-tooltip class="bg-white block-shadow text-secondary-text km-description" self="top middle" :offset="[-50, -50]">
                    System name serves as unique record id
                  </q-tooltip>
                </q-icon>
                <km-input-flat
                  class="col km-description text-black full-width"
                  placeholder="Enter system name"
                  :model-value="systemName"
                  @change="onSystemNameChange"
                  @focus="showInfo = true"
                  @blur="showInfo = false"
                />
              </div>
              <div v-if="showInfo" class="km-description text-secondary q-pl-6">
                It is highly recommended to fill in system name only once and not change it later.
              </div>
            </div>
          </div>
          <div class="column no-wrap ba-border bg-white border-radius-12 q-pa-16" style="min-width: 300px; height: calc(100vh - 190px)">
            <q-tabs
              v-model="activeTab"
              class="bb-border full-width"
              narrow-indicator
              dense
              align="left"
              active-color="primary"
              indicator-color="primary"
              active-bg-color="white"
              no-caps
              content-class="km-tabs"
            >
              <q-tab name="sources" label="Sources" />
              <q-tab name="settings" label="Settings" />
              <q-tab name="explorer" label="Data Explorer" />
            </q-tabs>

            <div class="column no-wrap q-gap-16 full-height full-width overflow-auto q-mt-lg">
              <div class="row q-gap-16 full-height full-width no-wrap">
                <div class="col full-height full-width">
                  <div class="column items-center full-height full-width q-gap-16 overflow-auto">
                    <div class="col-auto full-width">
                      <template v-if="activeTab === 'sources'">
                        <sources-tab
                          v-if="graphDetails"
                          ref="sourcesRef"
                          :graph-id="graphId"
                          :graph-details="graphDetails"
                          @refresh="fetchGraphDetails"
                        />
                      </template>
                      <template v-if="activeTab === 'settings'">
                        <settings-tab v-if="graphDetails" :graph-id="graphId" :graph-details="graphDetails" @refresh="fetchGraphDetails" />
                      </template>
                      <template v-if="activeTab === 'explorer'">
                        <explorer-tab
                          v-if="graphDetails"
                          ref="explorerRef"
                          :graph-id="graphId"
                          :graph-details="graphDetails"
                          @select-chunk="openChunkDrawer"
                        />
                      </template>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-if="drawerOpen" class="col-auto">
      <chunk-drawer v-if="drawerType === 'chunk'" :chunk="selectedChunk" @close="drawerOpen = false" />
    </div>
  </div>
  <q-inner-loading :showing="loading" />

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
</template>

<script setup lang="ts">
import { fetchData } from '@shared'
import { useQuasar } from 'quasar'
import { computed, onBeforeUnmount, onMounted, provide, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useStore } from 'vuex'
import ChunkDrawer from './DataExplorer/ChunkDrawer.vue'
import ExplorerTab from './DataExplorer/ExplorerTab.vue'
import SettingsTab from './Settings/SettingsTab.vue'
import SourcesTab from './Sources/SourcesTab.vue'

const route = useRoute()
const store = useStore()
const $q = useQuasar()

const graphId = computed(() => route.params.id as string)
const graphDetails = ref<any>(null)
const activeTab = ref<'sources' | 'settings' | 'explorer'>('sources')
const loading = ref(false)
const name = ref('')
const description = ref('')
const systemName = ref('')
const showInfo = ref(false)

const sourcesRef = ref<any>(null)
const explorerRef = ref<any>(null)
const drawerOpen = ref(false)
const drawerType = ref<'source' | 'chunk'>('source')
const selectedChunk = ref<any>(null)

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
    fetchGraphDetails()
  }
})

const openChunkDrawer = (chunk: any) => {
  selectedChunk.value = chunk
  drawerType.value = 'chunk'
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

    for (const file of files) {
      try {
        const formData = new FormData()
        formData.append('data', file)

        const response = await fetchData({
          endpoint,
          service: `knowledge_graphs//${graphId.value}/upload`,
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
        message: 'Failed to upload files. Please try again.',
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

<style lang="stylus" scoped>
.kg-dnd-overlay
  position: fixed
  inset: 0
  z-index: 5000
  display: flex
  align-items: center
  justify-content: center
  background: rgba(7, 14, 30, 0.45)
  backdrop-filter: blur(6px)
  -webkit-backdrop-filter: blur(6px)
  pointer-events: none
  animation: kg-overlay-fade-in 0.15s ease-out
  will-change: opacity

@keyframes kg-overlay-fade-in
  from
    opacity: 0
  to
    opacity: 1

.kg-dnd-content
  display: flex
  flex-direction: column
  align-items: center
  justify-content: center
  gap: 16px
  width: 480px
  max-width: calc(100vw - 48px)
  padding: 48px 32px
  border-radius: 20px
  background: white
  border: none
  outline: 3px dashed rgba(25, 118, 210, 0.6)
  outline-offset: -12px
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2), inset 0 0 0 1px rgba(240, 245, 250, 1)
  animation: kg-content-scale-in 0.2s cubic-bezier(0.34, 1.56, 0.64, 1)
  transform-origin: center
  will-change: transform, opacity
  transform: translateZ(0)
  backface-visibility: hidden

@keyframes kg-content-scale-in
  from
    transform: scale(0.9)
    opacity: 0
  to
    transform: scale(1)
    opacity: 1

.kg-dnd-icon-wrapper
  display: flex
  align-items: center
  justify-content: center
  width: 96px
  height: 96px
  border-radius: 50%
  background: linear-gradient(135deg, rgba(25, 118, 210, 0.08) 0%, rgba(25, 118, 210, 0.15) 100%)
  margin-bottom: 8px

.kg-dnd-icon
  font-size: 48px !important
  color: #1976d2

.kg-dnd-title
  font-size: 26px
  font-weight: 600
  color: #0b132b
  letter-spacing: -0.3px
  margin: 0
  line-height: 1.2

.kg-dnd-subtitle
  font-size: 15px
  color: #6b7b8a
  margin: 0
  font-weight: 400
  letter-spacing: 0.1px
</style>
