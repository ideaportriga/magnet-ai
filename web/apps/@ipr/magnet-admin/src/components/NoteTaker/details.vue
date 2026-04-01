<template lang="pug">
km-inner-loading(:showing='loading')
layouts-details-layout(v-if='!loading', :noHeader='false', :contentContainerStyle='{ maxWidth: "1200px", minWidth: "500px" }')
  template(#header)
    km-input-flat.km-heading-4.full-width.text-black(placeholder='Name', :modelValue='recordName', @input='recordName = $event')
    km-input-flat.km-description.full-width.text-black(
      placeholder='Description',
      :modelValue='recordDescription',
      @input='recordDescription = $event'
    )
    .row.items-center.q-pl-6
      q-icon.col-auto(name='o_info', color='text-secondary')
        q-tooltip.bg-white.block-shadow.text-black.km-description(self='top middle', :offset='[-50, -50]') System name serves as unique record id
      km-input-flat.col.km-description.full-width(
        placeholder='Enter system name',
        :modelValue='recordSystemName',
        @input='recordSystemName = $event'
      )
  template(#header-actions)
    km-btn(label='Record info', flat, icon='info', iconSize='16px')
      q-tooltip.bg-white.block-shadow
        .q-pa-sm
          .q-mb-sm
            .text-secondary-text.km-button-xs-text Created:
            .text-secondary-text.km-description {{ created_at }}
          .q-mb-sm
            .text-secondary-text.km-button-xs-text Modified:
            .text-secondary-text.km-description {{ modified_at }}
          .q-mb-sm
            .text-secondary-text.km-button-xs-text Created by:
            .text-secondary-text.km-description {{ created_by }}
          div
            .text-secondary-text.km-button-xs-text Modified by:
            .text-secondary-text.km-description {{ updated_by }}
    km-btn(label='Reload Runtime', flat, icon='fas fa-sync', iconSize='16px', @click='reloadRuntime', :loading='reloading')
    km-btn(label='Save', flat, icon='far fa-save', iconSize='16px', @click='save', :loading='saving')
    q-btn.q-px-xs(flat, :icon='"fas fa-ellipsis-v"', size='13px')
      q-menu(anchor='bottom right', self='top right')
        q-item(clickable, @click='showDeleteDialog = true', dense)
          q-item-section
            .km-heading-3 Delete
    km-popup-confirm(
      :visible='showDeleteDialog',
      confirmButtonLabel='Delete Note Taker',
      cancelButtonLabel='Cancel',
      notificationIcon='fas fa-triangle-exclamation',
      @confirm='confirmDelete',
      @cancel='showDeleteDialog = false'
    )
      .row.item-center.justify-center.km-heading-7 You are about to delete the Note Taker config
      .row.text-center.justify-center This action will permanently delete the Note Taker configuration.
  template(#content)
    km-tabs(v-model='tab')
      q-tab(name='transcription', label='Transcription')
      q-tab(name='post-processing', label='Post-processing')
      q-tab(name='embedding', label='Embedding')
      q-tab(name='integrations', label='Integrations')
      q-tab(name='ms-teams', label='MS Teams Settings')

    .col.overflow-auto.q-mt-lg(style='min-height: 0')
      template(v-if='tab === "transcription"')
        note-taker-tab-transcription
      template(v-if='tab === "post-processing"')
        note-taker-tab-post-processing
      template(v-if='tab === "embedding"')
        note-taker-tab-embedding
      template(v-if='tab === "integrations"')
        note-taker-tab-integrations
      template(v-if='tab === "ms-teams"')
        note-taker-tab-ms-teams
  template(#drawer)
    note-taker-drawer(:settingsId='configId', v-if='configId')
</template>

<script setup lang="ts">
import { computed, watch, ref } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { useNotify } from '@/composables/useNotify'
import { useNoteTakerStore } from '@/stores/noteTakerStore'
import { useWorkspaceStore } from '@/stores/workspaceStore'
import { useRouter, useRoute } from 'vue-router'
import { useEntityQueries } from '@/queries/entities'

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
const saving = ref(false)
const reloading = ref(false)
const showDeleteDialog = ref(false)

const configId = computed(() => route.params.id as string)
const activeRecord = computed(() => ntStore.activeRecord)
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
