<template lang="pug">
.row.no-wrap.overflow-hidden.full-height
  q-scroll-area.fit
    .row.no-wrap.full-height.justify-center.fit
      .col-auto.collection-container
        .full-height.q-pb-md.relative-position.q-px-md
          .border.border-radius-12.bg-white.ba-border.q-my-16.q-pa-16.q-gap-16.full-width
            .row.q-mb-12
              q-space
              .col-auto.center-flex-y
                km-btn.q-mr-12(
                  icon='refresh',
                  label='Refresh list',
                  @click='refreshTable',
                  iconColor='icon',
                  hoverColor='primary',
                  labelClass='km-title',
                  flat,
                  iconSize='16px',
                  hoverBg='primary-bg'
                )
                km-btn(
                  label='New',
                  @click='showNewDialog = true'
                )
            .row
              km-table(
                @selectRow='openDetails',
                @request='onRequest',
                selection='single',
                row-key='id',
                :columns='columns',
                :visibleColumns='visibleColumns',
                :rows='runs',
                style='min-width: 1100px',
                binary-state-sort,
                :loading='loading',
                dense,
                v-model:pagination='pagination'
              )
        q-inner-loading(:showing='loading')

  //- New Run Dialog
  q-dialog(:model-value='showNewDialog', @update:model-value='showNewDialog = $event')
    q-card(style='min-width: 600px')
      q-card-section
        .text-h6 Create New Run

      q-card-section.q-pt-none
        q-form(@submit.prevent='createRun')
          .km-field.q-mb-md
            .text-secondary-text.q-pb-xs Config
            km-select(
              v-model='selectedConfigId',
              :options='configOptions',
              option-value='id',
              option-label='name',
              emit-value,
              map-options,
              height='30px',
              placeholder='Select a config'
              :rules='[val => !!val || "Config is required"]'
            )
            .km-description.text-secondary-text.q-pt-2 Select the research configuration to use

          .km-field.q-mb-md
            .text-secondary-text.q-pb-xs Input (JSON)
            q-input(
              v-model='runInput',
              type='textarea',
              outlined,
              rows='8',
              :rules='[validateJSON]'
              placeholder='{"query": "Research question here"}'
            )
            .km-description.text-secondary-text.q-pt-2 Provide the input data for the research run

          .km-field.q-mb-md
            .text-secondary-text.q-pb-xs Client ID (optional)
            km-input(
              v-model='runClientId',
              height='30px',
              placeholder='Optional client identifier'
            )

          q-card-actions(align='right')
            km-btn(flat, label='Cancel', color='primary', @click='closeDialog')
            km-btn(label='Create Run', :loading='creating', @click='createRun')
</template>

<script setup lang="ts">
import { ref, computed, onMounted, markRaw } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import { date, useQuasar } from 'quasar'
import StatusChip from './StatusChip.vue'

const store = useStore()
const router = useRouter()
const $q = useQuasar()

const loading = ref(false)
const showNewDialog = ref(false)
const creating = ref(false)
const selectedConfigId = ref<string | null>(null)
const runInput = ref('{"query": ""}')
const runClientId = ref('')

const pagination = ref({
  sortBy: 'updated_at',
  descending: true,
  page: 1,
  rowsPerPage: 15,
  rowsNumber: 0,
})

const getConfigMeta = (rawConfig: unknown) => {
  if (!rawConfig) {
    return null
  }

  if (typeof rawConfig === 'string') {
    try {
      return JSON.parse(rawConfig)
    } catch (error) {
      console.warn('Unable to parse config payload for run row:', error)
      return null
    }
  }

  return rawConfig as Record<string, any>
}

const getConfigName = (row: any) => {
  const configMeta = getConfigMeta(row?.config)

  if (configMeta?.system_name) {
    return configMeta.system_name
  }

  if (configMeta?.config?.system_name) {
    return configMeta.config.system_name
  }

  if (configMeta?.name) {
    return configMeta.name
  }

  if (configMeta?.config?.name) {
    return configMeta.config.name
  }

  if (row?.config_system_name) {
    return row.config_system_name
  }

  if (row?.config_name) {
    return row.config_name
  }

  if (row?.config_id) {
    return row.config_id
  }

  return 'N/A'
}

