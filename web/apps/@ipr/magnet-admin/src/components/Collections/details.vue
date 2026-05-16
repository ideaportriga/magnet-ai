<template>
  <km-inner-loading :showing="loading" />
  <layouts-details-layout v-if="!loading" :name="name" :description="description" :system-name="system_name" :system-name-rules="[validSystemName()]" :created-at="created_at" :updated-at="modified_at" :created-by="created_by" :updated-by="updated_by" :updated-label="m.common_lastSynced()" show-record-info :readonly="recordReadonly" @update:name="name = $event" @update:description="description = $event" @update:system-name="system_name = $event">
    <template #header-actions>
      <km-btn v-if="isDirty && !recordReadonly" data-test="revert-btn" :label="m.common_revert()" icon="undo" icon-size="16px" flat @click="revert()" />
      <km-btn v-if="!recordReadonly" data-test="save-btn" :label="m.common_save()" flat icon="save" icon-size="16px" :loading="saving" :disable="saving || !isDirty" @click="save" />
      <km-btn v-if="!recordReadonly" data-test="save-and-sync-btn" :label="m.common_saveAndSync()" flat icon-size="16px" icon="fa-solid fa-rotate" @click="refreshCollection" />
      <km-glyph v-if="recordReadonly" name="lock" size="16px" tone="muted" :title="m.access_readOnlyTooltip()" data-test="collection-readonly-icon" />
      <ds-dropdown-menu-root>
        <ds-dropdown-menu-trigger as-child>
          <km-btn class="px-xs" data-test="show-more-btn" flat icon="more-vertical" size="13px" />
        </ds-dropdown-menu-trigger>
        <ds-dropdown-menu-content side="bottom" align="end" :side-offset="4">
          <ds-dropdown-menu-item data-test="clone-btn" :disabled="!canCreate" @select="canCreate && (showNewDialog = true)">{{ m.common_clone() }}</ds-dropdown-menu-item>
          <ds-dropdown-menu-item v-if="canDelete" data-test="delete-btn" variant="destructive" @select="showDeleteDialog = true">{{ m.common_delete() }}</ds-dropdown-menu-item>
        </ds-dropdown-menu-content>
      </ds-dropdown-menu-root>
      <km-popup-confirm :visible="showDeleteDialog" :confirm-button-label="m.deleteConfirm_deleteEntity({ entity: m.entity_knowledgeSource() })" :cancel-button-label="m.common_cancel()" notification-icon="warning" @confirm="deleteKnowledge" @cancel="showDeleteDialog = false">
        <div class="cluster mb-md" data-justify="center">{{ m.deleteConfirm_aboutToDelete({ entity: m.entity_knowledgeSource() }) }}</div>
        <div class="cluster text-center" data-justify="center">{{ m.deleteConfirm_knowledgeSourceBody() }}</div>
      </km-popup-confirm>
      <km-popup-confirm :visible="showSyncConfirm" :confirm-button-label="m.common_openSyncJob()" :cancel-button-label="m.common_cancel()" notification-icon="info" @confirm="openJobDetails" @cancel="showSyncConfirm = false">
        <div class="cluster mb-md" data-justify="center">{{ m.syncConfirm_syncingStarted() }}</div>
        <div class="cluster text-center" data-justify="center">{{ m.syncConfirm_syncJobCreated({ jobId: job_id }) }}</div>
      </km-popup-confirm>
    </template>
    <template #content>
      <km-tabs v-model="tab" :items="tabs" />
      <div :inert="recordReadonly" :class="recordReadonly ? 'collection-readonly-zone' : null" class="stack full-height full-width overflow-auto mb-md mt-lg" data-gap="lg" style="min-block-size: 0">
        <div class="cluster full-height full-width" data-gap="lg">
          <div class="flex-1 full-height full-width">
            <div class="stack full-height full-width overflow-auto" data-gap="lg">
              <collections-generalinfo v-if="tab == &quot;settings&quot;" />
              <collections-metadata-page v-if="tab == &quot;metadata&quot;" />
              <collections-chunks v-if="tab == &quot;chunks&quot;" :selected-row="selectedChunk" @select-row="selectedChunk = $event" />
              <collections-scheduler v-if="tab == &quot;scheduler&quot;" />
            </div>
          </div>
        </div>
      </div>
    </template>
    <template #drawer>
      <collections-metadata-drawer v-if="tab == &quot;metadata&quot; &amp;&amp; activeMetadataConfig" />
      <collection-items-drawer v-else-if="tab == &quot;chunks&quot; &amp;&amp; selectedChunk" :selected-row="selectedChunk" @close="selectedChunk = null" />
      <collections-drawer v-else />
    </template>
  </layouts-details-layout>
  <collections-create-new v-if="showNewDialog" :show-new-dialog="showNewDialog" copy @cancel="showNewDialog = false" />
