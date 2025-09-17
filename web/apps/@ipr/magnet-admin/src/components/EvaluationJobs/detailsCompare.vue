<template lang="pug">
.row.no-wrap.overflow-hidden.full-height(v-if='loading', style='min-width: 1200px')
  q-inner-loading(:showing='loading')
    q-spinner-gears(size='50px', color='primary')
layouts-details-layout.q-mx-auto(v-else, noHeader)
  template(#breadcrumbs)
    .column.q-px-16.q-mb-16
      .col.items-center
        .row.q-gap-12.no-wrap.items-baseline
          .col-auto
            .km-field.text-secondary-text Evaluated tool:
          .col-auto
            .km-heading-3.q-mr-sm {{ evaluation_list?.[0]?.tool?.name }}
      .col
        .row.q-gap-12.no-wrap.items-baseline
          .col-auto
            .km-field.text-secondary-text Test set:
          .col-auto
            .km-heading-3.q-mr-sm {{ evaluation_list?.[0]?.test_sets?.[0] }}
  template(#content)
    .column.items-center.full-height.full-width.q-gap-16.overflow-auto.q-pt-16
      .col-auto.full-width
        template(v-if='tab == "records"')
          evaluation-jobs-records-compare(@record:update='evaluationSetRecord', :input='evalInuptList[evalInputIndex]')
  template(#drawer)
    evaluation-jobs-drawer(v-if='openDrawer', :open='openDrawer')
configuration-create-new(v-if='showNewDialog', :showNewDialog='showNewDialog', @cancel='showNewDialog = false', copy)
</template>

<script>
import { ref } from 'vue'
import { useChroma } from '@shared'
import _ from 'lodash'

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
      evalInputIndex: ref(0),
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
    evalInuptList() {
      const pairs =
        this.evaluation?.results?.map(({ user_message, expected_output }) => ({
          user_message,
          expected_output,
        })) ?? []

      return _.uniqWith(pairs, _.isEqual)
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
    evaluation_list() {
      return this.$store.getters.evaluation_list || []
    },
    evaluation: {
      get() {
        return this.transformData(this.evaluation_list)
      },
    },
    evaluationType() {
      return this.evaluation?.type || ''
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
      return { color: 'in-progress', textColor: 'text-gray' }
    },
  },
  watch: {
    selectedRow(newVal, oldVal) {
      if (newVal?.id !== oldVal?.id) {
        this.$store.commit('setEvaluationSet', newVal)
      }
    },
  },
  mounted() {
    this.getEvaluation()
  },
  methods: {
    async getEvaluation() {
      this.loading = true
      const ids = this.$route.query.ids ? this.$route.query.ids.split(',') : []
      await this.$store.dispatch('getListOfEvaluations', { ids })
      this.loading = false
    },
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`${path}`)
      }
    },
    transformData(input) {
      const combinedResults = []

      input.forEach((entry) => {
        const { id: evaluation_id, tool, results } = entry

        results.forEach((result) => {
          const enhancedResult = {
            ..._.pick(result, [
              'id',
              'evaluated_at',
              'expected_output',
              'generated_output',
              'iteration',
              'latency',
              'model_version',
              'score',
              'score_comment',
              'test_set',
              'usage',
              'user_message',
            ]),
            evaluation_id,
            system_name: tool.system_name,
            variant: tool.variant_name,
          }
          combinedResults.push(enhancedResult)
        })
      })

      return {
        results: combinedResults,
      }
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
