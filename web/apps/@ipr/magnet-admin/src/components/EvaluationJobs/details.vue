<template lang="pug">
.row.no-wrap.overflow-hidden.full-height(v-if='loading', style='min-width: 1200px')
  q-inner-loading(:showing='loading')
    q-spinner-gears(size='50px', color='primary')
.row.no-wrap.overflow-hidden.full-height(v-else, style='min-width: 1200px')
  .col.row.no-wrap.full-height.justify-center.fit
    .col(style='max-width: 1200px; min-width: 600px')
      .full-height.q-pb-md.relative-position.q-px-md
        .items-center.q-gap-12.no-wrap.full-width.q-mt-lg.q-mb-sm.bg-white.border-radius-8.q-py-12.q-px-16.ba-border
          .row.items-center.justify-between.full-width
            .km-heading-7 {{ evaluation_name }}
            .row.q-gap-16
              km-chip(:color='statusStyles.color', round)
                .km-small-chip(:class='`text-${statusStyles.textColor}`') {{ evaluation.status }}
              km-chip(color='in-progress', round)
                .km-small-chip.text-text-grey {{ typeLabel }}
          .km-description.text-secondary-text.q-pt-8 {{ formattedDate }}
          .km-grid.q-mt-16
            dashboard-board-card(header='Latency')
              template(v-slot:body)
                .km-chart-value {{ latency }}
            dashboard-board-card(header='Input cost')
              template(v-slot:body)
                .km-chart-value {{ inputCost }}
            dashboard-board-card(header='Output cost')
              template(v-slot:body)
                .km-chart-value {{ outputCost }}
            dashboard-board-card(header='Total cost')
              template(v-slot:body)
                .km-chart-value {{ totalCost }}

            //.ba-border.bg-white.border-radius-12.q-pa-lg
        .column.no-wrap.q-gap-16.full-height.full-width.overflow-hidden.ba-border.bg-white.border-radius-12.q-pa-lg(style='height: calc(100vh - 300px) !important')
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
import { ref } from 'vue'
import { useChroma } from '@shared'

export default {
  emits: ['update:closeDrawer'],
  setup() {
    const { selectedRow, loading, ...useCollection } = useChroma('evaluation_jobs')

    return {
      tab: ref('records'),
      tabs: ref([
        { name: 'records', label: 'Records' },
        { name: 'settings', label: 'Variant details' },
      ]),
      showNewDialog: ref(false),
      activeEvaluationSet: ref({}),
      prompt: ref(null),
      showInfo: ref(false),
      selectedRow,
      useCollection,
      evaluationSetRecord: ref({}),
      loadingChroma: loading,
      loading: ref(false),
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
      const row = (this.$store.getters['chroma/evaluation_jobs'].items || []).find((item) => item._id == this.evaluation.id)
      return row || {}
    },
    model() {
      return this.$store.getters['chroma/model'].items?.find((model) => model.system_name === this.modelSystemName) || {}
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
        return this.$store.getters.evaluation
      },
    },
    evaluationType() {
      return this.evaluation?.type || ''
    },
    typeLabel() {
      if (this.evaluation?.type === 'prompt_eval') {
        return 'Prompt Template'
      }
      return 'RAG'
    },
    openDrawer() {
      return this.tab === 'records' && Object.keys(this.$store.getters.evaluation_job_record).length > 0
    },
    name: {
      get() {
        return this.$store.getters.evaluation_set?.name || ''
      },
      set(value) {
        this.$store.commit('updateEvaluationSetProperty', { key: 'name', value })
      },
    },
    description: {
      get() {
        return this.$store.getters.evaluation_set?.description || ''
      },
      set(value) {
        this.$store.commit('updateEvaluationSetProperty', { key: 'description', value })
      },
    },
    system_name: {
      get() {
        return this.$store.getters.evaluation_set?.system_name || ''
      },
      set(value) {
        this.$store.commit('updateEvaluationSetProperty', { key: 'system_name', value })
      },
    },
    isEvaluationSetChanged() {
      return this.$store.getters?.isEvaluationSetChanged
    },
    activeEvaluationSetId() {
      return this.$route.params.id
    },
    activeEvaluationSetName() {
      return this.items?.find((item) => item.id == this.activeEvaluationSetId)?.name
    },
    options() {
      return this.items?.map((item) => item.name)
    },
    color() {
      return this.statusStyles?.color || ''
    },
    textColor() {
      return this.statusStyles?.textColor || ''
    },
    statusStyles() {
      if (this.evaluation?.status === 'in_progress') {
        return { color: 'in-progress', textColor: 'text-gray' }
      }
      return { color: 'status-ready', textColor: 'status-ready-text' }
    },
  },
  watch: {
    selectedRow(newVal, oldVal) {
      if (newVal?.id !== oldVal?.id) {
        this.$store.commit('setEvaluationSet', newVal)
        this.tab = 'records'
      }
    },
  },
  mounted() {
    this.getEvaluation()
  },
  methods: {
    async getEvaluation() {
      this.loading = true
      await this.$store.dispatch('getEvaluation', { id: this.$route.params.id })
      this.loading = false
    },
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`${path}`)
      }
    },
    deleteEvaluationSet() {
      this.$q.notify({
        message: `Are you sure you want to delete ${this.selectedRow?.name}?`,
        color: 'error-text',
        position: 'top',
        timeout: 0,
        actions: [
          {
            label: 'Cancel',
            color: 'yellow',
            handler: () => {
              /* ... */
            },
          },
          {
            label: 'Delete',
            color: 'white',
            handler: () => {
              this.loadingDelelete = true
              this.useCollection.delete({ id: this.selectedRow?.id })
              this.$emit('update:closeDrawer', null)
              this.$q.notify({
                position: 'top',
                message: 'RAG Tool has been deleted.',
                color: 'positive',
                textColor: 'black',
                timeout: 1000,
              })
              this.navigate('/evaluation_set-tools')
            },
          },
        ],
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
