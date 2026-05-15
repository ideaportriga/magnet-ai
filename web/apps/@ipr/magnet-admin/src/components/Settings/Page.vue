<template>
  <div class="cluster overflow-hidden full-height" data-wrap="no">
    <km-scroll-area class="fit">
      <div class="flex full-height fit" style="justify-content: center; flex-wrap: nowrap">
        <div class="flex-none collection-container full-width">
          <div class="full-height pb-md relative-position px-md mt-lg">
            <km-tabs :model-value="activeTab" align="left" no-caps content-class="km-tabs" @update:model-value="onTabChange">
              <km-tab name="import" :label="m.common_import()" />
              <km-tab name="export" :label="m.common_export()" />
            </km-tabs>
            <div v-if="activeTab === &quot;import&quot;" class="ba-border border-radius-12 bg-white my-lg p-lg full-width relative-position">
              <km-inner-loading :showing="loadingPreview || populating || checkingExists">
                <div class="km-description text-primary mt-sm">{{ loadingPreview ? m.settings_loadingSeedRecords() : populating ? m.settings_importingRecords() : m.settings_checkingRecords() }}</div>
              </km-inner-loading>
              <div class="cluster mb-md" data-justify="between">
                <div class="km-heading-7">{{ m.settings_importHeading() }}</div>
                <div class="km-space" />
                <km-btn class="mr-sm" flat :label="m.common_addFromJson()" icon="upload" @click="showUploadDialog = true" />
                <km-btn class="mr-sm" flat :label="m.common_addFromSeed()" icon="database" :loading="loadingPreview" @click="addFromSeed" />
                <km-btn class="mr-sm" :label="m.common_loadSelected()" :disable="selected.length === 0 || populating" :loading="populating" @click="loadSelected" />
                <km-btn flat :label="m.common_clearList()" icon="delete" :disable="rows.length === 0 || populating" @click="clearList" />
              </div>
              <div class="cluster full-width py-xs px-sm mb-md bg-light" data-gap="sm" data-wrap="no">
                <km-notification-text :notification="m.settings_importHint()" />
              </div>
              <div class="cluster mb-md" data-gap="md">
                <div class="basis-2">
                  <km-input v-model="importSearch" :placeholder="m.common_search()" icon-before="search" clearable />
                </div>
                <div class="basis-1">
                  <km-select v-model="importEntityTypeFilter" :options="importEntityTypeOptions" emit-value map-options option-label="label" option-value="value" :placeholder="m.settings_entityTypePlaceholder()" />
                </div>
                <div class="basis-1">
                  <km-select v-model="importStatusFilter" :options="importStatusOptions" emit-value map-options option-label="label" option-value="value" :placeholder="m.common_status()" />
                </div>
              </div>
              <div v-if="rows.length === 0" class="cluster mb-md bg-light p-sm border-radius-6">
                <div class="km-description text-secondary-text">{{ m.settings_importListEmpty() }}</div>
              </div>
              <div v-if="selectedHasExisting" class="cluster mb-md bg-warning-low p-sm border-radius-6">
                <div class="km-description text-primary">{{ m.settings_existingWillBeOverwritten() }}</div>
              </div>
              <km-data-table :table="importTable" row-key="row_key" hide-pagination>
                <template #header-_select>
                  <km-checkbox dense size="sm" :model-value="allImportSelected" :indeterminate="someImportSelected && !allImportSelected" :disable="filteredImportRows.length === 0" @update:model-value="toggleSelectAllSeedRows" @click.stop />
                </template>
                <template #cell-_select="{ row }">
                  <km-checkbox dense size="sm" :model-value="selectedKeySet.has(row.row_key)" @update:model-value="toggleImportRow(row, $event)" @click.stop />
                </template>
                <template #cell-source="{ row }">
                  <km-chip tone="brand" size="sm">{{ row.source === 'seed' ? m.settings_sourceSeed() : m.settings_sourceJson() }}</km-chip>
                </template>
                <template #cell-exists="{ row }">
                  <km-chip v-if="row.exists === null" tone="brand" size="sm">{{ m.settings_unknown() }}</km-chip>
                  <km-chip v-else size="sm" :tone="row.exists ? &quot;warning&quot; : &quot;success&quot;">{{ row.exists ? m.settings_alreadyLoaded() : m.settings_missing() }}</km-chip>
                </template>
                <template #cell-overwrite="{ row }">
                  <div v-if="row.overwrite" class="km-description text-primary">{{ m.settings_willBeOverwritten() }}</div>
                </template>
                <template #cell-progress="{ row }">
                  <div class="cluster" data-gap="sm">
                    <km-loader v-if="row.progress === &quot;loading&quot;" size="14px" />
                    <km-chip v-if="row.progress === &quot;success&quot;" size="sm" tone="success">{{ m.settings_progressLoaded() }}</km-chip>
                    <km-chip v-if="row.progress === &quot;error&quot;" size="sm" tone="danger">{{ m.settings_progressError() }}</km-chip>
                    <div v-if="row.progressMessage" class="km-description text-secondary-text">{{ row.progressMessage }}</div>
                  </div>
                </template>
              </km-data-table>
              <div class="cluster mt-md">
                <div class="flex-1">
                  <km-linear-progress v-if="populating" :value="progressValue" rounded size="8px" />
                </div>
              </div>
            </div>
            <div v-if="activeTab === &quot;export&quot;" class="ba-border border-radius-12 bg-white my-lg p-lg full-width relative-position">
              <km-inner-loading :showing="loadingExportPreview || exportingJson">
                <div class="km-description text-primary mt-sm">{{ loadingExportPreview ? m.settings_loadingFromDb() : m.settings_exportingRecords() }}</div>
              </km-inner-loading>
              <div class="cluster mb-md" data-justify="between">
                <div class="km-heading-7">{{ m.settings_exportHeading() }}</div>
                <div class="km-space" />
                <km-btn class="mr-sm" flat :label="m.common_addFromDatabase()" icon="database" :loading="loadingExportPreview" @click="addFromDatabase" />
                <km-btn class="mr-sm" :label="m.common_exportSelected()" :disable="selectedExport.length === 0 || exportingJson" :loading="exportingJson" @click="exportSelected" />
                <km-btn flat :label="m.common_clearList()" icon="delete" :disable="exportRows.length === 0 || exportingJson" @click="clearExportList" />
              </div>
              <div class="cluster mb-md" data-gap="md">
                <div class="basis-4">
                  <km-input v-model="exportSearch" :placeholder="m.common_search()" icon-before="search" clearable />
                </div>
                <div class="basis-4">
                  <km-select v-model="exportEntityTypeFilter" :options="exportEntityTypeOptions" emit-value map-options option-label="label" option-value="value" :placeholder="m.settings_entityTypePlaceholder()" />
                </div>
                <div class="basis-4">
                  <km-input v-model="exportNameFilter" :placeholder="m.settings_filterByName()" clearable />
                </div>
              </div>
              <div v-if="exportRows.length === 0" class="cluster mb-md bg-light p-sm border-radius-6">
                <div class="km-description text-secondary-text">{{ m.settings_exportListEmpty() }}</div>
              </div>
              <km-data-table :table="exportTable" row-key="row_key" hide-pagination>
                <template #header-_select>
                  <km-checkbox dense size="sm" :model-value="allExportSelected" :indeterminate="someExportSelected && !allExportSelected" :disable="filteredExportRows.length === 0" @update:model-value="toggleSelectAllExportRows" @click.stop />
                </template>
                <template #cell-_select="{ row }">
                  <km-checkbox dense size="sm" :model-value="selectedExportKeySet.has(row.row_key)" @update:model-value="toggleExportRow(row, $event)" @click.stop />
                </template>
              </km-data-table>
            </div>
          </div>
        </div>
      </div>
    </km-scroll-area>
    <km-dialog :model-value="showUploadDialog" @update:model-value="showUploadDialog = $event">
      <km-card class="card-style" style="min-inline-size: 700px">
        <div class="km-card-section card-section-style">
          <div class="cluster" data-justify="between">
            <div class="km-heading-7">{{ m.settings_addFromJsonTitle() }}</div>
            <div class="km-space" />
            <km-btn icon="close" flat dense @click="showUploadDialog = false" />
          </div>
        </div>
        <div class="km-card-section card-section-style">
          <div class="cluster" data-gap="md">
            <div class="basis-12">
              <div class="km-field text-secondary-text pb-xs">{{ m.settings_jsonFileLabel() }}</div>
              <km-file-picker v-model="uploadFile" outlined dense :label="m.common_uploadFile()" accept=".json,application/json" clearable />
            </div>
          </div>
        </div>
        <div class="km-card-actions card-section-style" align="right">
          <km-btn flat :label="m.common_cancel()" @click="showUploadDialog = false" />
          <km-btn :label="m.common_addToList()" :disable="!uploadFile || uploadingJson" :loading="uploadingJson" @click="addFromJson" />
        </div>
      </km-card>
    </km-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { m } from '@/paraglide/messages'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/appStore'
