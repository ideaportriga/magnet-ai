<template lang="pug">
km-inner-loading(:showing='loading')
layouts-details-layout(v-if='!loading', :noHeader='false', :contentContainerStyle='{ maxWidth: "1200px", minWidth: "500px" }')
  template(#header)
    km-input-flat.km-heading-4.full-width.text-black(:placeholder='m.common_name()', :modelValue='recordName', @input='recordName = $event')
    km-input-flat.km-description.full-width.text-black(
      :placeholder='m.common_description()',
      :modelValue='recordDescription',
      @input='recordDescription = $event'
    )
    .row.items-center.q-pl-6
      q-icon.col-auto(name='o_info', color='text-secondary')
        q-tooltip.bg-white.block-shadow.text-black.km-description(self='top middle', :offset='[-50, -50]') {{ m.tooltip_systemNameUniqueId() }}
      km-input-flat.col.km-description.full-width(
        :placeholder='m.placeholder_enterSystemNameReadable()',
        :modelValue='recordSystemName',
        @input='recordSystemName = $event'
      )
  template(#header-actions)
    km-btn(:label='m.common_recordInfo()', flat, icon='info', iconSize='16px')
      q-tooltip.bg-white.block-shadow
        .q-pa-sm
          .q-mb-sm
            .text-secondary-text.km-button-xs-text {{ m.common_createdLabel() }}
            .text-secondary-text.km-description {{ created_at }}
          .q-mb-sm
            .text-secondary-text.km-button-xs-text {{ m.common_modified() }}
            .text-secondary-text.km-description {{ modified_at }}
          .q-mb-sm
            .text-secondary-text.km-button-xs-text {{ m.common_createdBy() }}
            .text-secondary-text.km-description {{ created_by }}
          div
            .text-secondary-text.km-button-xs-text {{ m.common_modifiedBy() }}
            .text-secondary-text.km-description {{ updated_by }}
    km-btn(:label='m.common_reloadRuntime()', flat, icon='fas fa-sync', iconSize='16px', @click='reloadRuntime', :loading='reloading')
    km-btn(:label='m.common_save()', flat, icon='far fa-save', iconSize='16px', @click='save', :loading='saving')
    q-btn.q-px-xs(flat, :icon='"fas fa-ellipsis-v"', size='13px')
      q-menu(anchor='bottom right', self='top right')
        q-item(clickable, @click='showDeleteDialog = true', dense)
          q-item-section
            .km-heading-3 {{ m.common_delete() }}
    km-popup-confirm(
      :visible='showDeleteDialog',
      :confirmButtonLabel='m.deleteConfirm_deleteEntity({ entity: m.entity_noteTaker() })',
      :cancelButtonLabel='m.common_cancel()',
      notificationIcon='fas fa-triangle-exclamation',
      @confirm='confirmDelete',
      @cancel='showDeleteDialog = false'
    )
      .row.item-center.justify-center.km-heading-7 {{ m.deleteConfirm_aboutToDelete({ entity: m.entity_noteTaker() }) }}
      .row.text-center.justify-center {{ m.deleteConfirm_noteTakerBody() }}
  template(#content)
    km-tabs(v-model='tab')
      q-tab(name='transcription', :label='m.common_transcription()')
      q-tab(name='post-processing', :label='m.common_postProcessing()')
      q-tab(name='embedding', :label='m.common_embedding()')
      q-tab(name='integrations', :label='m.common_integrations()')
      q-tab(name='ms-teams', :label='m.common_msTeamsSettings()')

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
