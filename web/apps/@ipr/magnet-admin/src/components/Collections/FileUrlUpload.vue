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

<script>
import { fetchData } from '@shared'
import { useCollectionDetailStore } from '@/stores/entityDetailStores'

export default {
  name: 'FileUrlUpload',
  props: {
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
  },
  emits: ['update:modelValue'],
  setup() {
    const collectionStore = useCollectionDetailStore()
    return { collectionStore }
  },
  data() {
    return {
      urlInput: '',
      pendingFiles: [],
      uploading: false,
      dragOver: false,
      acceptedExtensions:
        '.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.odt,.ods,.odp,.rtf,.epub,.csv,.html,.htm,.xml,.txt,.md,.json,.png,.jpg,.jpeg,.gif,.webp,.bmp,.tiff,.eml,.msg',
    }
  },
  computed: {
    urlModel: {
      get() {
        return this.modelValue || []
      },
      set(val) {
        this.$emit('update:modelValue', val)
      },
    },
    collectionId() {
      return this.collectionStore.entity?.id || ''
    },
    uploadedFiles() {
      return this.collectionStore.entity?.source?.uploaded_files || []
    },
    endpoint() {
      return this.$appConfig?.api?.aiBridge?.urlAdmin
    },
    allowedExtSet() {
      return new Set(this.acceptedExtensions.split(','))
    },
    urlError() {
      if (!this.urlInput) return ''
      try {
        const url = new URL(this.urlInput)
        if (url.protocol !== 'http:' && url.protocol !== 'https:') return 'Only http/https URLs are allowed'
        return ''
      } catch {
        return 'Invalid URL'
      }
    },
    allItems() {
      const urls = this.urlModel.map((url, i) => ({
        key: `url-${i}`,
        type: 'url',
        label: url,
        uploaded: false,
      }))
      const pending = this.pendingFiles.map((file, i) => ({
        key: `pending-${i}`,
        type: 'file',
        label: file.name,
        size: file.size,
        uploaded: false,
        _file: file,
        _pendingIndex: i,
      }))
      const uploaded = this.uploadedFiles.map((file, i) => ({
        key: `uploaded-${i}`,
        type: 'file',
        label: file.filename,
        uploaded: true,
        _uploadedIndex: i,
        _data: file,
      }))
      return [...urls, ...pending, ...uploaded]
    },
  },
  watch: {
    collectionId(newVal) {
      if (newVal && this.pendingFiles.length) {
        this.uploadPending()
      }
    },
  },
  methods: {
    formatSize(bytes) {
      if (bytes < 1024) return bytes + ' B'
      if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
      return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
    },
    addUrl() {
      const url = this.urlInput.trim()
      if (!url) return
      this.urlModel = [...this.urlModel, url]
      this.urlInput = ''
    },
    openFilePicker() {
      if (this.disable || this.uploading || this.readonly) return
      this.$refs.fileInput?.click()
    },
    onFileInputChange(e) {
      const files = Array.from(e.target.files || [])
      this.addFiles(files)
      e.target.value = ''
    },
    onDragOver() {
      if (this.disable || this.uploading || this.readonly) return
      this.dragOver = true
    },
    onDragLeave() {
      this.dragOver = false
    },
    onDrop(e) {
      this.dragOver = false
      if (this.disable || this.uploading || this.readonly) return
      const files = Array.from(e.dataTransfer?.files || [])
      this.addFiles(files)
    },
    addFiles(files) {
      const accepted = []
      const rejected = []
      for (const file of files) {
        const ext = '.' + file.name.split('.').pop()?.toLowerCase()
        if (this.allowedExtSet.has(ext)) {
          accepted.push(file)
        } else {
          rejected.push(file.name)
        }
      }
      if (rejected.length) {
        this.$q.notify({ color: 'orange-9', textColor: 'white', icon: 'warning', group: 'warning', message: `Unsupported format: ${rejected.join(', ')}` })
      }
      const total = [...this.pendingFiles, ...accepted]
      if (total.length > 10) {
        this.$q.notify({ color: 'orange-9', textColor: 'white', icon: 'warning', group: 'warning', message: 'Maximum 10 files at a time' })
        this.pendingFiles = total.slice(0, 10)
      } else {
        this.pendingFiles = total
      }
      // If no collection yet — upload to temp storage immediately
      if (!this.collectionId) {
        this.uploadToTemp(accepted)
      }
    },
    async uploadToTemp(files) {
      for (const file of files) {
        const formData = new FormData()
        formData.append('data', file, file.name)
        try {
          const response = await fetchData({
            method: 'POST',
            endpoint: this.endpoint,
            credentials: 'include',
            service: 'files/temp',
            body: formData,
          })
          if (response.ok) {
            const result = await response.json()
            const newFiles = [...this.uploadedFiles, { file_id: result.file_id, filename: result.filename }]
            this.collectionStore.updateNestedProperty({ path: 'source.uploaded_files', value: newFiles })
            this.pendingFiles = this.pendingFiles.filter((f) => f.name !== file.name)
          } else {
            this.$q.notify({ color: 'red-9', textColor: 'white', icon: 'error', group: 'error', message: `Failed to upload ${file.name}` })
          }
        } catch (e) {
          this.$q.notify({ color: 'red-9', textColor: 'white', icon: 'error', group: 'error', message: `Upload failed: ${e.message || e}` })
        }
      }
    },
    removeItem(item) {
      if (item.type === 'url') {
        this.urlModel = this.urlModel.filter((_, i) => `url-${i}` !== item.key)
      } else if (!item.uploaded) {
        this.pendingFiles = this.pendingFiles.filter((_, i) => `pending-${i}` !== item.key)
      } else {
        this.removeUploadedFile(item._data, item._uploadedIndex)
      }
    },
    async uploadPending() {
      if (!this.pendingFiles.length || !this.collectionId) return

      this.uploading = true
      try {
        for (const file of this.pendingFiles) {
          const formData = new FormData()
          formData.append('data', file, file.name)

          const response = await fetchData({
            method: 'POST',
            endpoint: this.endpoint,
            credentials: 'include',
            service: `knowledge_sources/${this.collectionId}/files`,
            body: formData,
          })

          if (response.ok) {
            const result = await response.json()
            const newFiles = [...this.uploadedFiles, {
              filename: result.filename,
              storage_path: result.storage_path,
            }]
            this.collectionStore.updateNestedProperty({ path: 'source.uploaded_files', value: newFiles })
          } else {
            this.$q.notify({ color: 'red-9', textColor: 'white', icon: 'error', group: 'error', message: `Failed to upload ${file.name}` })
          }
        }
        this.pendingFiles = []
        this.$q.notify({ color: 'green-9', textColor: 'white', icon: 'check_circle', group: 'success', message: 'Files uploaded successfully' })
      } catch (e) {
        this.$q.notify({ color: 'red-9', textColor: 'white', icon: 'error', group: 'error', message: `Upload failed: ${e.message || e}` })
      } finally {
        this.uploading = false
      }
    },
    async removeUploadedFile(file, index) {
      if (!this.collectionId) return
      try {
        const response = await fetchData({
          method: 'DELETE',
          endpoint: this.endpoint,
          credentials: 'include',
          service: `knowledge_sources/${this.collectionId}/files/${encodeURIComponent(file.filename)}`,
        })
        if (response.ok || response.status === 204) {
          const newFiles = this.uploadedFiles.filter((_, i) => i !== index)
          this.collectionStore.updateNestedProperty({ path: 'source.uploaded_files', value: newFiles })
        } else {
          this.$q.notify({ color: 'red-9', textColor: 'white', icon: 'error', group: 'error', message: `Failed to delete ${file.filename}` })
        }
      } catch (e) {
        this.$q.notify({ color: 'red-9', textColor: 'white', message: `Delete failed: ${e.message || e}` })
      }
    },
  },
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
