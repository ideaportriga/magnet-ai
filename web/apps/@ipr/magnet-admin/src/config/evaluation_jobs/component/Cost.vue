<template lang="pug">
.km-small-chip(:color='color', :text-color='textColor')
  .km-field {{ totalCost }}
    |
    q-tooltip(:offset='[0, 10]')
      .col-auto(v-if='hasAverageCost')
        .row.q-gap-16.justify-between
          .km-input-label Recorded avg cost: {{ totalCost }}
      .col-auto(v-else)
        .row.q-gap-16.justify-between.q-mb-md
          .km-input-label Input cost: {{ displayInputCost }}
        .row.q-gap-16.justify-between
          .km-input-label Output cost: {{ displayOutputCost }}
        .row.q-gap-16.justify-between.q-mt-md
          .km-input-label Cached cost: {{ displayCachedCost }}
</template>

<script>
import { defineComponent } from 'vue'

export default defineComponent({
  props: {
    row: {
      type: Object,
      required: true,
    },
  },
  computed: {
    label() {
      return this.row?.tool?.name || ''
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
    averageScore() {
      return this.row?.average_score || 0
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
    averageCost() {
      const cost = Number(this.row?.average_cost)
      return Number.isFinite(cost) ? cost : null
    },
    hasAverageCost() {
      return this.averageCost !== null && Number(this.row?.results_with_cost || 0) > 0
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
      return result
    },
    outputCost() {
      const result = (this.outputTokens * this.priceOutput) / 1000000
      return result
    },
    cachedCost() {
      const result = (this.cachedTokens * this.priceCached) / 1000000
      return result
    },
    displayInputCost() {
      return this.formatCost(this.hasAverageCost ? 0 : this.inputCost)
    },
    displayOutputCost() {
      return this.formatCost(this.hasAverageCost ? 0 : this.outputCost)
    },
    displayCachedCost() {
      return this.formatCost(this.hasAverageCost ? 0 : this.cachedCost)
    },
    totalTokens() {
      return this.roundedInputTokens + this.roundedOutputTokens + this.roundedCachedTokens
    },
    totalCost() {
      const result = this.hasAverageCost ? this.averageCost : this.inputCost + this.outputCost + this.cachedCost
      return this.formatCost(result)
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
  methods: {
    formatCost(value) {
      const cost = Number(value || 0)
      return Number.isFinite(cost) ? parseFloat(cost.toPrecision(2)) : 0
    },
  },
})
</script>

<style scoped>
.notification {
  color: var(--q-secondary-text) !important;
  height: auto;
  width: 100%;
}
</style>