const columns = [
  {
    name: 'status',
    label: 'Status',
    field: 'status',
    align: 'center' as const,
    sortable: true,
    type: 'component' as const,
    component: markRaw(StatusChip),
  },
  {
    name: 'config_name',
    label: 'Config',
    field: (row: any) => getConfigName(row),
    align: 'left' as const,
    sortable: true,
  },
  {
    name: 'input',
    label: 'Input',
    field: (row: any) => {
      try {
        return JSON.stringify(row.input)
      } catch {
        return String(row.input)
      }
    },
    align: 'left' as const,
    sortable: false,
    style: 'max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;',
  },
  {
    name: 'created_at',
    label: 'Created',
    field: 'created_at',
    align: 'left' as const,
    sortable: true,
    format: (val: string) => val ? date.formatDate(new Date(val), 'YYYY-MM-DD HH:mm:ss') : '-',
    sort: (a: string, b: string) => {
      const dateA = new Date(a)
      const dateB = new Date(b)
      return dateA.getTime() - dateB.getTime()
    },
  },
  {
    name: 'updated_at',
    label: 'Last Updated',
    field: 'updated_at',
    align: 'left' as const,
    sortable: true,
    format: (val: string) => val ? date.formatDate(new Date(val), 'YYYY-MM-DD HH:mm:ss') : '-',
    sort: (a: string, b: string) => {
      const dateA = new Date(a)
      const dateB = new Date(b)
      return dateA.getTime() - dateB.getTime()
    },
  },
]

const visibleColumns = computed(() => columns.map(c => c.name))

const runs = computed(() => store.getters.runs || [])

const configOptions = computed(() => {
  const configs = store.getters.configs || []
  return configs.map((c: any) => ({
    id: c.id,
    name: c.name,
  }))
})

const validateJSON = (val: string) => {
  try {
    JSON.parse(val)
    return true
  } catch (e) {
    return 'Invalid JSON'
  }
}

const onRequest = async (props: any) => {
  const { page, rowsPerPage, sortBy, descending } = props.pagination

  loading.value = true
  try {
    const result = await store.dispatch('fetchRuns', {
      page,
      pageSize: rowsPerPage,
      orderBy: sortBy || 'updated_at',
      sortOrder: descending ? 'desc' : 'asc',
    })

    // Update pagination with server response
    pagination.value.page = page
    pagination.value.rowsPerPage = rowsPerPage
    pagination.value.sortBy = sortBy
    pagination.value.descending = descending
    pagination.value.rowsNumber = result?.total || 0
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  // Only fetch if store is empty (consistent with other entities)
  if (!runs.value.length) {
    await onRequest({ pagination: pagination.value })
  } else {
    // Update pagination count from existing data
    pagination.value.rowsNumber = runs.value.length
  }
})

const refreshTable = async () => {
  await onRequest({ pagination: pagination.value })
}

const closeDialog = () => {
  showNewDialog.value = false
}

const createRun = async () => {
  try {

    if (!selectedConfigId.value) {
      $q.notify({
        position: 'top',
        message: 'Please select a config',
        color: 'positive',
        textColor: 'black',
        timeout: 1000,
      })
      return
    }

    // Validate JSON
    let inputPayload
    try {
      inputPayload = JSON.parse(runInput.value)
    } catch (e) {
      $q.notify({
        position: 'top',
        message: 'Invalid JSON input',
        color: 'positive',
        textColor: 'black',
        timeout: 1000,
      })
      return
    }

    creating.value = true

    // Get the selected config
    const selectedConfig = configOptions.value.find(c => c.id === selectedConfigId.value)
    if (!selectedConfig) {
      throw new Error('Selected config not found')
    }

    // Get full config details
    const configs = store.getters.configs || []
    const fullConfig = configs.find((c: any) => c.id === selectedConfigId.value)

    const result = await store.dispatch('createRun', {
      config: fullConfig?.config || {},
      input: inputPayload,
      client_id: runClientId.value || undefined,
      config_system_name: fullConfig?.system_name,
    })

    $q.notify({
      position: 'top',
      message: 'Run has been created',
      color: 'positive',
      textColor: 'black',
      timeout: 1000,
    })

    showNewDialog.value = false

    // Reset form
    selectedConfigId.value = null
    runInput.value = '{"query": ""}'
    runClientId.value = ''

    // Navigate to the new run
    if (result?.id) {
      router.push(`/deep-research/runs/${result.id}`)
    } else {
      // Refresh the list if navigation fails
      await refreshTable()
    }
  } catch (error: any) {
    console.error('Error creating run:', error)
    $q.notify({
      position: 'top',
      message: error?.message || 'Failed to create run',
      color: 'positive',
      textColor: 'black',
      timeout: 1000,
    })
  } finally {
    creating.value = false
  }
}

const openDetails = (row: any) => {
  router.push(`/deep-research/runs/${row.id}`)
}
</script>

<style lang="stylus">
.collection-container {
  min-width: 450px;
  max-width: 1200px;
  width: 100%;
}
.km-input:not(.q-field--readonly) .q-field__control::before {
  background: #fff !important;
}
</style>
