<template>
  <km-inner-loading :showing="loading" />
  <layouts-details-layout v-if="!loading" :name="recordName" :description="recordDescription" :system-name="recordSystemName" :created-at="created_at" :updated-at="modified_at" :created-by="created_by" :updated-by="updated_by" show-record-info :content-container-style="{ maxWidth: &quot;1200px&quot;, minWidth: &quot;500px&quot; }" :readonly="recordReadonly" @update:name="recordName = $event" @update:description="recordDescription = $event" @update:system-name="recordSystemName = $event">
    <template #header-actions>
      <km-btn :label="m.common_reloadRuntime()" flat icon="refresh" icon-size="16px" :loading="reloading" @click="reloadRuntime" />
      <km-btn v-if="!recordReadonly" :label="m.common_save()" flat icon="save" icon-size="16px" :loading="saving" @click="save" />
      <km-glyph v-if="recordReadonly" name="lock" size="16px" tone="muted" :title="m.access_readOnlyTooltip()" data-test="note-taker-readonly-icon" />
      <ds-dropdown-menu-root>
        <ds-dropdown-menu-trigger as-child>
          <km-btn class="px-xs" flat icon="more-vertical" size="13px" />
        </ds-dropdown-menu-trigger>
        <ds-dropdown-menu-content side="bottom" align="end" :side-offset="4">
          <ds-dropdown-menu-item v-if="canDelete" variant="destructive" @select="showDeleteDialog = true">{{ m.common_delete() }}</ds-dropdown-menu-item>
        </ds-dropdown-menu-content>
      </ds-dropdown-menu-root>
      <km-popup-confirm :visible="showDeleteDialog" :confirm-button-label="m.deleteConfirm_deleteEntity({ entity: m.entity_noteTaker() })" :cancel-button-label="m.common_cancel()" notification-icon="warning" @confirm="confirmDelete" @cancel="showDeleteDialog = false">
        <div class="cluster" data-justify="center">{{ m.deleteConfirm_aboutToDelete({ entity: m.entity_noteTaker() }) }}</div>
        <div class="cluster text-center" data-justify="center">{{ m.deleteConfirm_noteTakerBody() }}</div>
      </km-popup-confirm>
    </template>
    <template #content>
      <km-tabs v-model="tab" :items="tabs" />
      <div :inert="recordReadonly" :class="recordReadonly ? 'note-taker-readonly-zone' : null" class="flex-1 overflow-auto mt-lg" style="min-block-size: 0">
        <template v-if="tab === &quot;transcription&quot;">
          <note-taker-tab-transcription />
        </template>
        <template v-if="tab === &quot;post-processing&quot;">
          <note-taker-tab-post-processing />
        </template>
        <template v-if="tab === &quot;embedding&quot;">
          <note-taker-tab-embedding />
        </template>
        <template v-if="tab === &quot;integrations&quot;">
          <note-taker-tab-integrations />
        </template>
        <template v-if="tab === &quot;ms-teams&quot;">
          <note-taker-tab-ms-teams />
        </template>
      </div>
    </template>
    <template #drawer>
      <div :inert="recordReadonly" :class="recordReadonly ? 'note-taker-readonly-zone' : null" class="full-height">
        <note-taker-drawer v-if="configId" :settings-id="configId" />
      </div>
    </template>
  </layouts-details-layout>
</template>

<script setup lang="ts">
import { computed, watch, ref, provide } from 'vue'
import { usePermissions } from '@shared'
import { useAppStore } from '@/stores/appStore'
import { useNotify } from '@/composables/useNotify'
import { useNoteTakerStore } from '@/stores/noteTakerStore'
import { useWorkspaceStore } from '@/stores/workspaceStore'
import { useRouter, useRoute } from 'vue-router'
import { useEntityQueries } from '@/queries/entities'
import { m } from '@/paraglide/messages'

import NoteTakerTabTranscription from './tabs/Transcription.vue'
import NoteTakerTabPostProcessing from './tabs/PostProcessing.vue'
import NoteTakerTabEmbedding from './tabs/Embedding.vue'
import NoteTakerTabIntegrations from './tabs/Integrations.vue'
import NoteTakerTabMsTeams from './tabs/MSTeams.vue'
import NoteTakerDrawer from './Drawer.vue'