import { fetchData } from '@shared'
import { useNotify } from '@/composables/useNotify'
import { useLocalDataTable } from '@/composables/useLocalDataTable'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const { notifySuccess, notifyError } = useNotify()

const loadingPreview = ref(false)
const loadingExportPreview = ref(false)
const populating = ref(false)
const uploadingJson = ref(false)
const checkingExists = ref(false)
const exportingJson = ref(false)
const showUploadDialog = ref(false)

const rows = ref([])
const selected = ref([])
const progressByKey = ref({})
const jsonPayloadByKey = ref({})
const exportRows = ref([])
const selectedExport = ref([])
const importSearch = ref('')
const importEntityTypeFilter = ref('all')
const importStatusFilter = ref('all')
const exportSearch = ref('')
const exportEntityTypeFilter = ref('all')
const exportNameFilter = ref('')

const uploadFile = ref(null)

const adminEndpoint = computed(() => appStore.config?.api?.aiBridge?.urlAdmin || '')
const requestCredentials = computed(() => appStore.config?.auth?.enabled ? 'include' : undefined)
const allowedTabs = ['import', 'export']
const activeTab = computed(() => {
  const tab = route.params.tab
  return allowedTabs.includes(tab) ? tab : 'import'
})

const onTabChange = async (tab) => {
  if (tab && tab !== route.params.tab) {
    await router.push(`/settings/${tab}`)
  }
}

