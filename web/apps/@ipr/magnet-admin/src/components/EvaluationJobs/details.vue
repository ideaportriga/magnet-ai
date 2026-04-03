<template lang="pug">
.row.no-wrap.overflow-hidden.full-height(v-if='loading', style='min-width: 1200px')
  km-inner-loading(:showing='loading')
layouts-details-layout.q-mx-auto(v-else, :style='{ "max-width": openDrawer ? "none" : "1200px" }')
  template(#header)
    .row.items-center.justify-between.full-width
      .km-heading-7 {{ evaluation_name }}
      .row.q-gap-16
        km-chip(:color='statusStyles.color', round)
          .km-small-chip.text-capitalize(:class='`text-${statusStyles.textColor}`') {{ evaluation.status }}
        km-chip(color='in-progress', round)
          .km-small-chip.text-text-grey {{ typeLabel }}
    .km-description.text-secondary-text.q-pt-8 {{ formattedDate }}
    .km-grid.q-mt-16
      .column.ba-border.border-radius-12.q-pa-16.no-wrap.fit
        .km-heading-4.text-placeholder Avg. score
        .row
          km-chip(:color='color', :text-color='textColor', round, size='27px')
            .km-chart-value.q-pa-xs(:class='`text-${textColor}`') {{ averageScore }}
      .column.ba-border.border-radius-12.q-pa-16.no-wrap.fit
        .km-heading-4.text-placeholder Records rated
        .km-chart-value {{ recordsRated }}
      .column.ba-border.border-radius-12.q-pa-16.no-wrap.fit
        .km-heading-4.text-placeholder Avg. total cost
        .km-chart-value {{ totalCost }}
      .column.ba-border.border-radius-12.q-pa-16.no-wrap.fit
        .km-heading-4.text-placeholder Avg. latency
        .km-chart-value {{ latency }}
  template(#content)
    q-tabs.bb-border(
      v-model='tab',
      narrow-indicator,
      dense,
      align='left',
      active-color='primary',
      indicator-color='primary',
      no-caps,
      content-class='km-tabs'
    )
      template(v-for='t in tabs')
        q-tab(:name='t.name', :label='t.label')
    .column.full-height.full-width.q-pt-16(style='min-height: 0')
      template(v-if='tab == "records"')
        .col(style='min-height: 0')
          evaluation-jobs-records(@record:update='evaluationSetRecord')
      template(v-if='tab == "settings"')
        .col.overflow-auto
          template(v-if='evaluationType == "prompt_eval"')
            evaluation-jobs-settings
          template(v-else)
            evaluation-jobs-settings-rag
  template(#drawer)
    evaluation-jobs-drawer(v-if='openDrawer', :open='openDrawer')
configuration-create-new(v-if='showNewDialog', :showNewDialog='showNewDialog', @cancel='showNewDialog = false', copy)
</template>

<script setup>
import { ref, computed, watch, onMounted, onActivated } from 'vue'
import { m } from '@/paraglide/messages'
import { useRoute, useRouter } from 'vue-router'
import { useEntityQueries } from '@/queries/entities'
import { useEvaluationStore } from '@/stores/evaluationStore'
import { useNotify } from '@/composables/useNotify'

// Define emits
const emit = defineEmits(['update:closeDrawer'])

// Composables
const route = useRoute()
const router = useRouter()
const evalStore = useEvaluationStore()
const { notifyError, notifySuccess } = useNotify()

// Queries
const queries = useEntityQueries()
const id = ref(route.params.id)
const { data: selectedRow } = queries.evaluation_jobs.useDetail(id)
const { data: evalJobsData } = queries.evaluation_jobs.useList()
const { data: modelData } = queries.model.useList()
const evalJobsItems = computed(() => evalJobsData.value?.items ?? [])
const modelItems = computed(() => modelData.value?.items ?? [])
const removeMutation = queries.evaluation_jobs.useRemove()

// Reactive data
const tab = ref('records')
const tabs = ref([
  { name: 'records', label: 'Records' },
  { name: 'settings', label: 'Variant details' },
])
const showNewDialog = ref(false)
const activeEvaluationSet = ref({})
const prompt = ref(null)
const showInfo = ref(false)
const evaluationSetRecord = ref({})
const loading = ref(false)

// Computed properties
const latency = computed(() => {
  const result = row.value?.average_latency || 0
  return new Intl.NumberFormat(undefined, {
    style: 'unit',
    unit: 'millisecond',
    unitDisplay: 'short',
    maximumFractionDigits: 0,
  }).format(result)
})

const row = computed(() => {
  const rowData = (evalJobsItems.value || []).find((item) => item._id == evaluation.value.id)
  return rowData || {}
})

const model = computed(() => {
  return modelItems.value?.find((model) => model.system_name === modelSystemName.value) || {}
})

const modelSystemName = computed(() => {
  return row.value?.tool?.variant_object?.system_name_for_model || ''
})

const priceInput = computed(() => {
  return model.value?.price_input || 0
})

const priceOutput = computed(() => {
  return model.value?.price_output || 0
})

const priceCached = computed(() => {
  return model.value?.price_cached || 0
})

const inputTokens = computed(() => {
  return row.value?.average_prompt_tokens || 0
})

const outputTokens = computed(() => {
  return row.value?.average_completion_tokens || 0
})

const cachedTokens = computed(() => {
  return row.value?.average_cached_tokens || 0
})

const roundedInputTokens = computed(() => {
  return Math.round(inputTokens.value)
})

const roundedOutputTokens = computed(() => {
  return Math.round(outputTokens.value)
})

const roundedCachedTokens = computed(() => {
  return Math.round(cachedTokens.value)
})

const inputCost = computed(() => {
  const result = (inputTokens.value * priceInput.value) / 1000000
  return parseFloat(result.toPrecision(2))
})

const outputCost = computed(() => {
  const result = (outputTokens.value * priceOutput.value) / 1000000
  return parseFloat(result.toPrecision(2))
})

const cachedCost = computed(() => {
  const result = (cachedTokens.value * priceCached.value) / 1000000
  return parseFloat(result.toPrecision(2))
})

const totalTokens = computed(() => {
  return roundedInputTokens.value + roundedOutputTokens.value + roundedCachedTokens.value
})

const totalCost = computed(() => {
  const result = inputCost.value + outputCost.value + cachedCost.value
  const resusltFloat = parseFloat(result.toPrecision(2))
  return `$${resusltFloat}`
})

const formattedDate = computed(() => {
  const date = new Date(evaluation.value?.started_at)
  const day = String(date.getDate()).padStart(2, '0')
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const year = date.getFullYear()
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')

  return `${day}.${month}.${year} ${hours}:${minutes}`
})

const averageScore = computed(() => {
  if (!results.value || results.value.length === 0) {
    return 0
  }
  const filteredResults = results.value.filter((item) => item.score > 0)
  if (filteredResults.length === 0) {
    return 0
  }
  const totalScore = filteredResults.reduce((sum, item) => sum + item.score, 0)
  return totalScore / filteredResults.length
})

const recordsRated = computed(() => {
  const recordsRatedCount = (results.value || []).filter((item) => item.score > 0)?.length
  return `${recordsRatedCount} of ${results.value?.length} `
})

const results = computed(() => {
  return evaluation.value?.results || []
})

const evaluation_name = computed(() => {
  return evaluation.value?.tool?.name || ''
})

const evaluation = computed(() => {
  return evalStore.evaluation
})

const evaluationType = computed(() => {
  return evaluation.value?.type || ''
})

const typeLabel = computed(() => {
  if (evaluation.value?.type === 'prompt_eval') {
    return 'Prompt Template'
  }
  return 'RAG'
})

const openDrawer = computed(() => {
  return tab.value === 'records' && Object.keys(evalStore.evaluationJobRecord).length > 0
})


const color = computed(() => {
  return statusStyles.value?.color || ''
})

const textColor = computed(() => {
  return statusStyles.value?.textColor || ''
})

const statusStyles = computed(() => {
  if (evaluation.value?.status === 'in_progress') {
    return { color: 'in-progress', textColor: 'text-gray' }
  }
  return { color: 'status-ready', textColor: 'status-ready-text' }
})

// Methods
const getEvaluation = async () => {
  loading.value = true
  await evalStore.getEvaluation({ id: route.params.id })
  loading.value = false
}

const navigate = (path = '') => {
  if (route.path !== `/${path}`) {
    router.push(`${path}`)
  }
}

const deleteEvaluationSet = () => {
  notifyError(`Are you sure you want to delete ${selectedRow.value?.name}?`)
  removeMutation.mutate(selectedRow.value?.id)
  emit('update:closeDrawer', null)
  notifySuccess('RAG Tool has been deleted.')
  navigate('/evaluation_set-tools')
}

// Lifecycle
onMounted(() => {
  getEvaluation()
})

onActivated(() => {
  id.value = route.params.id
  // Re-sync Vuex state when KeepAlive reactivates this component (multi-tab support)
  if (route.params.id && route.params.id !== evalStore.evaluation?.id) {
    getEvaluation()
  }
})
</script>
<style lang="scss">
@keyframes wobble {
  0% {
    transform: rotate(-5deg);
  }
  50% {
    transform: rotate(5deg);
  }
  100% {
    transform: rotate(-5deg);
  }
}

.wobble {
  animation: wobble 2s infinite;
}

.grid-container {
  display: grid;
  grid-template-columns: 0.5fr 1fr 0.5fr 1fr;
  grid-template-rows: repeat(2, auto);
  gap: 2px;
  justify-items: center;
  align-items: baseline;
  white-space: nowrap;
}

.grid-item-left {
  justify-self: start;
  margin-left: 8px;
}

.grid-item {
  justify-self: end;
  margin-left: 12px;
}
</style>
