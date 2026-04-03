<template lang="pug">
div
  //- Dropzone
  .dropzone(
    :class='{ "dropzone--active": dragOver, "dropzone--disabled": disable || uploading || readonly }',
    @dragover.prevent='onDragOver',
    @dragleave.prevent='onDragLeave',
    @drop.prevent='onDrop',
    @click='openFilePicker'
  )
    input.hidden-input(
      ref='fileInput',
      type='file',
      multiple,
      :accept='acceptedExtensions',
      @change='onFileInputChange'
    )
    .dropzone-content
      q-icon.q-mb-sm(:name='dragOver ? "fas fa-cloud-arrow-down" : "fas fa-cloud-upload-alt"', size='32px', :color='dragOver ? "primary" : "grey-6"')
      .text-body2(:class='dragOver ? "text-primary" : "text-grey-7"')
        template(v-if='dragOver') Drop files here
        template(v-else) Drag & drop files or #[span.text-primary.cursor-pointer click to browse]
      .text-caption.text-grey.q-mt-xs PDF, DOCX, XLSX, PPTX, HTML, images and more

  //- URL input
  .row.q-mt-sm.items-center.q-gap-sm
    km-input.col.url-input(
      :model-value='urlInput',
      @input='urlInput = $event',
      placeholder='Add URL to file (https://...)',
      icon-before='fas fa-link',
      :error-message='urlError',
      :error='!!urlError',
      :readonly='readonly',
      :disable='disable',
      @keydown.enter.prevent='addUrl'
    )
    q-btn.url-add-btn(
      flat,
      round,
      icon='fas fa-plus',
      color='secondary',
      size='sm',
      :disable='!urlInput || !!urlError || disable || readonly',
      @click='addUrl'
    )

  //- Unified list
  template(v-if='allItems.length')
    .q-mt-md
      .row.items-center.q-py-xs.q-px-sm.rounded-borders.list-item(
        v-for='(item, index) in allItems',
        :key='item.key'
      )
        //- Icon
        q-icon.q-mr-sm(
          :name='item.type === "file" ? (item.uploaded ? "fas fa-file-circle-check" : "fas fa-file-lines") : "fas fa-link"',
          size='14px',
          :color='item.type === "file" ? (item.uploaded ? "positive" : "grey-7") : "primary"'
        )
        //- Name
        .col.text-body2.text-ellipsis {{ item.label }}
        //- Size (pending files only)
        span.text-caption.text-grey.q-ml-sm.q-mr-sm(v-if='item.size') ({{ formatSize(item.size) }})
        //- Upload badge for pending
        q-badge.q-mr-sm(v-if='item.type === "file" && !item.uploaded', color='orange-2', text-color='orange-9', label='pending')
        //- Remove button
        q-btn(
          flat, round, dense, size='sm',
          icon='fas fa-xmark',
          :color='item.type === "file" && item.uploaded ? "negative" : "grey-6"',
          :disable='disable || readonly || uploading',
          @click.stop='removeItem(item, index)'
        )

  //- Upload button for pending files
  .row.q-mt-sm(v-if='pendingFiles.length && collectionId')
    km-btn(
      :label='uploading ? "Uploading..." : `Upload ${pendingFiles.length} file${pendingFiles.length > 1 ? "s" : ""}`',
      icon='fas fa-cloud-upload-alt',
      color='primary',
      :disable='uploading',
      :loading='uploading',
      @click='uploadPending'
    )
  .row.q-mt-sm(v-else-if='pendingFiles.length && !collectionId')
    .text-caption.text-grey
      q-icon.q-mr-xs(name='fas fa-circle-info', size='12px')
      | Files will be uploaded after saving the knowledge source
</template>

<script setup>
import { ref, computed, watch, useTemplateRef, inject } from 'vue'
import { m } from '@/paraglide/messages'
import { useQuasar } from 'quasar'
import { fetchData } from '@shared'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { useCollectionDetailStore } from '@/stores/entityDetailStores'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => [],
  },
  readonly: {
    type: Boolean,
    default: false,
  },
  disable: {
    type: Boolean,
    default: false,
  },
})
const emit = defineEmits(['update:modelValue'])

