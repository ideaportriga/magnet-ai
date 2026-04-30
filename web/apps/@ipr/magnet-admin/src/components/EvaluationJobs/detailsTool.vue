<template>
  <div v-if="loading" class="cluster overflow-hidden full-height" data-wrap="no" style="min-inline-size: 1200px">
    <km-inner-loading :showing="loading" />
  </div>
  <div v-else class="cluster overflow-hidden full-height" data-wrap="no" style="min-inline-size: 1200px">
    <div class="flex-1 flex full-height fit" style="justify-content: center; flex-wrap: nowrap">
      <div class="flex-1" style="max-inline-size: 1200px; min-inline-size: 600px">
        <div class="full-height pb-md relative-position px-md">
          <div class="cluster full-width mt-lg mb-sm" data-gap="md" data-wrap="no">
            <div class="flex-1">
              <div class="cluster">
                <div class="km-heading-7 full-width">{{ evaluation_name }}</div>
                <div class="cluster">
                  <div class="km-heading-2 text-secondary full-width">{{ formattedDate }}</div>
                </div>
              </div>
            </div>
            <div class="flex-none">
              <div class="grid-container ba-border bg-white border-radius-12 py-xs pr-md">
                <div class="grid-item">
                  <km-score :score="averageScore || m.evaluation_notRated()" />
                </div>
                <div class="grid-item-left km-label">{{ m.evaluation_avgScore() }}</div>
                <div class="grid-item km-chip text-text-gray">{{ recordsRated }}</div>
                <div class="grid-item-left km-label">{{ m.evaluation_recordsRated() }}</div>
                <div v-if="evaluationType == &quot;prompt_eval&quot;" class="grid-item">
                  <km-chip class="km-chip" tone="neutral" :label="totalCost" />
                </div>
                <div v-if="evaluationType == &quot;prompt_eval&quot;" class="grid-item-left km-label">{{ m.evaluation_avgTotalCost() }}</div>
                <div class="grid-item km-chip text-text-gray">{{ latency }}</div>
                <div class="grid-item-left km-label">{{ m.evaluation_avgLatency() }}</div>
              </div>
            </div>
          </div>
          <km-tabs v-model="tab" narrow-indicator dense align="left" no-caps content-class="km-tabs">
            <template v-for="t in tabs" :key="t">
              <km-tab :name="t.name" :label="t.label" />
            </template>
          </km-tabs>
          <div class="stack full-height full-width overflow-hidden my-md" data-gap="lg" style="block-size: calc(100vb - 256px) !important">
            <div class="cluster full-height full-width" data-gap="lg">
              <div class="flex-1 full-height full-width">
                <div class="stack items-center full-height full-width overflow-auto" data-gap="lg">
                  <template v-if="true">
                    <div class="full-width">
                      <template v-if="tab == &quot;records&quot;">
                        <evaluation-jobs-records />
                      </template>
                      <template v-if="tab == &quot;settings&quot;">
                        <template v-if="evaluationType == &quot;prompt_eval&quot;">
                          <evaluation-jobs-settings />
                        </template>
                        <template v-else>
                          <evaluation-jobs-settings-rag />
                        </template>
                      </template>
                    </div>
                  </template>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="flex-none">
      <evaluation-jobs-drawer v-if="openDrawer" :open="openDrawer" />
    </div>
    <rag-create-new v-if="showNewDialog" :show-new-dialog="showNewDialog" copy @cancel="showNewDialog = false" />
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { m } from '@/paraglide/messages'
import { useRoute } from 'vue-router'
import { useEntityQueries } from '@/queries/entities'
import { useEvaluationStore } from '@/stores/evaluationStore'

