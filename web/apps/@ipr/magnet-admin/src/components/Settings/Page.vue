<template lang="pug">
.row.no-wrap.overflow-hidden.full-height
  q-scroll-area.fit
    .row.no-wrap.full-height.justify-center.fit
      .col-auto.collection-container.full-width
        .full-height.q-pb-md.relative-position.q-px-md.q-mt-lg
          q-tabs(
            :model-value='activeTab',
            align='left',
            active-color='primary',
            indicator-color='primary',
            active-bg-color='white',
            no-caps,
            content-class='km-tabs',
            @update:model-value='onTabChange'
          )
            q-tab(name='seed-data', label='Seed Data')
            q-tab(name='export-data', label='Export Data')

          .border.border-radius-12.bg-white.ba-border.q-my-16.q-pa-16.q-gap-16.full-width(v-if='activeTab === "seed-data"')
            .row.items-center.q-mb-md
              .km-heading-7 Seed Data
              q-space
              km-btn.q-mr-8(flat, label='Add from JSON', icon='fas fa-upload', @click='showUploadDialog = true')
              km-btn.q-mr-8(flat, label='Add from Seed', icon='fas fa-database', :loading='loadingPreview', @click='addFromSeed')
              km-btn.q-mr-8(
                label='Load Selected',
                :disable='selected.length === 0 || populating',
                :loading='populating',
                @click='loadSelected'
              )
              km-btn(flat, label='Clear List', icon='fas fa-trash', :disable='rows.length === 0 || populating', @click='clearList')
            .row.bg-light.full-width.q-py-4.q-px-8.q-gap-8.no-wrap.items-center.q-mb-md
              q-icon(name='o_info', color='icon', size='20px', style='min-width: 20px')
              .km-paragraph.q-pb-4 The list is empty by default. Add candidate records from Seed or JSON, select needed rows, then click Load Selected.
            .row(v-if='rows.length === 0').q-mb-md.bg-light.q-pa-sm.border-radius-6
              .km-description.text-secondary-text The list is empty. Use Add from Seed or Add from JSON.
            .row(v-if='selectedHasExisting').q-mb-md.bg-warning-low.q-pa-sm.border-radius-6
              .km-description.text-primary Existing selected records will be overwritten.
            q-table.full-width(
              :rows='displayRows',
              :columns='columns',
              row-key='row_key',
              selection='multiple',
              v-model:selected='selected',
              :loading='loadingPreview || populating',
              :pagination='{ rowsPerPage: 10 }',
              flat
            )
              template(v-slot:header-selection)
                q-checkbox(
                  dense,
                  :model-value='allSeedRowsSelected',
                  :indeterminate='someSeedRowsSelected',
                  @update:model-value='toggleSelectAllSeedRows'
                )
              template(v-slot:body-cell-source='props')
                q-td(:props='props')
                  q-chip(size='sm', color='primary-light', text-color='primary') {{ props.row.source === 'seed' ? 'Seed' : 'JSON' }}
              template(v-slot:body-cell-exists='props')
                q-td(:props='props')
                  q-chip(size='sm', color='primary-light', text-color='primary', v-if='props.row.exists === null') Unknown
                  q-chip(size='sm', :color='props.row.exists ? "orange-2" : "green-2"', :text-color='props.row.exists ? "orange-8" : "green-8"', v-else)
                    | {{ props.row.exists ? 'Already loaded' : 'Missing' }}
              template(v-slot:body-cell-overwrite='props')
                q-td(:props='props')
                  .km-description.text-primary(v-if='props.row.overwrite') Will be overwritten
              template(v-slot:body-cell-progress='props')
                q-td(:props='props')
                  .row.items-center.q-gap-8
                    q-spinner(size='14px', color='primary', v-if='props.row.progress === "loading"')
                    q-chip(size='sm', color='green-2', text-color='green-8', v-if='props.row.progress === "success"') Loaded
                    q-chip(size='sm', color='red-2', text-color='red-8', v-if='props.row.progress === "error"') Error
                    .km-description.text-secondary-text(v-if='props.row.progressMessage') {{ props.row.progressMessage }}

            .row.q-mt-md.items-center
              .col
                q-linear-progress(v-if='populating', :value='progressValue', color='primary', rounded, size='8px')

          .border.border-radius-12.bg-white.ba-border.q-my-16.q-pa-16.q-gap-16.full-width(v-if='activeTab === "export-data"')
            .row.items-center.q-mb-md
              .km-heading-7 Export Data
              q-space
              km-btn.q-mr-8(flat, label='Add from Database', icon='fas fa-database', :loading='loadingExportPreview', @click='addFromDatabase')
              km-btn.q-mr-8(
                label='Export Selected',
                :disable='selectedExport.length === 0 || exportingJson',
                :loading='exportingJson',
                @click='exportSelected'
              )
              km-btn(flat, label='Clear List', icon='fas fa-trash', :disable='exportRows.length === 0 || exportingJson', @click='clearExportList')
            .row.q-col-gutter-md.q-mb-md
              .col-4
                km-input(placeholder='Search', iconBefore='search', v-model='exportSearch', clearable)
              .col-4
                q-select(
                  outlined,
                  dense,
                  v-model='exportEntityTypeFilter',
                  :options='exportEntityTypeOptions',
                  emit-value,
                  map-options,
                  option-label='label',
                  option-value='value',
                  label='Entity Type'
                )
              .col-4
                km-input(placeholder='Filter by Name', v-model='exportNameFilter', clearable)
            .row.bg-light.full-width.q-py-4.q-px-8.q-gap-8.no-wrap.items-center.q-mb-md
              q-icon(name='o_info', color='icon', size='20px', style='min-width: 20px')
              .km-paragraph.q-pb-4 Add records from any entity, select needed rows, then click Export Selected to download JSON in import format.
            .row(v-if='exportRows.length === 0').q-mb-md.bg-light.q-pa-sm.border-radius-6
              .km-description.text-secondary-text The list is empty. Use Add from Database.
            q-table.full-width(
              :rows='filteredExportRows',
              :columns='exportColumns',
              row-key='row_key',
              selection='multiple',
              v-model:selected='selectedExport',
              :loading='loadingExportPreview || exportingJson',
              :pagination='{ rowsPerPage: 10 }',
              flat
            )
              template(v-slot:header-selection)
                q-checkbox(
                  dense,
                  :model-value='allExportRowsSelected',
                  :indeterminate='someExportRowsSelected',
                  @update:model-value='toggleSelectAllExportRows'
                )

  q-dialog(:model-value='showUploadDialog', @update:model-value='showUploadDialog = $event')
    q-card.card-style(style='min-width: 700px')
      q-card-section.card-section-style
        .row.items-center
          .km-heading-7 Add from JSON
          q-space
          q-btn(icon='close', flat, dense, @click='showUploadDialog = false')
      q-card-section.card-section-style
        .row.q-col-gutter-md
          .col-12
            .km-field.text-secondary-text.q-pb-xs JSON File
            q-file(
              outlined,
              dense,
              label='Upload File',
              accept='.json,application/json',
              v-model='uploadFile',
              clearable
            )
      q-card-actions.card-section-style(align='right')
        km-btn(flat, label='Cancel', @click='showUploadDialog = false')
        km-btn(
          label='Add to List',
          :disable='!uploadFile || uploadingJson',
          :loading='uploadingJson',
          @click='addFromJson'
        )
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { useQuasar } from 'quasar'
import { fetchData } from '@shared'

