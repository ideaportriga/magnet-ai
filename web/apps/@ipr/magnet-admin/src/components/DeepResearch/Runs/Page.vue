<template lang="pug">
.column.no-wrap.full-height
  .collection-container.q-mx-auto.full-width.column.full-height.q-px-md.q-pt-16
    .col.ba-border.border-radius-12.bg-white.q-pa-16.column(style='min-height: 0')
      .row.q-mb-12
        q-space
        .col-auto.center-flex-y
          km-btn.q-mr-12(
            icon='refresh',
            :label='m.common_refreshList()',
            @click='refreshTable',
            iconColor='icon',
            hoverColor='primary',
            labelClass='km-title',
            flat,
            iconSize='16px',
            hoverBg='primary-bg'
          )
          km-btn(
            :label='m.common_new()',
            @click='showNewDialog = true'
          )
      .col(style='min-height: 0')
        km-data-table(
          fill-height,
          :table='table',
          :loading='loading',
          row-key='id',
          dense,
          @row-click='openDetails'
        )
        km-inner-loading(:showing='loading')

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
    km-btn(flat, :label='m.common_cancel()', color='primary', @click='closeDialog')
    km-btn(:label='m.common_createRun()', :loading='creating', @click='createRun')
</template>

<script setup lang="ts">
import { ref, computed, onMounted, markRaw, watch } from 'vue'
import { m } from '@/paraglide/messages'
import { useRouter } from 'vue-router'
import { date } from 'quasar'
import StatusChip from './StatusChip.vue'
import { useDeepResearchStore } from '@/stores/deepResearchStore'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
import { textColumn, componentColumn } from '@/utils/columnHelpers'
import { useNotify } from '@/composables/useNotify'

const drStore = useDeepResearchStore()
const router = useRouter()
const { notifySuccess, notifyError } = useNotify()

const loading = ref(false)
const showNewDialog = ref(false)
const creating = ref(false)
const selectedConfigId = ref<string | null>(null)
const runInput = ref('{"task": ""}')
const runClientId = ref('')

const getConfigMeta = (rawConfig: unknown) => {
  if (!rawConfig) {
    return null
  }

  if (typeof rawConfig === 'string') {
    try {
      return JSON.parse(rawConfig)
    } catch (error) {
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
  componentColumn('status', 'Status', markRaw(StatusChip), {
    accessorKey: 'status',
    sortable: true,
    align: 'center',
  }),
  textColumn('config_name', 'Config', {
    sortable: true,
    format: (val: unknown) => String(val ?? 'N/A'),
  }),
  textColumn('input', 'Input', {
    sortable: false,
    format: (val: unknown) => {
      try {
        return typeof val === 'string' ? val : JSON.stringify(val)
      } catch {
        return String(val)
      }
    },
  }),
  textColumn('created_at', m.common_created(), {
    sortable: true,
    format: (val: unknown) => val ? date.formatDate(new Date(val as string), 'YYYY-MM-DD HH:mm:ss') : '-',
  }),
  textColumn('updated_at', m.common_lastUpdated(), {
    sortable: true,
    format: (val: unknown) => val ? date.formatDate(new Date(val as string), 'YYYY-MM-DD HH:mm:ss') : '-',
  }),
]

// Map runs to include config_name for the text column
const runs = computed(() => {
  const rawRuns = drStore.runs || []
  return rawRuns.map((r: any) => ({
    ...r,
    config_name: getConfigName(r),
  }))
})

const { table, sorting } = useLocalDataTable(runs, columns, {
  defaultSort: [{ id: 'updated_at', desc: true }],
  defaultPageSize: 15,
})

const configOptions = computed(() => {
  const configs = drStore.configs || []
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

const fetchRuns = async () => {
  loading.value = true
  try {
    const sort = sorting.value?.[0]
    await drStore.fetchRuns({
      page: 1,
      pageSize: 100,
      orderBy: sort?.id || 'updated_at',
      sortOrder: sort?.desc ? 'desc' : 'asc',
    })
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  drStore.fetchConfigs()
  if (!runs.value.length) {
    await fetchRuns()
  }
})

const refreshTable = async () => {
  await fetchRuns()
}

const closeDialog = () => {
  showNewDialog.value = false
}

const createRun = async () => {
  try {

    if (!selectedConfigId.value) {
      notifyError('Please select a config')
      return
    }

    // Validate JSON
    let inputPayload
    try {
      inputPayload = JSON.parse(runInput.value)
    } catch (e) {
      notifyError('Invalid JSON input')
      return
    }

    creating.value = true

    // Get the selected config
    const selectedConfig = configOptions.value.find(c => c.id === selectedConfigId.value)
    if (!selectedConfig) {
      throw new Error('Selected config not found')
    }

    // Get full config details
    const configs = drStore.configs || []
    const fullConfig = configs.find((c: any) => c.id === selectedConfigId.value)

    const result = await drStore.createRun({
      config: fullConfig?.config || {},
      input: inputPayload,
      client_id: runClientId.value || undefined,
      config_system_name: fullConfig?.system_name,
    })

    notifySuccess('Run has been created')

    showNewDialog.value = false

    // Reset form
    selectedConfigId.value = null
    runInput.value = '{"task": ""}'
    runClientId.value = ''

    // Navigate to the new run
    if (result?.id) {
      router.push(`/deep-research/runs/${result.id}`)
    } else {
      // Refresh the list if navigation fails
      await refreshTable()
    }
  } catch (error: any) {
    notifyError(error?.message || 'Failed to create run')
  } finally {
    creating.value = false
  }
}

const openDetails = (row: any) => {
  router.push(`/deep-research/runs/${row.id}`)
}
</script>

<style lang="stylus">
.km-input:not(.q-field--readonly) .q-field__control::before {
  background: #fff !important;
}
</style>