export default {
  emits: ['update:closeDrawer'],
  setup() {
    const route = useRoute()
    const queries = useEntityQueries()
    const evalStore = useEvaluationStore()
    const routeId = computed(() => route.params.id)
    const { data: selectedRow } = queries.evaluation_jobs.useDetail(routeId)
    const { data: evalJobsData } = queries.evaluation_jobs.useList()
    const { data: modelData } = queries.model.useList()
    const evalJobsItems = computed(() => evalJobsData.value?.items ?? [])
    const modelItems = computed(() => modelData.value?.items ?? [])
    const { mutateAsync: removeEvaluationJob } = queries.evaluation_jobs.useRemove()

    return {
      m,
      evalStore,
      tab: ref('records'),
      tabs: ref([
        { name: 'records', label: m.common_records() },
        { name: 'settings', label: m.evaluation_variantDetails() },
      ]),
      showNewDialog: ref(false),
      activeEvaluationSet: ref({}),
      prompt: ref(null),
      showInfo: ref(false),
      selectedRow,
      removeEvaluationJob,
      evaluationSetRecord: ref({}),
      loadingChroma: ref(false),
      loading: ref(false),
      evalJobsItems,
      modelItems,
    }
  },
  computed: {
    latency() {
      const result = this.row?.average_latency || 0
      return new Intl.NumberFormat(undefined, {
        style: 'unit',
        unit: 'millisecond',
        unitDisplay: 'short',
        maximumFractionDigits: 0,
      }).format(result)
    },

    row() {
      const row = (this.evalJobsItems || []).find((item) => item._id == this.evaluation.id)
      return row || {}
    },
    model() {
      return this.modelItems?.find((model) => model.system_name === this.modelSystemName) || {}
    },
    modelSystemName() {
      return this.row?.tool?.variant_object?.system_name_for_model || ''
    },
    priceInput() {
      return this.model?.price_input || 0
    },
    priceOutput() {
      return this.model?.price_output || 0
    },
    priceCached() {
      return this.model?.price_cached || 0
    },

    inputTokens() {
      return this.row?.average_prompt_tokens || 0
    },
    outputTokens() {
      return this.row?.average_completion_tokens || 0
    },
    cachedTokens() {
      return this.row?.average_cached_tokens || 0
    },
    roundedInputTokens() {
      return Math.round(this.inputTokens)
    },
    roundedOutputTokens() {
      return Math.round(this.outputTokens)
    },
    roundedCachedTokens() {
      return Math.round(this.cachedTokens)
    },
    inputCost() {
      const result = (this.inputTokens * this.priceInput) / 1000000
      return parseFloat(result.toPrecision(2))
    },
    outputCost() {
      const result = (this.outputTokens * this.priceOutput) / 1000000
      return parseFloat(result.toPrecision(2))
    },
    cachedCost() {
      const result = (this.cachedTokens * this.priceCached) / 1000000
      return parseFloat(result.toPrecision(2))
    },
    totalTokens() {
      return this.roundedInputTokens + this.roundedOutputTokens + this.roundedCachedTokens
    },
    totalCost() {
      const result = this.inputCost + this.outputCost + this.cachedCost
      const resusltFloat = parseFloat(result.toPrecision(2))
      return `$${resusltFloat}`
    },
    formattedDate() {
      const date = new Date(this.evaluation?.started_at)
      const day = String(date.getDate()).padStart(2, '0')
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const year = date.getFullYear()
      const hours = String(date.getHours()).padStart(2, '0')
      const minutes = String(date.getMinutes()).padStart(2, '0')

      return `${day}.${month}.${year} ${hours}:${minutes}`
    },
    averageScore() {
      if (!this.results || this.results.length === 0) {
        return 0
      }
      const filteredResults = this.results.filter((item) => item.score > 0)
      if (filteredResults.length === 0) {
        return 0
      }
      const totalScore = filteredResults.reduce((sum, item) => sum + item.score, 0)
      return totalScore / filteredResults.length
    },

    recordsRated() {
      const recordsRated = (this.results || []).filter((item) => item.score > 0)?.length
      return `${recordsRated} of ${this.results?.length} `
    },
    results() {
      return this.evaluation?.results || []
    },
    evaluation_name() {
      return this.evaluation?.tool?.name || ''
    },
    evaluation: {
      get() {
        return this.evalStore.evaluation
      },
    },
    evaluationType() {
      return this.evaluation?.type || ''
    },
    openDrawer() {
      return this.tab === 'records' && Object.keys(this.evalStore.evaluationJobRecord).length > 0
    },
  },
  watch: {},
  mounted() {
    this.getEvaluation()
  },
  methods: {
    async getEvaluation() {
      this.loading = true
      await this.evalStore.getEvaluation({ id: this.$route.params.id })
      this.loading = false
    },
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`${path}`)
      }
    },
    deleteEvaluationSet() {
      notify.confirm({
        message: m.evaluation_deleteNamedConfirm({ name: this.selectedRow?.name || '' }),
        confirmLabel: m.common_delete(),
        cancelLabel: m.common_cancel(),
        onConfirm: () => {
          this.loadingDelelete = true
          this.removeEvaluationJob(this.selectedRow?.id)
          this.$emit('update:closeDrawer', null)
          notify.success(m.notify_entityDeleted({ entity: m.entity_ragTool() }))
          this.navigate('/evaluation_set-tools')
        },
      })
    },
  },
}
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