</template>

<script setup>
import { ref, computed, provide } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { notify } from '@ds/composables/useNotify'
import { useEntityQueries } from '@/queries/entities'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { validSystemName } from '@/utils/validationRules'
import { fetchData, usePermissions } from '@shared'
import { useCollectionMetadataStore } from '@/stores/entityDetailStores'
import { useSearchStore } from '@/stores/searchStore'
import { useAppStore } from '@/stores/appStore'
import { storeToRefs } from 'pinia'
import { m } from '@/paraglide/messages'

const emit = defineEmits(['update:closeDrawer'])

const route = useRoute()
const router = useRouter()
const queries = useEntityQueries()
const { draft, isDirty, isLoading, updateField, save: entitySave, revert, remove, buildPayload, data: serverData } = useEntityDetail('collections')
const collectionMetadataStore = useCollectionMetadataStore()
const searchStore = useSearchStore()
const appStore = useAppStore()
const { semanticSearchAnswers } = storeToRefs(searchStore)

const { data: listData } = queries.collections.useList()
const { mutateAsync: updateCollection } = queries.collections.useUpdate()
const { mutateAsync: createCollection } = queries.collections.useCreate()

const showNewDialog = ref(false)
const showDeleteDialog = ref(false)
const showSyncConfirm = ref(false)
const saving = ref(false)
const job_id = ref(null)
const selectedChunk = ref(null)

const tabs = ref([
  { value: 'chunks', label: m.common_chunks() },
  { value: 'metadata', label: m.common_metadata() },
  { value: 'settings', label: m.common_settings() },
  { value: 'scheduler', label: m.common_scheduleAndRuns() },
])
const tab = ref('chunks')

function clearSemanticSearchAnswers() {
  semanticSearchAnswers.value = []
}

const items = computed(() => listData.value?.items || [])

// PR 10 — record-level permission gating mirrors Agents/details.vue.
// Reads `_permissions` from the loaded collection (shipped by backend
// after PR 10). Falls through to global capability for legacy records
// without `_permissions` so existing UX doesn't regress.
const { can, canOn } = usePermissions()
const canEdit = computed(() => canOn(draft?.value, 'edit', 'collections'))
const canDelete = computed(() => canOn(draft?.value, 'delete', 'collections'))
const canCreate = computed(() => can('write:collections'))
const recordReadonly = computed(() => {
  const c = draft?.value
  if (!c) return false
  return canEdit.value === false
})
provide('collectionReadonly', recordReadonly)

const name = computed({
  get() { return draft.value?.name || '' },
  set(value) { updateField('name', value) },
})
const description = computed({
  get() { return draft.value?.description || '' },
  set(value) { updateField('description', value) },
})
const system_name = computed({
  get() { return draft.value?.system_name || '' },
  set(value) { updateField('system_name', value) },
})

const activeKnowledgeId = computed(() => route.params?.id)
const activeRowDB = computed(() => items.value.find((item) => item.id == activeKnowledgeId.value))
const activeMetadataConfig = computed(() => collectionMetadataStore.activeMetadataConfig)
const loading = computed(() => isLoading.value || !draft.value?.id)
const created_by = computed(() => activeRowDB.value?.created_by ? `${activeRowDB.value.created_by}` : m.common_unknown())
const updated_by = computed(() => activeRowDB.value?.updated_by ? `${activeRowDB.value.updated_by}` : m.common_unknown())
const created_at = computed(() => {
  if (!activeRowDB.value) return ''
  return formatDate(activeRowDB.value?.created)
})
const modified_at = computed(() => {
  if (!activeRowDB.value) return ''
  if (!activeRowDB.value?.last_synced || activeRowDB.value?.last_synced?.invalid) return '-'
  return formatDate(activeRowDB.value?.last_synced)
})

