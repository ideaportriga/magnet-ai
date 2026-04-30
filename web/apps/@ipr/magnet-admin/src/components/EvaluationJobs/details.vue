<template>
  <div v-if="loading" class="cluster overflow-hidden full-height" data-wrap="no" style="min-inline-size: 1200px">
    <km-inner-loading :showing="loading" />
  </div>
  <layouts-details-layout v-else class="mx-auto" :style="{ &quot;max-width&quot;: openDrawer ? &quot;none&quot; : &quot;1200px&quot; }">
    <template #header>
      <div class="cluster full-width" data-justify="between">
        <div class="km-heading-7">{{ evaluation_name }}</div>
        <div class="cluster" data-gap="lg">
          <km-chip :tone="statusTone" round>
            <div class="km-small-chip text-capitalize">{{ evaluation.status }}</div>
          </km-chip>
          <km-chip tone="neutral" round>
            <div class="km-small-chip text-text-grey">{{ typeLabel }}</div>
          </km-chip>
        </div>
      </div>
      <div class="km-description text-secondary-text pt-sm">{{ formattedDate }}</div>
      <div class="km-grid mt-lg">
        <div class="stack ba-border border-radius-12 p-lg fit" data-gap="0">
          <div class="km-heading-4 text-placeholder">{{ m.evaluation_avgScore() }}</div>
          <div class="cluster">
            <km-chip :tone="statusTone" round size="27px">
              <div class="km-chart-value p-xs">{{ averageScore }}</div>
            </km-chip>
          </div>
        </div>
        <div class="stack ba-border border-radius-12 p-lg fit" data-gap="0">
          <div class="km-heading-4 text-placeholder">{{ m.evaluation_recordsRated() }}</div>
          <div class="km-chart-value">{{ recordsRated }}</div>
        </div>
        <div class="stack ba-border border-radius-12 p-lg fit" data-gap="0">
          <div class="km-heading-4 text-placeholder">{{ m.evaluation_avgTotalCost() }}</div>
          <div class="km-chart-value">{{ totalCost }}</div>
        </div>
        <div class="stack ba-border border-radius-12 p-lg fit" data-gap="0">
          <div class="km-heading-4 text-placeholder">{{ m.evaluation_avgLatency() }}</div>
          <div class="km-chart-value">{{ latency }}</div>
        </div>
      </div>
    </template>
    <template #content>
      <km-tabs v-model="tab" class="bb-border" narrow-indicator dense align="left" no-caps content-class="km-tabs">
        <template v-for="t in tabs" :key="t">
          <km-tab :name="t.name" :label="t.label" />
        </template>
      </km-tabs>
      <div class="stack full-height full-width pt-lg" data-gap="0" style="min-block-size: 0">
        <template v-if="tab == &quot;records&quot;">
          <div class="flex-1" style="min-block-size: 0">
            <evaluation-jobs-records />
          </div>
        </template>
        <template v-if="tab == &quot;settings&quot;">
          <div class="flex-1 overflow-auto">
            <template v-if="evaluationType == &quot;prompt_eval&quot;">
              <evaluation-jobs-settings />
            </template>
            <template v-else>
              <evaluation-jobs-settings-rag />
            </template>
          </div>
        </template>
      </div>
    </template>
    <template #drawer>
      <evaluation-jobs-drawer v-if="openDrawer" :open="openDrawer" />
    </template>
  </layouts-details-layout>
  <rag-create-new v-if="showNewDialog" :show-new-dialog="showNewDialog" copy @cancel="showNewDialog = false" />
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
  { name: 'records', label: m.common_records() },
  { name: 'settings', label: m.evaluation_variantDetails() },
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
    return m.entity_promptTemplate()
  }
  return m.entity_ragTool()
})

const openDrawer = computed(() => {
  return tab.value === 'records' && Object.keys(evalStore.evaluationJobRecord).length > 0
})

const statusTone = computed(() => {
  if (evaluation.value?.status === 'in_progress') {
    return 'neutral'
  }
  return 'success'
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
  notifyError(m.evaluation_deleteNamedConfirm({ name: selectedRow.value?.name || '' }))
  removeMutation.mutate(selectedRow.value?.id)
  emit('update:closeDrawer', null)
  notifySuccess(m.notify_entityDeleted({ entity: m.entity_ragTool() }))
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

.wobble {
  animation: ds-attention-wobble var(--ds-duration-attention) infinite;
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