const route = useRoute()
const router = useRouter()
const store = useStore()
const $q = useQuasar()

const loadingPreview = ref(false)
const loadingExportPreview = ref(false)
const populating = ref(false)
const uploadingJson = ref(false)
const exportingJson = ref(false)
const showUploadDialog = ref(false)

const rows = ref([])
const selected = ref([])
const progressByKey = ref({})
const jsonPayloadByKey = ref({})
const exportRows = ref([])
const selectedExport = ref([])
const exportSearch = ref('')
const exportEntityTypeFilter = ref('all')
const exportNameFilter = ref('')

const uploadFile = ref(null)

const adminEndpoint = computed(() => store.getters.config?.api?.aiBridge?.urlAdmin || '')
const requestCredentials = computed(() => store.getters.config?.auth?.enabled ? 'include' : undefined)
const activeTab = computed(() => (route.params.tab || 'seed-data'))

const onTabChange = async (tab) => {
  if (tab && tab !== route.params.tab) {
    await router.push(`/settings/${tab}`)
  }
}

const columns = [
  { name: 'source', label: 'Source', field: 'source', align: 'left', sortable: true },
  { name: 'entity_type', label: 'Entity Type', field: 'entity_type', align: 'left', sortable: true },
  { name: 'system_name', label: 'System Name', field: 'system_name', align: 'left', sortable: true },
  { name: 'exists', label: 'Status', field: 'exists', align: 'left' },
  { name: 'overwrite', label: 'Overwrite', field: 'overwrite', align: 'left' },
  { name: 'progress', label: 'Progress', field: 'progress', align: 'left' },
]