const q = useQuasar()
const { draft, updateField } = useEntityDetail('collections')
// Fallback to Pinia store for CreateNew context (no route ID, so draft is undefined)
const collectionStore = useCollectionDetailStore()
const appConfig = inject('appConfig', {})
const fileInputRef = useTemplateRef('fileInput')

const urlInput = ref('')
const pendingFiles = ref([])
const uploading = ref(false)
const dragOver = ref(false)
const acceptedExtensions =
  '.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.odt,.ods,.odp,.rtf,.epub,.csv,.html,.htm,.xml,.txt,.md,.json,.png,.jpg,.jpeg,.gif,.webp,.bmp,.tiff,.eml,.msg'

const urlModel = computed({
  get() { return props.modelValue || [] },
  set(val) { emit('update:modelValue', val) },
})

// Use editBuffer draft when available (detail page), fall back to Pinia store (CreateNew)
const collectionId = computed(() => draft.value?.id || collectionStore.entity?.id || '')
const uploadedFiles = computed(() => draft.value?.source?.uploaded_files || collectionStore.entity?.source?.uploaded_files || [])
const endpoint = computed(() => appConfig?.api?.aiBridge?.urlAdmin)
const allowedExtSet = computed(() => new Set(acceptedExtensions.split(',')))

const urlError = computed(() => {
  if (!urlInput.value) return ''
  try {
    const url = new URL(urlInput.value)
    if (url.protocol !== 'http:' && url.protocol !== 'https:') return 'Only http/https URLs are allowed'
    return ''
  } catch {
    return 'Invalid URL'
  }
})

const allItems = computed(() => {
  const urls = urlModel.value.map((url, i) => ({
    key: `url-${i}`,
    type: 'url',
    label: url,
    uploaded: false,
  }))
  const pending = pendingFiles.value.map((file, i) => ({
    key: `pending-${i}`,
    type: 'file',
    label: file.name,
    size: file.size,
    uploaded: false,
    _file: file,
    _pendingIndex: i,
  }))
  const uploaded = uploadedFiles.value.map((file, i) => ({
    key: `uploaded-${i}`,
    type: 'file',
    label: file.filename,
    uploaded: true,
    _uploadedIndex: i,
    _data: file,
  }))
  return [...urls, ...pending, ...uploaded]
})

// Helper: update uploaded files in the correct store (editBuffer or Pinia)
function setUploadedFiles(newFiles) {
  if (draft.value) {
    updateField('source.uploaded_files', newFiles)
  } else {
    collectionStore.updateNestedProperty({ path: 'source.uploaded_files', value: newFiles })
  }
}

watch(collectionId, (newVal) => {
  if (newVal && pendingFiles.value.length) {
    uploadPending()
  }
})

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function addUrl() {
  const url = urlInput.value.trim()
  if (!url) return
  urlModel.value = [...urlModel.value, url]
  urlInput.value = ''
}

function openFilePicker() {
  if (props.disable || uploading.value || props.readonly) return
  fileInputRef.value?.click()
}

function onFileInputChange(e) {
  const files = Array.from(e.target.files || [])
  addFiles(files)
  e.target.value = ''
}

function onDragOver() {
  if (props.disable || uploading.value || props.readonly) return
  dragOver.value = true
}

function onDragLeave() {
  dragOver.value = false
}

function onDrop(e) {
  dragOver.value = false
  if (props.disable || uploading.value || props.readonly) return
  const files = Array.from(e.dataTransfer?.files || [])
  addFiles(files)
}

function addFiles(files) {
  const accepted = []
  const rejected = []
  for (const file of files) {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase()
    if (allowedExtSet.value.has(ext)) {
      accepted.push(file)
    } else {
      rejected.push(file.name)
    }
  }
  if (rejected.length) {
    q.notify({ color: 'orange-9', textColor: 'white', icon: 'warning', group: 'warning', message: `Unsupported format: ${rejected.join(', ')}` })
  }
  const total = [...pendingFiles.value, ...accepted]
  if (total.length > 10) {
    q.notify({ color: 'orange-9', textColor: 'white', icon: 'warning', group: 'warning', message: 'Maximum 10 files at a time' })
    pendingFiles.value = total.slice(0, 10)
  } else {
    pendingFiles.value = total
  }
  // If no collection yet — upload to temp storage immediately
  if (!collectionId.value) {
    uploadToTemp(accepted)
  }
}

