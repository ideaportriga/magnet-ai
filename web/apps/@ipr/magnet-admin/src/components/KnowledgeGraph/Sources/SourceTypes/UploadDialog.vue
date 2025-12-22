<template>
  <kg-dialog-base
    :model-value="dialogOpen"
    title="File Upload"
    confirm-label="Upload"
    :disable-confirm="!canUpload"
    :error="error"
    size="md"
    @update:model-value="onModelUpdate"
    @cancel="onCancel"
    @confirm="uploadDocument"
  >
    <kg-dialog-section
      title="File Source"
      description="Choose whether to upload files from your local computer or import content from a URL."
      icon-color="primary"
    >
      <template #header-actions>
        <q-btn-toggle
          v-model="uploadMode"
          class="section-control-toggle"
          no-caps
          rounded
          unelevated
          toggle-color="primary"
          color="grey-3"
          text-color="grey-8"
          dense
          :options="modeOptions"
        />
      </template>

      <div class="q-mt-md">
        <div v-if="uploadMode === 'local'">
          <q-file
            v-model="files"
            outlined
            dense
            multiple
            use-chips
            clearable
            counter
            bottom-slots
            hint="Select files to upload. Drag & drop files or click to browse."
            @rejected="onRejected"
          >
            <template #prepend>
              <q-icon name="fas fa-file" />
            </template>
          </q-file>
        </div>

        <div v-if="uploadMode === 'url'">
          <km-input v-model="urlInput" label="File URL" placeholder="https://example.com/file.pdf" dense @keyup.enter="uploadDocument" />
          <div class="q-ml-12 q-mt-8 q-mb-1" style="font-size: 11px; color: rgba(0, 0, 0, 0.54); line-height: 11px">
            Enter a direct link to a file from the web.
          </div>
        </div>
      </div>
    </kg-dialog-section>
  </kg-dialog-base>
</template>

<script setup lang="ts">
import { fetchData } from '@shared'
import { computed, inject, onUnmounted, ref, watch, type Ref } from 'vue'
import { useStore } from 'vuex'
import { KgDialogBase, KgDialogSection } from '../../common'

const props = defineProps<{
  showDialog: boolean
  graphId: string | null
  source?: any | null
}>()
const emit = defineEmits<{
  cancel: []
}>()

const store = useStore()
const files = ref<File[] | null>(null)
const urlInput = ref('')
const error = ref('')
const uploadMode = ref<'local' | 'url'>('local')

const modeOptions = [
  { label: 'Local Computer', value: 'local' },
  { label: 'Import from URL', value: 'url' },
]

// Access global uploading flag provided by Details.vue to show spinner in table
const kgUploading = inject<Ref<boolean>>('kgUploading')
// Access global DnD disabled flag to suspend window-level DnD while dialog is open
const kgDndDisabled = inject<Ref<boolean>>('kgDndDisabled')
// Function to trigger source list refresh
const kgRefreshSources = inject<() => void>('kgRefreshSources')

const onRejected = () => {
  error.value = 'Some files were not accepted. Please check file type or size.'
}

// Enable/disable global DnD overlay based on dialog visibility
watch(
  () => props.showDialog,
  (visible) => {
    if (kgDndDisabled) kgDndDisabled.value = !!visible
  },
  { immediate: true }
)

onUnmounted(() => {
  if (kgDndDisabled) kgDndDisabled.value = false
})

watch(
  () => props.showDialog,
  (visible) => {
    if (!visible) return
    // Always open with a clean form; URL is transient and not persisted in source config.
    uploadMode.value = 'local'
    files.value = null
    urlInput.value = ''
    error.value = ''
  },
  { immediate: true }
)

watch([files, urlInput, uploadMode], () => {
  if (error.value) error.value = ''
})

watch(
  () => uploadMode.value,
  (mode) => {
    // Prevent accidentally keeping stale inputs when switching modes
    if (mode === 'local') urlInput.value = ''
    if (mode === 'url') files.value = null
  }
)

const canUpload = computed(() => {
  if (uploadMode.value === 'local') {
    return files.value && files.value.length > 0
  } else {
    return urlInput.value && urlInput.value.trim().length > 0
  }
})

const uploadDocument = async () => {
  if (!canUpload.value) {
    error.value = 'Please select a file or enter a URL'
    return
  }

  if (kgUploading) kgUploading.value = true
  error.value = ''
  emit('cancel')

  try {
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
    const results: any[] = []

    if (uploadMode.value === 'local' && files.value) {
      for (const f of files.value) {
        const formData = new FormData()
        formData.append('data', f)

        const response = await fetchData({
          endpoint,
          service: `knowledge_graphs/${props.graphId}/upload`,
          method: 'POST',
          credentials: 'include',
          body: formData,
          headers: {},
        })

        if (response.ok) {
          const result = await response.json()
          results.push(result)
        } else {
          const errorData = await response.json()
          throw new Error(errorData.error || `Failed to upload: ${f.name}`)
        }
      }
    } else if (uploadMode.value === 'url' && urlInput.value) {
      const response = await fetchData({
        endpoint,
        service: `knowledge_graphs/${props.graphId}/upload_url`,
        method: 'POST',
        credentials: 'include',
        body: JSON.stringify({ url: urlInput.value.trim() }),
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (response.ok) {
        const result = await response.json()
        results.push(result)
      } else {
        const errorData = await response.json()
        throw new Error(errorData.error || `Failed to import from URL: ${urlInput.value}`)
      }
    }

    if (results.length > 0 && kgRefreshSources) {
      kgRefreshSources()
    }
  } catch (err: any) {
    console.error('Upload error:', err)
    error.value = err.message || 'Failed to upload one or more documents. Please try again.'
  } finally {
    if (kgUploading) kgUploading.value = false
    if (kgDndDisabled) kgDndDisabled.value = false

    // Reset fields
    files.value = null
    urlInput.value = ''
  }
}

const dialogOpen = computed(() => props.showDialog)

const onModelUpdate = (v: boolean) => {
  if (!v) {
    emit('cancel')
  }
}

const onCancel = () => {
  emit('cancel')
}
</script>

<style scoped>
:deep(.q-field--auto-height.q-field--dense .q-field__control) {
  min-height: 42px;
}

:deep(.q-file .q-chip) {
  max-width: 120px;
  height: 22px;
  padding: 0 10px;
  font-size: 12px;
}

:deep(.q-file .q-chip__content) {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

:deep(.q-field--outlined .q-field__control:before) {
  border-color: var(--q-control-border) !important;
  transition: all 600ms;
  background-color: white !important;
}

.section-control-toggle :deep(.q-btn) {
  padding: 4px 12px;
  min-height: 28px;
  font-size: 13px;
  font-weight: 500;
}

:deep(.km-control) {
  --field-height: 42px !important;
}
</style>