// §E.3.1 — TanStack columns. The leading `_select` column renders a
// custom checkbox via the #cell-_select slot that binds to our external
// `selected` / `selectedExport` refs (preserves per-filter select-all
// semantics from the original q-table implementation).
const columns = [
  { id: '_select', header: '', enableSorting: false, meta: { align: 'center', width: '40px' } },
  { id: 'source', accessorKey: 'source', header: m.settings_colSource(), enableSorting: true, meta: { align: 'left' } },
  { id: 'entity_type', accessorKey: 'entity_type', header: m.settings_colEntityType(), enableSorting: true, meta: { align: 'left' } },
  { id: 'system_name', accessorKey: 'system_name', header: m.settings_colSystemName(), enableSorting: true, meta: { align: 'left' } },
  { id: 'exists', accessorKey: 'exists', header: m.common_status(), enableSorting: false, meta: { align: 'left' } },
  { id: 'overwrite', header: m.settings_colOverwrite(), enableSorting: false, meta: { align: 'left' } },
  { id: 'progress', header: m.settings_colProgress(), enableSorting: false, meta: { align: 'left' } },
]

const exportColumns = [
  { id: '_select', header: '', enableSorting: false, meta: { align: 'center', width: '40px' } },
  { id: 'entity_type', accessorKey: 'entity_type', header: m.settings_colEntityType(), enableSorting: true, meta: { align: 'left' } },
  { id: 'name', accessorKey: 'name', header: m.common_name(), enableSorting: true, meta: { align: 'left' } },
  { id: 'system_name', accessorKey: 'system_name', header: m.settings_colSystemName(), enableSorting: true, meta: { align: 'left' } },
]

const importEntityTypeOptions = computed(() => {
  const values = [...new Set(rows.value.map((row) => row.entity_type))].sort()
  return [{ label: m.common_all(), value: 'all' }, ...values.map((value) => ({ label: value, value }))]
})

const importStatusOptions = computed(() => [
  { label: m.common_all(), value: 'all' },
  { label: m.settings_missing(), value: 'missing' },
  { label: m.settings_alreadyLoaded(), value: 'loaded' },
  { label: m.settings_unknown(), value: 'unknown' },
])

