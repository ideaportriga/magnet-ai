<template>
  <source-dialog-base
    :show-dialog="dialogOpen"
    :title="isEditMode ? 'Edit SharePoint Source' : 'Connect SharePoint'"
    :confirm-label="isEditMode ? 'Save' : 'Add'"
    :loading="loading"
    :disable-confirm="loading || !isFormValid"
    :error="error"
    @update:show-dialog="onModelUpdate"
    @cancel="$emit('cancel')"
    @confirm="isEditMode ? updateSource() : addSource()"
  >
    <div class="column q-gutter-y-lg">
      <div>
        <div class="km-heading-8 q-pb-xs bb-border text-weight-medium">Name</div>
        <div class="km-description text-secondary-text q-mt-xs q-mb-md">Give this connection a friendly name.</div>
        <km-input v-model="sourceName" height="36px" placeholder="E.g., SharePoint HR Library" border-radius="8px" />
      </div>

      <div>
        <div class="km-heading-8 q-pb-xs bb-border text-weight-medium">Connection</div>
        <div class="km-description text-secondary-text q-mt-xs q-mb-md">Enter the SharePoint site URL to connect. Use the full site URL.</div>
        <km-input
          ref="siteUrlRef"
          v-model="siteUrl"
          height="36px"
          placeholder="https://your-domain.sharepoint.com/sites/your-site"
          border-radius="8px"
          :rules="siteUrlRules"
          required
        />
      </div>

      <div>
        <div class="km-heading-8 q-pb-xs bb-border text-weight-medium">Scope</div>
        <div class="km-description text-secondary-text q-mt-xs q-mb-md">Optionally narrow which content to sync from SharePoint.</div>
        <div class="row q-col-gutter-lg">
          <div class="col-6">
            <div class="km-input-label q-pb-xs">Library</div>
            <km-input v-model="library" height="36px" placeholder="Documents" border-radius="8px" />
          </div>
          <div class="col-6">
            <div class="km-input-label q-pb-xs">Folder Path</div>
            <km-input v-model="folderPath" height="36px" placeholder="Shared Documents/MyFolder" border-radius="8px" />
          </div>
        </div>
        <div class="q-mt-md">
          <div class="km-input-label q-pb-xs">Include Subfolders</div>
          <div class="row items-center q-gutter-sm q-mt-xs">
            <q-toggle v-model="includeSubfolders" dense />
            <div class="km-description text-secondary-text">When enabled, syncs all nested folders under the selected path.</div>
          </div>
        </div>
      </div>
    </div>
  </source-dialog-base>
</template>

<script setup lang="ts">
import { fetchData } from '@shared'
import { computed, ref, watch } from 'vue'
import { useStore } from 'vuex'
import SourceDialogBase from './BaseDialog.vue'

type SharePointSourceConfig = {
  site_url?: string
  library?: string | null
  folder_path?: string | null
  recursive?: boolean
}

type SharePointSourceRecord = {
  id: string
  name: string
  type: 'sharepoint'
  config?: SharePointSourceConfig | null
  status?: string | null
}

const props = defineProps<{
  showDialog: boolean
  graphId: string
  source?: SharePointSourceRecord | null
}>()

const emit = defineEmits<{
  (e: 'cancel'): void
  (e: 'created', result: any): void
  (e: 'update:showDialog', value: boolean): void
}>()

const store = useStore()
const siteUrl = ref('')
const folderPath = ref('')
const library = ref('')
const sourceName = ref('')
const includeSubfolders = ref<boolean>(false)
const loading = ref(false)
const error = ref('')
const showValidation = ref(false)

// Refs for field-level validation
const siteUrlRef = ref<any>(null)

const siteUrlRules = [
  (val: string) => !!(val && val.trim()) || 'Site URL is required',
  (val: string) => /^https?:\/\//.test(val || '') || 'Must start with http(s)://',
]

const isFormValid = computed(() => !!siteUrl.value.trim())

const isEditMode = computed(() => !!props.source)

const dialogOpen = computed(() => props.showDialog)
const onModelUpdate = (v: boolean) => {
  if (!v) {
    emit('cancel')
  } else {
    emit('update:showDialog', v)
  }
}

// Prefill or reset when dialog opens
watch(
  () => [props.showDialog, props.source] as const,
  () => {
    if (props.showDialog) {
      if (props.source) {
        try {
          sourceName.value = props.source?.name || ''
          const cfg = (props.source?.config || {}) as SharePointSourceConfig
          siteUrl.value = cfg.site_url || ''
          library.value = cfg.library || ''
          folderPath.value = cfg.folder_path || ''
          includeSubfolders.value = !!cfg.recursive
        } catch {
          // ignore prefill errors
        }
      } else {
        // opening in create mode - ensure clean form
        sourceName.value = ''
        siteUrl.value = ''
        library.value = ''
        folderPath.value = ''
        includeSubfolders.value = false
      }
    }
  },
  { immediate: true }
)

const addSource = async () => {
  showValidation.value = true
  const siteOk = await (siteUrlRef.value?.validate?.() ?? true)
  if (!siteOk) return

  loading.value = true
  error.value = ''

  try {
    const endpoint = store.getters.config.api.aiBridge.urlAdmin

    const payload = {
      type: 'sharepoint',
      name: sourceName.value.trim() || null,
      config: {
        site_url: siteUrl.value.trim(),
        library: library.value.trim() || null,
        folder_path: folderPath.value.trim() || null,
        recursive: !!includeSubfolders.value,
      },
    }

    const response = await fetchData({
      endpoint,
      service: `knowledge_graphs//${props.graphId}/sources`,
      method: 'POST',
      credentials: 'include',
      body: JSON.stringify(payload),
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (response.ok) {
      const result = await response.json()
      console.log('SharePoint source created:', result)
      emit('created', result)
    } else {
      const errorData = await response.json()
      error.value = errorData.detail || errorData.error || 'Failed to connect to SharePoint'
    }
  } catch (err) {
    console.error('SharePoint connection error:', err)
    error.value = 'Failed to connect to SharePoint. Please try again.'
  } finally {
    loading.value = false
  }
}

const updateSource = async () => {
  if (!props.source) return
  const siteOk = await (siteUrlRef.value?.validate?.() ?? true)
  if (!siteOk) return
  loading.value = true
  error.value = ''
  try {
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
    const payload = {
      name: sourceName.value.trim() || null,
      config: {
        site_url: siteUrl.value.trim(),
        library: library.value.trim() || null,
        folder_path: folderPath.value.trim() || null,
        recursive: !!includeSubfolders.value,
      },
    }
    const response = await fetchData({
      endpoint,
      service: `knowledge_graphs//${props.graphId}/sources/${props.source.id}`,
      method: 'PATCH',
      credentials: 'include',
      body: JSON.stringify(payload),
      headers: { 'Content-Type': 'application/json' },
    })
    if (response.ok) {
      const result = await response.json()
      emit('created', result)
    } else {
      const errorData = await response.json()
      error.value = errorData.detail || errorData.error || 'Failed to save SharePoint source'
    }
  } catch (err) {
    console.error('SharePoint update error:', err)
    error.value = 'Failed to save SharePoint source. Please try again.'
  } finally {
    loading.value = false
  }
}

// Clear error message when user edits inputs
watch([siteUrl, library, folderPath, sourceName, includeSubfolders], () => {
  if (error.value) error.value = ''
})
</script>

<style scoped>
:deep(.q-field--auto-height.q-field--dense .q-field__control) {
  min-height: 42px;
}

:deep(.q-field--outlined .q-field__control:before) {
  border-color: var(--q-control-border) !important;
  transition: all 600ms;
}
</style>