const exportColumns = [
  { name: 'entity_type', label: 'Entity Type', field: 'entity_type', align: 'left', sortable: true },
  { name: 'name', label: 'Name', field: 'name', align: 'left', sortable: true },
  { name: 'system_name', label: 'System Name', field: 'system_name', align: 'left', sortable: true },
]

const exportEntityTypeOptions = computed(() => {
  const values = [...new Set(exportRows.value.map((row) => row.entity_type))].sort()
  return [{ label: 'All', value: 'all' }, ...values.map((value) => ({ label: value, value }))]
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

const allSeedRowsSelected = computed(() => {
  if (!displayRows.value.length) return false
  return displayRows.value.every((row) => selectedKeySet.value.has(row.row_key))
})

const someSeedRowsSelected = computed(() => {
  if (!displayRows.value.length || allSeedRowsSelected.value) return false
  return displayRows.value.some((row) => selectedKeySet.value.has(row.row_key))
})

const allExportRowsSelected = computed(() => {
  if (!filteredExportRows.value.length) return false
  return filteredExportRows.value.every((row) => selectedExportKeySet.value.has(row.row_key))
})

const someExportRowsSelected = computed(() => {
  if (!filteredExportRows.value.length || allExportRowsSelected.value) return false
  return filteredExportRows.value.some((row) => selectedExportKeySet.value.has(row.row_key))
})

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
    $q.notify({ type: 'negative', message: 'Failed to load seed preview' })
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

  $q.notify({ type: 'positive', message: `Added ${seedRows.length} records from seed to the list.` })
}

const clearList = () => {
  rows.value = []
  selected.value = []
  progressByKey.value = {}
  jsonPayloadByKey.value = {}
}

const toggleSelectAllSeedRows = (value) => {
  selected.value = value ? [...displayRows.value] : []
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
    $q.notify({ type: 'negative', message: 'Failed to load export preview.' })
    return
  }

  const data = await response.json()
  exportRows.value = (data.items || []).map((item) => ({
    ...item,
    name: item.name || '',
    row_key: `${item.entity_type}:${item.system_name}`,
  }))

  selectedExport.value = []

  $q.notify({ type: 'positive', message: `Added ${exportRows.value.length} records to export list.` })
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
    $q.notify({ type: 'negative', message: 'Failed to export records.' })
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

  $q.notify({ type: 'positive', message: 'Export file generated.' })
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
          message: 'Failed to load',
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
        message: overwritten ? 'Overwritten' : 'Created',
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
    $q.notify({ type: 'negative', message: 'Invalid JSON file' })
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
      $q.notify({
        type: 'negative',
        message: 'Export JSON must contain entity keys with arrays of records that include system_name.',
      })
      return
    }
  } else {
    const payloadItems = Array.isArray(payload) ? payload : [payload]
    const invalidItems = payloadItems.filter(
      (item) => !item || typeof item !== 'object' || !item.system_name || !item.entity_type
    )

    if (invalidItems.length > 0) {
      uploadingJson.value = false
      $q.notify({ type: 'negative', message: 'Each JSON record must include entity_type and system_name.' })
      return
    }

    payloadItems.forEach((item) => {
      addRecord(item.entity_type, item)
    })
  }

  mergeRows(normalizedRows)

  uploadingJson.value = false

  $q.notify({
    type: 'positive',
    message: `Added ${normalizedRows.length} JSON records to the list.`,
  })

  uploadFile.value = null
  showUploadDialog.value = false
}

onMounted(async () => {
  if (activeTab.value !== 'seed-data') {
    await router.replace('/settings/seed-data')
  }
})
</script>