async function uploadToTemp(files) {
  for (const file of files) {
    const formData = new FormData()
    formData.append('data', file, file.name)
    try {
      const response = await fetchData({
        method: 'POST',
        endpoint: endpoint.value,
        credentials: 'include',
        service: 'files/temp',
        body: formData,
      })
      if (response.ok) {
        const result = await response.json()
        const newFiles = [...uploadedFiles.value, { file_id: result.file_id, filename: result.filename }]
        setUploadedFiles(newFiles)
        pendingFiles.value = pendingFiles.value.filter((f) => f.name !== file.name)
      } else {
        q.notify({ color: 'red-9', textColor: 'white', icon: 'error', group: 'error', message: `Failed to upload ${file.name}` })
      }
    } catch (e) {
      q.notify({ color: 'red-9', textColor: 'white', icon: 'error', group: 'error', message: `Upload failed: ${e.message || e}` })
    }
  }
}

function removeItem(item) {
  if (item.type === 'url') {
    urlModel.value = urlModel.value.filter((_, i) => `url-${i}` !== item.key)
  } else if (!item.uploaded) {
    pendingFiles.value = pendingFiles.value.filter((_, i) => `pending-${i}` !== item.key)
  } else {
    removeUploadedFile(item._data, item._uploadedIndex)
  }
}

async function uploadPending() {
  if (!pendingFiles.value.length || !collectionId.value) return

  uploading.value = true
  try {
    for (const file of pendingFiles.value) {
      const formData = new FormData()
      formData.append('data', file, file.name)

      const response = await fetchData({
        method: 'POST',
        endpoint: endpoint.value,
        credentials: 'include',
        service: `knowledge_sources/${collectionId.value}/files`,
        body: formData,
      })

      if (response.ok) {
        const result = await response.json()
        const newFiles = [...uploadedFiles.value, {
          filename: result.filename,
          storage_path: result.storage_path,
        }]
        setUploadedFiles(newFiles)
      } else {
        q.notify({ color: 'red-9', textColor: 'white', icon: 'error', group: 'error', message: `Failed to upload ${file.name}` })
      }
    }
    pendingFiles.value = []
    q.notify({ color: 'green-9', textColor: 'white', icon: 'check_circle', group: 'success', message: 'Files uploaded successfully' })
  } catch (e) {
    q.notify({ color: 'red-9', textColor: 'white', icon: 'error', group: 'error', message: `Upload failed: ${e.message || e}` })
  } finally {
    uploading.value = false
  }
}

async function removeUploadedFile(file, index) {
  if (!collectionId.value) return
  try {
    const response = await fetchData({
      method: 'DELETE',
      endpoint: endpoint.value,
      credentials: 'include',
      service: `knowledge_sources/${collectionId.value}/files/${encodeURIComponent(file.filename)}`,
    })
    if (response.ok || response.status === 204) {
      const newFiles = uploadedFiles.value.filter((_, i) => i !== index)
      updateField('source.uploaded_files', newFiles)
    } else {
      q.notify({ color: 'red-9', textColor: 'white', icon: 'error', group: 'error', message: m.notify_failedToDeleteNamed({ name: file.filename }) })
    }
  } catch (e) {
    q.notify({ color: 'red-9', textColor: 'white', message: `${m.notify_failedToDelete()}: ${e.message || e}` })
  }
}
</script>

<style scoped>
.dropzone {
  border: 2px dashed var(--q-border-2);
  border-radius: var(--radius-lg);
  padding: 24px 16px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
}
.dropzone:hover {
  border-color: var(--q-primary);
  background: var(--q-primary-transparent);
}
.dropzone--active {
  border-color: var(--q-primary);
  background: var(--q-primary-bg);
}
.dropzone--disabled {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}
.dropzone-content {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.hidden-input {
  display: none;
}
.url-input :deep(.q-field__prepend .q-icon) {
  font-size: 14px;
}
.url-add-btn {
  flex-shrink: 0;
}
.list-item {
  gap: 0;
}
.list-item:hover {
  background: var(--q-background);
}
.text-ellipsis {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}
</style>