const filteredImportRows = computed(() => {
  const search = importSearch.value?.trim().toLowerCase() || ''

  return displayRows.value.filter((row) => {
    const byType = importEntityTypeFilter.value === 'all' || row.entity_type === importEntityTypeFilter.value
    const rowSystemName = String(row.system_name || '').toLowerCase()
    const rowEntity = String(row.entity_type || '').toLowerCase()
    const bySearch = !search || rowSystemName.includes(search) || rowEntity.includes(search)
    const byStatus =
      importStatusFilter.value === 'all' ||
      (importStatusFilter.value === 'unknown' && row.exists === null) ||
      (importStatusFilter.value === 'missing' && row.exists === false) ||
      (importStatusFilter.value === 'loaded' && row.exists === true)
    return byType && bySearch && byStatus
  })
})

const exportEntityTypeOptions = computed(() => {
  const values = [...new Set(exportRows.value.map((row) => row.entity_type))].sort()
  return [{ label: m.common_all(), value: 'all' }, ...values.map((value) => ({ label: value, value }))]
})

const filteredExportRows = computed(() => {
  const search = exportSearch.value?.trim().toLowerCase() || ''
  const nameFilter = exportNameFilter.value?.trim().toLowerCase() || ''

  return exportRows.value.filter((row) => {
    const byType = exportEntityTypeFilter.value === 'all' || row.entity_type === exportEntityTypeFilter.value
    const rowName = String(row.name || '').toLowerCase()
    const rowSystemName = String(row.system_name || '').toLowerCase()
    const rowEntity = String(row.entity_type || '').toLowerCase()

    const byName = !nameFilter || rowName.includes(nameFilter)
    const bySearch = !search || rowSystemName.includes(search) || rowName.includes(search) || rowEntity.includes(search)

    return byType && byName && bySearch
  })
})

const selectedKeySet = computed(() => new Set(selected.value.map((row) => row.row_key)))
const selectedExportKeySet = computed(() => new Set(selectedExport.value.map((row) => row.row_key)))

const allImportSelected = computed(() =>
  filteredImportRows.value.length > 0 &&
  filteredImportRows.value.every((row) => selectedKeySet.value.has(row.row_key))
)
const someImportSelected = computed(() =>
  filteredImportRows.value.some((row) => selectedKeySet.value.has(row.row_key))
)
const allExportSelected = computed(() =>
  filteredExportRows.value.length > 0 &&
  filteredExportRows.value.every((row) => selectedExportKeySet.value.has(row.row_key))
)
const someExportSelected = computed(() =>
  filteredExportRows.value.some((row) => selectedExportKeySet.value.has(row.row_key))
)

const displayRows = computed(() => {
  return rows.value.map((row) => {
    const progress = progressByKey.value[row.row_key] || {}
    const overwrite = selectedKeySet.value.has(row.row_key) && row.exists === true

    return {
      ...row,
      overwrite,
      progress: progress.status || '',
      progressMessage: progress.message || '',
    }
  })
})

const selectedHasExisting = computed(() => selected.value.some((row) => row.exists))

// §E.3.1 — TanStack tables (client-side pagination disabled — hide-pagination).
const { table: importTable } = useLocalDataTable(
  filteredImportRows,
  columns,
  { defaultPageSize: 1000 },
)
const { table: exportTable } = useLocalDataTable(
  filteredExportRows,
  exportColumns,
  { defaultPageSize: 1000 },
)

// Per-row checkbox toggles for the custom `_select` cell.
function toggleImportRow(row, value) {
  if (value) {
    if (!selectedKeySet.value.has(row.row_key)) {
      selected.value = [...selected.value, row]
    }
  } else {
    selected.value = selected.value.filter((r) => r.row_key !== row.row_key)
  }
}

function toggleExportRow(row, value) {
  if (value) {
    if (!selectedExportKeySet.value.has(row.row_key)) {
      selectedExport.value = [...selectedExport.value, row]
    }
  } else {
    selectedExport.value = selectedExport.value.filter((r) => r.row_key !== row.row_key)
  }
}

const progressValue = computed(() => {
  const total = selected.value.length
  if (!total) return 0

  const done = selected.value.filter((row) => {
    const status = progressByKey.value[row.row_key]?.status
    return status === 'success' || status === 'error'
  }).length

  return done / total
})

const mergeRows = (newRows) => {
  const existingByKey = new Map(rows.value.map((row) => [row.row_key, row]))

  newRows.forEach((row) => {
    existingByKey.set(row.row_key, row)
  })

  rows.value = [...existingByKey.values()]
}

