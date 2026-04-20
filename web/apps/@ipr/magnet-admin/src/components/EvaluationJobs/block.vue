<template lang="pug">
.row.no-wrap.overflow-hidden.full-height(v-if='loading', style='min-width: 1200px')
  km-inner-loading(:showing='loading')
.row.no-wrap.overflow-hidden.full-height(v-else, style='min-width: 1200px')
  .col.row.no-wrap.full-height.justify-center.fit
    .col(style='max-width: 1200px; min-width: 600px')
      .full-height.q-pb-md.relative-position.q-px-md
        .row.q-gap-12.no-wrap.full-width.q-mt-lg.q-mb-sm
          .col
            .row.items-center
              .km-heading-7.full-width {{ evaluation_name }}
              .row.items-center
                .km-heading-2.text-secondary.full-width {{ formattedDate }}
          .col-auto
            .grid-container.ba-border.bg-white.border-radius-12.q-py-xs.q-pr-md
              .grid-item
                km-score(:score='averageScore || m.evaluation_notRated()')
              .grid-item-left.km-label {{ m.evaluation_avgScore() }}
              .grid-item.km-chip.text-text-gray {{ recordsRated }}
              .grid-item-left.km-label {{ m.evaluation_recordsRated() }}
              .grid-item(v-if='evaluationType == "prompt_eval"')
                q-chip.km-chip(:color='color', :text-color='textColor', :label='totalCost')
              .grid-item-left.km-label(v-if='evaluationType == "prompt_eval"') {{ m.evaluation_avgTotalCost() }}
              .grid-item.km-chip.text-text-gray {{ latency }}
              .grid-item-left.km-label {{ m.evaluation_avgLatency() }}

        q-tabs(
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
        .column.no-wrap.q-gap-16.full-height.full-width.overflow-hidden.q-my-md(style='height: calc(100vh - 256px) !important')
          .row.q-gap-16.full-height.full-width
            .col.full-height.full-width
              .column.items-center.full-height.full-width.q-gap-16.overflow-auto
                template(v-if='true')
                  .col-auto.full-width
                    template(v-if='tab == "records"')
                      evaluation-jobs-records(@record:update='evaluationSetRecord')
                    template(v-if='tab == "settings"')
                      template(v-if='evaluationType == "prompt_eval"')
                        evaluation-jobs-settings
                      template(v-else)
                        evaluation-jobs-settings-rag

  .col-auto
    evaluation-jobs-drawer(v-if='openDrawer', :open='openDrawer')
  configuration-create-new(v-if='showNewDialog', :showNewDialog='showNewDialog', @cancel='showNewDialog = false', copy)
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
    color() {
      return this.statusStyles?.color || ''
    },
    textColor() {
      return this.statusStyles?.textColor || ''
    },
    statusStyles() {
      return { color: 'in-progress', textColor: 'text-gray' }
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
