<template lang="pug">
km-inner-loading(:showing='loading')
layouts-details-layout(v-if='!loading')
  template(#header)
    km-input-flat.km-heading-4.full-width.text-black(:placeholder='m.common_name()', :modelValue='name', @change='name = $event')
    km-input-flat.km-description.full-width.text-black(:placeholder='m.common_description()', :modelValue='description', @change='description = $event')
    .row.items-center.q-pl-6
      q-icon.col-auto(name='o_info', color='text-secondary')
        q-tooltip.bg-white.block-shadow.text-secondary-text.km-description(self='top middle', :offset='[-50, -50]') {{ m.tooltip_systemNameUniqueId() }}
      km-input-flat.col.km-description.text-black.full-width(
        :placeholder='m.placeholder_enterSystemNameReadable()',
        :modelValue='system_name',
        @change='system_name = $event',
        @focus='showInfo = true',
        @blur='showInfo = false',
        :rules='[validSystemName()]'
      )
    .km-description.text-secondary.q-pl-6(v-if='showInfo') {{ m.hint_systemNameRecommendation() }}
  template(#header-actions)
    km-btn(:label='m.common_recordInfo()', flat, icon='info', iconSize='16px')
      q-tooltip.bg-white.block-shadow
        .q-pa-sm
          .q-mb-sm
            .text-secondary-text.km-button-xs-text {{ m.common_createdLabel() }}
            .text-secondary-text.km-description {{ created_at }}
          .q-mb-sm
            .text-secondary-text.km-button-xs-text {{ m.common_lastSynced() }}
            .text-secondary-text.km-description {{ modified_at }}
          .q-mb-sm
            .text-secondary-text.km-button-xs-text {{ m.common_createdBy() }}
            .text-secondary-text.km-description {{ created_by }}
          div
            .text-secondary-text.km-button-xs-text {{ m.common_modifiedBy() }}
            .text-secondary-text.km-description {{ updated_by }}
    km-btn(:label='m.common_revert()', icon='fas fa-undo', iconSize='16px', flat, @click='revert()', v-if='isDirty')
    km-btn(:label='m.common_save()', flat, icon='far fa-save', iconSize='16px', @click='save', :loading='saving', :disable='saving || !isDirty')
    km-btn(:label='m.common_saveAndSync()', flat, @click='refreshCollection', iconSize='16px', icon='fa-solid fa-rotate')
    q-btn.q-px-xs(flat, :icon='"fas fa-ellipsis-v"', size='13px')
      q-menu(anchor='bottom right', self='top right')
        q-item(clickable, @click='showNewDialog = true', dense)
          q-item-section
            .km-heading-3 {{ m.common_clone() }}
        q-item(clickable, @click='showDeleteDialog = true', dense)
          q-item-section
            .km-heading-3 {{ m.common_delete() }}
    km-popup-confirm(
      :visible='showDeleteDialog',
      :confirmButtonLabel='m.deleteConfirm_deleteEntity({ entity: m.entity_knowledgeSource() })',
      :cancelButtonLabel='m.common_cancel()',
      notificationIcon='fas fa-triangle-exclamation',
      @confirm='deleteKnowledge',
      @cancel='showDeleteDialog = false'
    )
      .row.item-center.justify-center.km-heading-7 {{ m.deleteConfirm_aboutToDelete({ entity: m.entity_knowledgeSource() }) }}
      .row.text-center.justify-center {{ m.deleteConfirm_knowledgeSourceBody() }}
    km-popup-confirm(
      :visible='showSyncConfirm',
      :confirmButtonLabel='m.common_openSyncJob()',
      :cancelButtonLabel='m.common_cancel()',
      notificationIcon='fas fa-info-circle',
      @confirm='openJobDetails',
      @cancel='showSyncConfirm = false'
    )
      .row.item-center.justify-center.km-heading-7.q-mb-md {{ m.syncConfirm_syncingStarted() }}
      .row.text-center.justify-center {{ m.syncConfirm_syncJobCreated({ jobId: job_id }) }}
  template(#content)
    km-tabs(v-model='tab')
      template(v-for='t in tabs')
        q-tab(:name='t.name', :label='t.label')
    .column.no-wrap.q-gap-16.full-height.full-width.overflow-auto.q-mb-md.q-mt-lg(style='min-height: 0')
      .row.q-gap-16.full-height.full-width
        .col.full-height.full-width
          .column.full-height.full-width.q-gap-16.overflow-auto.no-wrap
            collections-generalinfo(v-if='tab == "settings"')
            collections-metadata-page(v-if='tab == "metadata"')
            collections-chunks(v-if='tab == "chunks"', :selectedRow='selectedChunk', @selectRow='selectedChunk = $event')
            collections-scheduler(v-if='tab == "scheduler"')
  template(#drawer)
    collections-metadata-drawer(v-if='tab == "metadata" && activeMetadataConfig')
    collection-items-drawer(v-else-if='tab == "chunks" && selectedChunk', :selectedRow='selectedChunk', @close='selectedChunk = null')
    collections-drawer(v-else)
collections-create-new(v-if='showNewDialog', :showNewDialog='showNewDialog', @cancel='showNewDialog = false', copy)
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { useEntityQueries } from '@/queries/entities'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { validSystemName } from '@shared/utils/validationRules'
import { fetchData } from '@shared'
import { useCollectionMetadataStore } from '@/stores/entityDetailStores'
import { useSearchStore } from '@/stores/searchStore'
import { useAppStore } from '@/stores/appStore'
import { storeToRefs } from 'pinia'
import { m } from '@/paraglide/messages'

const emit = defineEmits(['update:closeDrawer'])

const route = useRoute()
const router = useRouter()
const q = useQuasar()
const queries = useEntityQueries()
const { draft, isDirty, updateField, save: entitySave, revert, remove, buildPayload, data: serverData } = useEntityDetail('collections')
const collectionMetadataStore = useCollectionMetadataStore()
const searchStore = useSearchStore()
const appStore = useAppStore()
const { semanticSearchAnswers } = storeToRefs(searchStore)

const { data: listData } = queries.collections.useList()
const { mutateAsync: updateCollection } = queries.collections.useUpdate()
const { mutateAsync: createCollection } = queries.collections.useCreate()

const showInfo = ref(false)
const showNewDialog = ref(false)
const showDeleteDialog = ref(false)
const showSyncConfirm = ref(false)
const saving = ref(false)
const job_id = ref(null)
const selectedChunk = ref(null)

const tabs = ref([
  { name: 'chunks', label: m.common_chunks() },
  { name: 'metadata', label: m.common_metadata() },
  { name: 'settings', label: m.common_settings() },
  { name: 'scheduler', label: m.common_scheduleAndRuns() },
])
const tab = ref('chunks')

function clearSemanticSearchAnswers() {
  semanticSearchAnswers.value = []
}

const items = computed(() => listData.value?.items || [])

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
const loading = computed(() => !draft.value?.id)
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
  window.open(router.resolve({ path: `/jobs/?job_id=${job_id.value}` }).href, '_blank')
}

async function deleteKnowledge() {
  saving.value = true
  try {
    const result = await remove()
    if (!result.success) throw result.error || new Error('Failed to delete')
    emit('update:closeDrawer', null)
    q.notify({
      color: 'green-9', textColor: 'white',
      icon: 'check_circle',
      group: 'success',
      message: m.notify_entityDeleted({ entity: m.entity_knowledgeSource() }),
      timeout: 1000,
    })
    navigate('/knowledge-sources')
  } catch (error) {
    const errorMessage = error?.message || m.notify_failedToDelete()
    q.notify({
      color: 'red-9', textColor: 'white',
      icon: 'error',
      group: 'error',
      message: errorMessage,
      timeout: 3000,
    })
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

  q.notify({
    color: 'green-9', textColor: 'white',
    icon: 'check_circle',
    group: 'success',
    message: m.collections_syncJobCreated(),
    timeout: 1000,
  })
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
    q.notify({
      color: 'red-9', textColor: 'white',
      icon: 'error',
      group: 'error',
      message: systemNameValidation,
      timeout: 3000,
    })
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
    q.notify({
      color: 'green-9', textColor: 'white',
      icon: 'check_circle',
      group: 'success',
      message: m.notify_savedSuccessfully(),
      timeout: 2000,
    })
  } catch (error) {
    q.notify({
      color: 'red-9', textColor: 'white',
      icon: 'error',
      group: 'error',
      message: error.message || 'Failed to save',
      timeout: 3000,
    })
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

<style lang="stylus">

@keyframes wobble {
    0% { transform: rotate(-5deg); }
    50% { transform: rotate(5deg); }
    100% { transform: rotate(-5deg); }
}

.wobble {
    animation: wobble 2s infinite;
}
</style>