const addFromSeed = async () => {
  loadingPreview.value = true

  const response = await fetchData({
    endpoint: adminEndpoint.value,
    service: 'settings/seed/preview',
    credentials: requestCredentials.value,
  })

  loadingPreview.value = false

  if (response?.error) {
    notifyError(m.settings_failedLoadSeedPreview())
    return
  }

  const data = await response.json()
  const seedRows = (data.items || []).map((item) => ({
    ...item,
    source: 'seed',
    row_key: `${item.entity_type}:${item.system_name}`,
  }))

  const nonSeedRows = rows.value.filter((row) => row.source !== 'seed')
  rows.value = [...nonSeedRows]
  mergeRows(seedRows)

  notifySuccess(m.settings_addedSeedRecords({ count: String(seedRows.length) }))
}

const clearList = () => {
  rows.value = []
  selected.value = []
  progressByKey.value = {}
  jsonPayloadByKey.value = {}
  importSearch.value = ''
  importEntityTypeFilter.value = 'all'
  importStatusFilter.value = 'all'
}

const toggleSelectAllSeedRows = (value) => {
  if (value) {
    const selectedMap = new Map(selected.value.map((row) => [row.row_key, row]))
    filteredImportRows.value.forEach((row) => {
      selectedMap.set(row.row_key, row)
    })
    selected.value = [...selectedMap.values()]
    return
  }

  const filteredKeys = new Set(filteredImportRows.value.map((row) => row.row_key))
  selected.value = selected.value.filter((row) => !filteredKeys.has(row.row_key))
}

const clearExportList = () => {
  exportRows.value = []
  selectedExport.value = []
  exportSearch.value = ''
  exportEntityTypeFilter.value = 'all'
  exportNameFilter.value = ''
}


const toggleSelectAllExportRows = (value) => {
  if (value) {
    const selectedMap = new Map(selectedExport.value.map((row) => [row.row_key, row]))
    filteredExportRows.value.forEach((row) => {
      selectedMap.set(row.row_key, row)
    })
    selectedExport.value = [...selectedMap.values()]
    return
  }

  const filteredKeys = new Set(filteredExportRows.value.map((row) => row.row_key))
  selectedExport.value = selectedExport.value.filter((row) => !filteredKeys.has(row.row_key))
}

const addFromDatabase = async () => {
  loadingExportPreview.value = true

  const response = await fetchData({
    endpoint: adminEndpoint.value,
    service: 'settings/seed/export-preview',
    credentials: requestCredentials.value,
  })

  loadingExportPreview.value = false

  if (response?.error) {
    notifyError(m.settings_failedLoadExportPreview())
    return
  }

  const data = await response.json()
  exportRows.value = (data.items || []).map((item) => ({
    ...item,
    name: item.name || '',
    row_key: `${item.entity_type}:${item.system_name}`,
  }))

  selectedExport.value = []

  notifySuccess(m.settings_addedExportRecords({ count: String(exportRows.value.length) }))
}

const exportSelected = async () => {
  if (!selectedExport.value.length) {
    return
  }

  exportingJson.value = true

  const response = await fetchData({
    endpoint: adminEndpoint.value,
    service: 'settings/seed/export-json',
    method: 'POST',
    credentials: requestCredentials.value,
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      items: selectedExport.value.map((row) => ({
        entity_type: row.entity_type,
        system_name: row.system_name,
      })),
    }),
  })

  exportingJson.value = false

  if (response?.error) {
    notifyError(m.settings_failedExportRecords())
    return
  }

  const result = await response.json()
  const content = JSON.stringify(result?.data || {}, null, 2)
  const blob = new Blob([content], { type: 'application/json' })
  const fileUrl = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = fileUrl
  anchor.download = `settings_export_${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')}.json`
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(fileUrl)

  notifySuccess(m.settings_exportFileGenerated())
}

