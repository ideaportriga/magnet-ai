<template>
  <div>
    <div class="dropzone" :class="{ &quot;dropzone--active&quot;: dragOver, &quot;dropzone--disabled&quot;: disable || uploading || readonly }" @dragover.prevent="onDragOver" @dragleave.prevent="onDragLeave" @drop.prevent="onDrop" @click="openFilePicker">
      <input ref="fileInput" class="hidden-input" type="file" multiple :accept="acceptedExtensions" @change="onFileInputChange">
      <div class="dropzone-content">
        <km-glyph class="mb-sm" :name="dragOver ? &quot;cloud-download&quot; : &quot;cloud-upload&quot;" size="32px" :tone="dragOver ? &quot;brand&quot; : &quot;muted&quot;" />
        <div class="text-body2" :class="dragOver ? &quot;text-primary&quot; : &quot;text-grey-7&quot;">
          <template v-if="dragOver">{{ m.collections_dropFilesHere() }}</template>
          <template v-else>{{ m.collections_dragAndDrop() }} <span class="text-primary cursor-pointer">{{ m.collections_clickToBrowse() }}</span></template>
        </div>
        <div class="text-caption text-grey mt-xs">{{ m.collections_fileFormats() }}</div>
      </div>
    </div>
    <div class="cluster mt-sm" data-gap="sm">
      <km-input class="flex-1 file-url-upload__url-input" :model-value="urlInput" :placeholder="m.collections_addUrlPlaceholder()" icon-before="link" :error-message="urlError" :error="!!urlError" :readonly="readonly" :disable="disable" @input="urlInput = $event" @keydown.enter.prevent="addUrl" />
      <km-btn class="url-add-btn" flat round icon="add" tone="muted" size="sm" :disable="!urlInput || !!urlError || disable || readonly" @click="addUrl" />
    </div>
    <template v-if="allItems.length">
      <div class="mt-md">
        <div v-for="(item, index) in allItems" :key="item.key" class="cluster py-xs px-sm rounded-borders list-item">
          <km-glyph class="mr-sm" :name="item.type === &quot;file&quot; ? (item.uploaded ? &quot;file-check&quot; : &quot;file-text&quot;) : &quot;link&quot;" size="14px" :tone="item.type === &quot;file&quot; ? (item.uploaded ? &quot;success&quot; : &quot;weak&quot;) : &quot;brand&quot;" />
          <div class="flex-1 text-body2 text-ellipsis">{{ item.label }}</div><span v-if="item.size" class="text-caption text-grey ml-sm mr-sm">({{ formatSize(item.size) }})</span>
          <km-badge v-if="item.type === &quot;file&quot; &amp;&amp; !item.uploaded" class="mr-sm" tone="warning" :label="m.common_pending()" />
          <km-btn flat round dense size="sm" icon="close" :tone="item.type === &quot;file&quot; &amp;&amp; item.uploaded ? &quot;danger&quot; : &quot;weak&quot;" :disable="disable || readonly || uploading" @click.stop="removeItem(item, index)" />
        </div>
      </div>
    </template>
    <div v-if="pendingFiles.length &amp;&amp; collectionId" class="cluster mt-sm">
      <km-btn :label="uploading ? m.common_uploading() : m.collections_uploadFiles({ count: pendingFiles.length })" icon="cloud-upload" :disable="uploading" :loading="uploading" @click="uploadPending" />
    </div>
    <div v-else-if="pendingFiles.length &amp;&amp; !collectionId" class="cluster mt-sm">
      <div class="text-caption text-grey">
        <km-glyph class="mr-xs" name="info" size="12px" />{{ m.collections_filesWillBeUploaded() }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, useTemplateRef } from 'vue'
import { m } from '@/paraglide/messages'
import { notify } from '@ds/composables/useNotify'
import { fetchData } from '@shared'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { useCollectionDetailStore } from '@/stores/entityDetailStores'
import { useAppStore } from '@/stores/appStore'

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

const { draft, updateField } = useEntityDetail('collections')
// Fallback to Pinia store for CreateNew context (no route ID, so draft is undefined)
const collectionStore = useCollectionDetailStore()
const appStore = useAppStore()
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
const endpoint = computed(() => appStore.adminEndpoint)
const allowedExtSet = computed(() => new Set(acceptedExtensions.split(',')))

const urlError = computed(() => {
  if (!urlInput.value) return ''
  try {
    const url = new URL(urlInput.value)
    if (url.protocol !== 'http:' && url.protocol !== 'https:') return m.validation_onlyHttpHttpsUrls()
    return ''
  } catch {
    return m.validation_invalidUrl()
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
    if (!collectionStore.entity) {
      // Bootstrap a stub entity so updateNestedProperty can write to it (create-new context)
      collectionStore.setEntity({ source: { uploaded_files: [] } })
    }
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
    notify.warning(m.notify_unsupportedFormatNamed({ name: rejected.join(', ') }))
  }
  const total = [...pendingFiles.value, ...accepted]
  if (total.length > 10) {
    notify.warning(m.collections_maxFiles())
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
        notify.error(m.notify_failedToUploadNamed({ name: file.name }))
      }
    } catch (e) {
      notify.error(`${m.notify_uploadFailed()}: ${e.message || e}`)
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
        notify.error(m.notify_failedToUploadNamed({ name: file.name }))
      }
    }
    pendingFiles.value = []
    notify.success(m.collections_filesUploadedSuccessfully())
  } catch (e) {
    notify.error(`${m.notify_uploadFailed()}: ${e.message || e}`)
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
      notify.error(m.notify_failedToDeleteNamed({ name: file.filename }))
    }
  } catch (e) {
    notify.error(`${m.notify_failedToDelete()}: ${e.message || e}`)
  }
}
</script>

<style>
.dropzone {
  border: 2px dashed var(--ds-color-border-2);
  border-radius: var(--ds-radius-lg);
  padding: 24px 16px;
  text-align: center;
  cursor: pointer;
  transition: var(--ds-transition-colors);
}
.dropzone:hover {
  border-color: var(--ds-color-primary);
  background: var(--ds-color-primary-transparent);
}
.dropzone--active {
  border-color: var(--ds-color-primary);
  background: var(--ds-color-primary-bg);
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
.file-url-upload__url-input .km-input__prefix {
  font-size: 14px;
}
.url-add-btn {
  flex-shrink: 0;
}
.list-item {
  gap: 0;
}
.list-item:hover {
  background: var(--ds-color-background);
}
.text-ellipsis {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-inline-size: 0;
}
</style>
