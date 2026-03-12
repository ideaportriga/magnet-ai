<template lang="pug">
div
  q-tabs.q-mb-sm(v-model='activeTab', dense, align='left', narrow-indicator)
    q-tab(name='url', label='URL', icon='fas fa-link')
    q-tab(name='upload', label='Upload', icon='fas fa-upload', :disable='!collectionId')
      q-tooltip(v-if='!collectionId') Save the knowledge source first to enable file upload

  q-tab-panels(v-model='activeTab', animated)
    q-tab-panel(name='url')
      km-input-list-add(
        v-model='urlModel',
        btnLabel='Add URL',
        :readonly='readonly',
        :disable='disable'
      )

    q-tab-panel(name='upload')
      //- Dropzone area
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
          q-icon.q-mb-sm(:name='dragOver ? "fas fa-cloud-arrow-down" : "fas fa-cloud-upload-alt"', size='36px', :color='dragOver ? "primary" : "grey-6"')
          .text-body2(:class='dragOver ? "text-primary" : "text-grey-7"')
            template(v-if='dragOver') Drop files here
            template(v-else) Drag & drop files here or #[span.text-primary.cursor-pointer click to browse]
          .text-caption.text-grey.q-mt-xs PDF, DOCX, XLSX, PPTX, HTML, images, and more (max 10 files)

      //- Selected files ready for upload
      template(v-if='selectedFiles && selectedFiles.length')
        .text-caption.text-grey.q-mt-md.q-mb-xs Selected files:
        .row.items-center.q-mb-xs(v-for='(file, index) in selectedFiles', :key='index')
          q-icon.q-mr-sm(name='fas fa-file-lines', size='14px', color='grey-7')
          span.text-body2 {{ file.name }}
          span.text-caption.text-grey.q-ml-sm ({{ formatSize(file.size) }})
          q-space
          q-btn(flat, round, dense, size='sm', icon='fas fa-xmark', @click='removeSelected(index)')
        .row.q-mt-sm
          km-btn(
            :label='uploading ? "Uploading..." : `Upload ${selectedFiles.length} file${selectedFiles.length > 1 ? "s" : ""}`',
            icon='fas fa-cloud-upload-alt',
            color='primary',
            :disable='uploading',
            :loading='uploading',
            @click='uploadFiles'
          )

      //- List of already uploaded files
      template(v-if='uploadedFiles.length')
        q-separator.q-my-md
        .text-caption.text-grey.q-mb-xs Uploaded files:
        .row.items-center.q-mb-xs(v-for='(file, index) in uploadedFiles', :key='"uploaded-" + index')
          q-icon.q-mr-sm(name='fas fa-file-circle-check', size='14px', color='positive')
          span.text-body2 {{ file.filename }}
          q-space
          q-btn(
            flat,
            round,
            dense,
            size='sm',
            icon='far fa-trash-can',
            color='negative',
            :disable='disable || readonly',
            @click.stop='removeUploadedFile(file, index)'
          )
</template>

<script>
import { fetchData } from '@shared'

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
  data() {
    return {
      activeTab: 'url',
      selectedFiles: [],
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
      return this.$store.getters.knowledge?.id || ''
    },
    uploadedFiles() {
      return this.$store.getters.knowledge?.source?.uploaded_files || []
    },
    endpoint() {
      return this.$store?.getters?.config?.api?.aiBridge?.urlAdmin
    },
    allowedExtSet() {
      return new Set(this.acceptedExtensions.split(','))
    },
  },
  methods: {
    formatSize(bytes) {
      if (bytes < 1024) return bytes + ' B'
      if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
      return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
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
        this.$q.notify({
          type: 'warning',
          message: `Unsupported format: ${rejected.join(', ')}`,
        })
      }
      const total = [...this.selectedFiles, ...accepted]
      if (total.length > 10) {
        this.$q.notify({ type: 'warning', message: 'Maximum 10 files at a time' })
        this.selectedFiles = total.slice(0, 10)
      } else {
        this.selectedFiles = total
      }
    },
    removeSelected(index) {
      this.selectedFiles.splice(index, 1)
    },
    async uploadFiles() {
      if (!this.selectedFiles?.length || !this.collectionId) return

      this.uploading = true
      try {
        for (const file of this.selectedFiles) {
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
            this.$store.dispatch('updateKnowledge', {
              source: { uploaded_files: newFiles },
            })
          } else {
            this.$q.notify({
              type: 'negative',
              message: `Failed to upload ${file.name}`,
            })
          }
        }

        this.selectedFiles = []
        this.$q.notify({
          type: 'positive',
          message: 'Files uploaded successfully',
        })
      } catch (e) {
        this.$q.notify({
          type: 'negative',
          message: `Upload failed: ${e.message || e}`,
        })
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
          this.$store.dispatch('updateKnowledge', {
            source: { uploaded_files: newFiles },
          })
        } else {
          this.$q.notify({
            type: 'negative',
            message: `Failed to delete ${file.filename}`,
          })
        }
      } catch (e) {
        this.$q.notify({
          type: 'negative',
          message: `Delete failed: ${e.message || e}`,
        })
      }
    },
  },
}
</script>

<style scoped>
.dropzone {
  border: 2px dashed #ccc;
  border-radius: 8px;
  padding: 32px 16px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
}
.dropzone:hover {
  border-color: #1976d2;
  background: rgba(25, 118, 210, 0.03);
}
.dropzone--active {
  border-color: #1976d2;
  background: rgba(25, 118, 210, 0.08);
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
</style>