const loadSelected = async () => {
  if (!selected.value.length) {
    return
  }

  populating.value = true
  const rowsToLoad = [...selected.value]

  for (const row of rowsToLoad) {
    progressByKey.value = {
      ...progressByKey.value,
      [row.row_key]: {
        status: 'loading',
        message: '',
      },
    }

    let response
    if (row.source === 'seed') {
      response = await fetchData({
        endpoint: adminEndpoint.value,
        service: 'settings/seed/populate-one',
        method: 'POST',
        credentials: requestCredentials.value,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          entity_type: row.entity_type,
          system_name: row.system_name,
        }),
      })
    } else {
      response = await fetchData({
        endpoint: adminEndpoint.value,
        service: 'settings/seed/upload-json',
        method: 'POST',
        credentials: requestCredentials.value,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          entity_type: row.entity_type,
          payload: jsonPayloadByKey.value[row.row_key],
        }),
      })
    }

    if (response?.error) {
      progressByKey.value = {
        ...progressByKey.value,
        [row.row_key]: {
          status: 'error',
          message: m.settings_failedToLoad(),
        },
      }
      continue
    }

    const result = await response.json()
    const overwritten = row.source === 'seed' ? result.overwritten : result?.results?.[0]?.overwritten

    progressByKey.value = {
      ...progressByKey.value,
      [row.row_key]: {
        status: 'success',
        message: overwritten ? m.settings_recordOverwritten() : m.settings_recordCreated(),
      },
    }

    rows.value = rows.value.map((item) => {
      if (item.row_key !== row.row_key) return item
      return { ...item, exists: true }
    })
  }

  populating.value = false
  selected.value = []
}

const addFromJson = async () => {
  if (!uploadFile.value) {
    return
  }

  uploadingJson.value = true

  let payload
  try {
    const content = await uploadFile.value.text()
    payload = JSON.parse(content)
  } catch {
    uploadingJson.value = false
    notifyError(m.settings_invalidJsonFile())
    return
  }

  const normalizedRows = []

  const addRecord = (entityType, item) => {
    if (!item || typeof item !== 'object' || !entityType) return false

    const systemName = item.system_name
    if (!systemName) return false

    const rowKey = `${entityType}:${systemName}`
    jsonPayloadByKey.value[rowKey] = item
    normalizedRows.push({
      source: 'json',
      entity_type: entityType,
      system_name: systemName,
      exists: null,
      row_key: rowKey,
    })
    return true
  }

  const isExportFormat = payload && !Array.isArray(payload) && typeof payload === 'object' && !payload.system_name
  const exportData = isExportFormat && payload.data && typeof payload.data === 'object' ? payload.data : payload

  if (isExportFormat && exportData && typeof exportData === 'object') {
    Object.entries(exportData).forEach(([entityType, records]) => {
      if (!Array.isArray(records)) return
      records.forEach((item) => {
        addRecord(entityType, item)
      })
    })

    if (!normalizedRows.length) {
      uploadingJson.value = false
      notifyError(m.settings_invalidExportJson())
      return
    }
  } else {
    const payloadItems = Array.isArray(payload) ? payload : [payload]
    const invalidItems = payloadItems.filter(
      (item) => !item || typeof item !== 'object' || !item.system_name || !item.entity_type
    )

    if (invalidItems.length > 0) {
      uploadingJson.value = false
      notifyError(m.settings_invalidRecordJson())
      return
    }

    payloadItems.forEach((item) => {
      addRecord(item.entity_type, item)
    })
  }

  mergeRows(normalizedRows)

  uploadingJson.value = false
  uploadFile.value = null
  showUploadDialog.value = false

  // Check which records already exist in the database (after dialog closes so overlay is visible)
  checkingExists.value = true
  const checkResponse = await fetchData({
    endpoint: adminEndpoint.value,
    service: 'settings/seed/check-exists',
    method: 'POST',
    credentials: requestCredentials.value,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      items: normalizedRows.map((row) => ({
        entity_type: row.entity_type,
        system_name: row.system_name,
      })),
    }),
  })

  if (!checkResponse?.error) {
    const checkData = await checkResponse.json()
    const existsMap = new Map(
      (checkData.items || []).map((item) => [`${item.entity_type}:${item.system_name}`, item.exists])
    )
    rows.value = rows.value.map((row) => {
      if (!existsMap.has(row.row_key)) return row
      return { ...row, exists: existsMap.get(row.row_key) }
    })
  }

  checkingExists.value = false

  notifySuccess(m.settings_addedJsonRecords({ count: String(normalizedRows.length) }))
}

onMounted(async () => {
  if (activeTab.value !== 'import') {
    await router.replace('/settings/import')
  }
})
</script>