const { notifySuccess, notifyError } = useNotify()
const ntStore = useNoteTakerStore()
const workspace = useWorkspaceStore()
const appStore = useAppStore()
const router = useRouter()
const route = useRoute()
const queries = useEntityQueries()

// TanStack Query auto-fetches promptTemplates and api_servers
queries.promptTemplates.useList()
queries.api_servers.useList()

const tab = ref('transcription')
const tabs = ref([
  { value: 'transcription', label: m.common_transcription() },
  { value: 'post-processing', label: m.common_postProcessing() },
  { value: 'embedding', label: m.common_embedding() },
  { value: 'integrations', label: m.common_integrations() },
  { value: 'ms-teams', label: m.common_msTeamsSettings() },
])
const saving = ref(false)
const reloading = ref(false)
const showDeleteDialog = ref(false)

const configId = computed(() => route.params.id as string)
const activeRecord = computed(() => ntStore.activeRecord)

// PR 10 — record-level permission gating.
const { can, canOn } = usePermissions()
const canEdit = computed(() => canOn(activeRecord.value as any, 'edit', 'note_taker'))
const canDelete = computed(() => canOn(activeRecord.value as any, 'delete', 'note_taker'))
const canCreate = computed(() => can('write:note_taker'))
const recordReadonly = computed(() => {
  const r = activeRecord.value
  if (!r) return false
  return canEdit.value === false
})
provide('noteTakerReadonly', recordReadonly)
const loading = computed(() => ntStore.loading || !activeRecord.value)
const apiReady = computed(() => Boolean(appStore.config?.api?.aiBridge?.urlAdmin))

const recordName = computed({
  get: () => activeRecord.value?.name || '',
  set: (value: string) => ntStore.updateRecordMeta({ name: value }),
})
const recordDescription = computed({
  get: () => activeRecord.value?.description || '',
  set: (value: string) => ntStore.updateRecordMeta({ description: value }),
})
const recordSystemName = computed({
  get: () => activeRecord.value?.system_name || '',
  set: (value: string) => ntStore.updateRecordMeta({ system_name: value }),
})

const created_at = computed(() => activeRecord.value?.created_at ? formatDate(activeRecord.value.created_at) : '')
const modified_at = computed(() => activeRecord.value?.updated_at ? formatDate(activeRecord.value.updated_at) : '')
const created_by = computed(() => activeRecord.value?.created_by || 'Unknown')
const updated_by = computed(() => activeRecord.value?.updated_by || 'Unknown')

function formatDate(date: string) {
  const d = new Date(date)
  return `${d.toLocaleDateString()} ${d.toLocaleTimeString()}`
}

async function save() {
  saving.value = true
  try {
    await ntStore.saveSettings()
    notifySuccess('Saved successfully')
  } catch (error: any) {
    notifyError(error.message || 'Failed to save')
  } finally {
    saving.value = false
  }
}

async function reloadRuntime() {
  reloading.value = true
  try {
    await ntStore.reloadRuntime(configId.value)
    notifySuccess('Runtime reloaded')
  } catch (error: any) {
    notifyError(error.message || 'Failed to reload')
  } finally {
    reloading.value = false
  }
}

async function confirmDelete() {
  try {
    await ntStore.deleteSettings(configId.value)
    notifySuccess('Note Taker config deleted')
    router.push('/note-taker')
  } catch (error: any) {
    notifyError(error.message || 'Failed to delete')
  }
}

const loadRecord = async () => {
  if (!configId.value || !apiReady.value) return
  const record = await ntStore.fetchSettingsById(configId.value)
  if (!record) router.push('/note-taker')
}

watch(
  apiReady,
  (ready) => {
    if (!ready) return
    loadRecord()
  },
  { immediate: true }
)

watch(
  () => configId.value,
  () => loadRecord()
)

// Update workspace tab label when record name is loaded
watch(
  () => activeRecord.value?.name,
  (name) => {
    if (!name || !configId.value) return
    const tab = workspace.tabs.find((t) => t.entityType === 'note_taker' && t.entityId === configId.value)
    if (tab && tab.label !== name) {
      workspace.updateTabLabel(tab.id, name)
    }
  },
  { immediate: true }
)
</script>

<style scoped>
.note-taker-readonly-zone {
  opacity: 0.72;
  cursor: not-allowed;
}
.note-taker-readonly-zone :where(input, textarea, select, button, [role='button']) {
  cursor: not-allowed;
}
</style>