function navigate(path = '') {
  if (route.path !== `/${path}`) {
    router.push(`${path}`)
  }
}

function openJobDetails() {
  showSyncConfirm.value = false
  router.push(`/jobs/?job_id=${job_id.value}`)
}

async function deleteKnowledge() {
  saving.value = true
  try {
    const result = await remove()
    if (!result.success) throw result.error || new Error('Failed to delete')
    emit('update:closeDrawer', null)
    notify.success(m.notify_entityDeleted({ entity: m.entity_knowledgeSource() }))
    navigate('/knowledge-sources')
  } catch (error) {
    notify.error(error?.message || m.notify_failedToDelete())
  } finally {
    saving.value = false
  }
}

async function refreshCollection() {
  await save()
  await createSyncJob()
  showSyncConfirm.value = true
}

async function createSyncJob() {
  let jobData = {
    name: `${m.collections_sync()} ${activeRowDB.value?.name}`,
    job_type: 'one_time_immediate',
    notification_email: '',
    run_configuration: {
      type: 'sync_collection',
      params: {
        system_name: activeRowDB.value?.system_name,
      },
    },
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  }

  const endpoint = appStore.config?.scheduler?.endpoint
  const service = appStore.config?.scheduler?.service
  const credentials = appStore.config?.scheduler?.credentials
  const response = await fetchData({
    endpoint,
    service: `${service}/create-job`,
    method: 'POST',
    body: JSON.stringify(jobData),
    credentials,
    headers: { 'Content-Type': 'application/json' },
  })
  const job = await response.json()
  job_id.value = job.job_id

  notify.success(m.collections_syncJobCreated())
}

function transformSourceFields(source) {
  // Transform Documentation source fields from comma-separated strings to arrays
  if (source?.source_type === 'Documentation') {
    const transformed = { ...source }

    // Convert languages from string to array
    if (transformed.languages && typeof transformed.languages === 'string') {
      transformed.languages = transformed.languages
        .split(',')
        .map((lang) => lang.trim())
        .filter((lang) => lang.length > 0)
    }

    // Convert sections from string to array
    if (transformed.sections && typeof transformed.sections === 'string') {
      transformed.sections = transformed.sections
        .split(',')
        .map((section) => section.trim())
        .filter((section) => section.length > 0)
    }

    // Convert max_depth to integer if provided
    if (transformed.max_depth) {
      transformed.max_depth = parseInt(transformed.max_depth) || 5
    }

    return transformed
  }

  return source
}

async function save() {
  // Validate system_name before saving
  const systemNameValidation = validSystemName()(draft.value?.system_name)
  if (systemNameValidation !== true) {
    notify.error(systemNameValidation)
    return
  }

  saving.value = true
  try {
    if (draft.value?.created_at) {
      const obj = buildPayload()

      // Ensure provider_system_name is preserved
      if (activeRowDB.value?.provider_system_name) {
        obj.provider_system_name = activeRowDB.value.provider_system_name
      }

      // Transform source fields for Documentation type
      if (obj.source) {
        obj.source = transformSourceFields(obj.source)
      }

      await updateCollection({ id: draft.value.id, data: obj })
    } else {
      await createCollection(draft.value)
    }
    notify.success(m.notify_savedSuccessfully())
  } catch (error) {
    notify.error(error.message || 'Failed to save')
  } finally {
    saving.value = false
  }
}

function formatDate(date) {
  const dateObject = new Date(date)
  const localeDateString = dateObject.toLocaleDateString()
  const localeTimeString = dateObject.toLocaleTimeString()
  return `${localeDateString} ${localeTimeString}`
}
</script>

<style>
.wobble {
  animation: ds-attention-wobble var(--ds-duration-attention) infinite;
}
.collection-readonly-zone {
  opacity: 0.72;
  cursor: not-allowed;
}
.collection-readonly-zone :where(input, textarea, select, button, [role='button']) {
  cursor: not-allowed;
}
</style>
