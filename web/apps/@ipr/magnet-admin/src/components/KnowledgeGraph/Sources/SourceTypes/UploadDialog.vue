<template>
  <q-dialog v-model="dialogOpen">
    <q-card class="q-px-lg q-py-sm" style="width: 600px; display: flex; flex-direction: column">
      <q-card-section>
        <div class="row items-center">
          <div class="col">
            <div class="km-heading-7">Upload Files</div>
          </div>
          <div class="col-auto">
            <q-btn icon="close" flat dense @click="onCancel" />
          </div>
        </div>
      </q-card-section>

      <q-card-section>
        <div class="column q-mt-16">
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

        <q-banner v-if="error" class="q-mt-md bg-negative text-white" rounded dense>
          {{ error }}
        </q-banner>
      </q-card-section>

      <q-card-actions class="q-py-lg q-pr-lg">
        <km-btn label="Cancel" flat color="primary" @click="onCancel" />
        <q-space />
        <km-btn label="Upload" :disable="!files || files.length === 0" @click="uploadDocument" />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { fetchData } from '@shared'
import { computed, inject, onUnmounted, ref, watch, type Ref } from 'vue'
import { useStore } from 'vuex'

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
const error = ref('')

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

watch(files, () => {
  if (error.value) error.value = ''
})

const uploadDocument = async () => {
  if (!files.value || files.value.length === 0) {
    error.value = 'Please select at least one file'
    return
  }

  if (kgUploading) kgUploading.value = true
  error.value = ''
  emit('cancel')

  try {
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
    const results: any[] = []
    for (const f of files.value) {
      const formData = new FormData()
      formData.append('data', f)

      const response = await fetchData({
        endpoint,
        service: `knowledge_graphs//${props.graphId}/upload`,
        method: 'POST',
        credentials: 'include',
        body: formData,
        headers: {},
      })

      if (response.ok) {
        const result = await response.json()
        results.push(result)
        // Refresh sources after first successful upload
        if (results.length === 1 && kgRefreshSources) {
          kgRefreshSources()
        }
      } else {
        const errorData = await response.json()
        throw new Error(errorData.error || `Failed to upload: ${f.name}`)
      }
    }
  } catch (err) {
    console.error('Upload error:', err)
    error.value = 'Failed to upload one or more documents. Please try again.'
  } finally {
    if (kgUploading) kgUploading.value = false
    if (kgDndDisabled) kgDndDisabled.value = false
  }
}

const dialogOpen = computed({
  get: () => props.showDialog,
  set: (v: boolean) => {
    if (!v) {
      emit('cancel')
    }
  },
})
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
}
</style>
