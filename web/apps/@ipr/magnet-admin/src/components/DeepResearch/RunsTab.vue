<template lang="pug">
.column.q-gap-16
  .row.items-center.justify-between
    .km-heading-5.text-black Research Runs
    .row.q-gap-8
      q-btn(
        flat,
        dense,
        icon='refresh',
        color='primary',
        @click='refreshRuns'
      )
        q-tooltip Refresh
      q-btn.km-btn(
        label='New Run',
        icon='add',
        color='primary',
        unelevated,
        @click='showCreateRunDialog = true'
      )

  q-card.q-pa-md(v-if='loading')
    q-inner-loading(:showing='loading')
      q-spinner(color='primary', size='50px')

  .column.q-gap-12(v-else-if='runs.length > 0')
    q-card.q-pa-md(
      v-for='run in runs',
      :key='run.id',
      :class='getRunCardClass(run.status)'
    )
      .row.items-center.justify-between
        .column.col
          .row.items-center.q-gap-8
            .km-title.text-black Run {{ run.id.slice(0, 8) }}
            q-badge(
              :color='getStatusColor(run.status)',
              :label='run.status.toUpperCase()'
            )
          .km-description.text-secondary.q-mt-xs Created: {{ formatDate(run.created_at) }}
          .km-description.text-secondary(v-if='run.client_id') Client ID: {{ run.client_id }}
        .row.q-gap-8
          q-btn(
            flat,
            dense,
            icon='visibility',
            color='primary',
            @click='viewRunDetails(run)'
          )
            q-tooltip View Details
          q-btn(
            flat,
            dense,
            icon='refresh',
            color='primary',
            @click='refreshSingleRun(run.id)',
            v-if='run.status === "pending" || run.status === "running"'
          )
            q-tooltip Refresh Status

      q-linear-progress(
        v-if='run.status === "running" || run.status === "pending"',
        indeterminate,
        color='primary',
        class='q-mt-md'
      )

      .q-mt-md(v-if='run.status === "failed" && run.error')
        .km-description.text-negative Error: {{ run.error }}

      .q-mt-md(v-if='run.status === "completed"')
        .km-description.text-positive.q-mb-xs Research completed with {{ run.steps?.length || 0 }} steps
        .km-description.text-secondary.q-mb-xs Query: {{ run.input?.query ?? "—" }}
        .km-description.text-secondary(v-if='run.result') Result keys: {{ Object.keys(run.result).join(', ') }}

  q-card.q-pa-md(v-else)
    .text-center.text-secondary No runs found

// Create Run Dialog
q-dialog(v-model='showCreateRunDialog')
  q-card(style='min-width: 600px')
    q-card-section
      .text-h6 Create Research Run

    q-card-section.q-pt-none
      q-form(@submit.prevent='createRun')
        .text-subtitle2.q-mb-sm Select Config (optional)
        q-select.q-mb-md(
          v-model='selectedConfig',
          :options='configOptions',
          option-value='id',
          option-label='name',
          outlined,
          dense,
          clearable,
          emit-value,
          map-options,
          label='Config'
        )

        q-separator.q-my-md

        .text-subtitle2.q-mb-md Input Data (JSON)
        q-input.q-mb-md(
          v-model='newRunInput',
          type='textarea',
          outlined,
          dense,
          rows='8',
          :rules='[validateJSON]'
          placeholder='{"query": "Research question here", "context": "Additional context..."}'
        )

        q-input.q-mb-md(
          v-model='newRunClientId',
          label='Client ID (optional)',
          outlined,
          dense,
        )

        q-card-actions(align='right')
          q-btn(flat, label='Cancel', color='grey', v-close-popup)
          q-btn(type='submit', label='Create', color='primary', unelevated, :loading='creating')

// Run Details Dialog
deep-research-run-details-dialog(
  v-model='showDetailsDialog',
  :run='selectedRunForDetails'
)
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useStore } from 'vuex'
import { Notify } from 'quasar'
import { date } from 'quasar'
import DeepResearchRunDetailsDialog from './RunDetailsDialog.vue'

const store = useStore()

const showCreateRunDialog = ref(false)
const showDetailsDialog = ref(false)
const creating = ref(false)
const selectedConfig = ref<string | null>(null)
const newRunInput = ref('{"query": ""}')
const newRunClientId = ref('')
const selectedRunForDetails = ref<any>(null)

// Auto-refresh interval
let refreshInterval: any = null

const runs = computed(() => store.getters.runs || [])
const configs = computed(() => store.getters.configs || [])
const loading = computed(() => store.getters.loading)

const configOptions = computed(() => {
  return configs.value.map((c: any) => ({
    id: c.id,
    name: c.name,
  }))
})

const ensureConfigsLoaded = async () => {
  if (!store.getters.configs?.length) {
    try {
      await store.dispatch('fetchConfigs')
    } catch (error) {
      console.error('Failed to load configs:', error)
    }
  }
}

const validateJSON = (val: string) => {
  try {
    JSON.parse(val)
    return true
  } catch (e) {
    return 'Invalid JSON'
  }
}

const formatDate = (dateStr: string) => {
  return date.formatDate(new Date(dateStr), 'YYYY-MM-DD HH:mm:ss')
}

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    pending: 'orange',
    running: 'blue',
    completed: 'green',
    failed: 'red',
  }
  return colors[status] || 'grey'
}

const getRunCardClass = (status: string) => {
  if (status === 'failed') return 'bg-red-1'
  if (status === 'completed') return 'bg-green-1'
  return ''
}

const refreshRuns = async () => {
  await store.dispatch('fetchRuns')
}

const refreshSingleRun = async (runId: string) => {
  await store.dispatch('fetchRun', runId)
  await store.dispatch('fetchRuns')
}

const createRun = async () => {
  try {
    creating.value = true

    await ensureConfigsLoaded()

    const inputData = JSON.parse(newRunInput.value)

    if (selectedConfig.value) {
      // Create run from config
      const configData = configs.value.find((c: any) => c.id === selectedConfig.value)
      if (configData) {
        await store.dispatch('createRunFromConfig', {
          configId: selectedConfig.value,
          input: inputData,
          client_id: newRunClientId.value || undefined,
        })
      }
    } else {
      // Create run with default config
      await store.dispatch('createRun', {
        input: inputData,
        client_id: newRunClientId.value || undefined,
      })
    }

    Notify.create({
      type: 'positive',
      message: 'Run created successfully',
    })

    showCreateRunDialog.value = false

    // Reset form
    selectedConfig.value = null
    newRunInput.value = '{"query": ""}'
    newRunClientId.value = ''
  } catch (error: any) {
    Notify.create({
      type: 'negative',
      message: error?.message || 'Failed to create run',
    })
  } finally {
    creating.value = false
  }
}

const viewRunDetails = (run: any) => {
  selectedRunForDetails.value = run
  showDetailsDialog.value = true
}

watch(showCreateRunDialog, (value) => {
  if (value) {
    ensureConfigsLoaded()
  }
})

// Setup auto-refresh for active runs
onMounted(() => {
  refreshInterval = setInterval(() => {
    const hasActiveRuns = runs.value.some(
      (r: any) => r.status === 'pending' || r.status === 'running'
    )
    if (hasActiveRuns) {
      refreshRuns()
    }
  }, 5000) // Refresh every 5 seconds
})

onBeforeUnmount(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>

<style scoped lang="scss">
.km-btn {
  text-transform: none;
}
</style>
