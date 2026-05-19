<template>
  <km-list-page>
    <template #toolbar>
      <div class="km-space" />
      <div class="flex-none center-flex-y">
        <km-btn class="mr-md" icon="refresh" :label="m.common_refreshList()" interaction-tone="brand" label-class="km-title" flat icon-size="16px" @click="refreshTable" />
        <km-btn v-if="canCreate" :label="m.common_new()" @click="showNewDialog = true" />
      </div>
    </template>
    <div class="flex-1" style="min-block-size: 0">
      <km-data-table fill-height :table="table" :loading="loading" row-key="id" dense @row-click="openDetails" />
      <km-inner-loading :showing="loading" />
    </div>
    <template #overlays>
      <km-dialog :model-value="showNewDialog" @update:model-value="showNewDialog = $event">
        <km-card style="min-inline-size: 600px">
          <div class="km-card-section">
            <div class="text-h6">Create New Run</div>
          </div>
          <div class="km-card-section pt-0">
            <form class="km-form" @submit.prevent="createRun">
              <div class="km-field mb-md" />
            </form>
          </div>
        </km-card>
        <div class="text-secondary-text pb-xs">Config</div>
        <km-select v-model="selectedConfigId" :options="configOptions" option-value="id" option-label="name" emit-value map-options height="30px" :placeholder="m.deepResearch_selectConfig()" :rules="[val => !!val || 'Config is required']" />
        <div class="km-description text-secondary-text pt-2xs">
          Select the research configuration to use
          <div class="km-field mb-md" />
        </div>
        <div class="text-secondary-text pb-xs">Input (JSON)</div>
        <km-input v-model="runInput" type="textarea" outlined rows="8" :rules="[validateJSON]" :placeholder="m.deepResearch_exampleQuery()" />
        <div class="km-description text-secondary-text pt-2xs">
          Provide the input data for the research run
          <div class="km-field mb-md" />
        </div>
        <div class="text-secondary-text pb-xs">Client ID (optional)</div>
        <km-input v-model="runClientId" height="30px" :placeholder="m.deepResearch_optionalClientIdentifier()">
          <div class="km-card-actions" align="right" />
        </km-input>
        <km-btn flat :label="m.common_cancel()" tone="brand" @click="closeDialog" />
        <km-btn :label="m.common_createRun()" :loading="creating" @click="createRun" />
      </km-dialog>
    </template>
  </km-list-page>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, markRaw, watch } from 'vue'
import { m } from '@/paraglide/messages'
import { useRouter } from 'vue-router'
import { DateTime } from 'luxon'
import StatusChip from './StatusChip.vue'
import { useDeepResearchStore } from '@/stores/deepResearchStore'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
import { textColumn, componentColumn } from '@/utils/columnHelpers'
import { useNotify } from '@/composables/useNotify'
import { useEntityAccess } from '@/composables/useEntityAccess'

const drStore = useDeepResearchStore()
const router = useRouter()
const { notifySuccess, notifyError } = useNotify()
const { canCreate } = useEntityAccess('deep_research')

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
    format: (val: unknown) => val ? DateTime.fromJSDate(new Date(val as string)).toFormat('yyyy-MM-dd HH:mm:ss') : '-',
  }),
  textColumn('updated_at', m.common_lastUpdated(), {
    sortable: true,
    format: (val: unknown) => val ? DateTime.fromJSDate(new Date(val as string)).toFormat('yyyy-MM-dd HH:mm:ss') : '-',
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
