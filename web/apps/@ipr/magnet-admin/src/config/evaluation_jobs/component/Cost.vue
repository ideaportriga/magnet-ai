<template lang="pug">
.km-small-chip(:color='color', :text-color='textColor')
  .km-field {{ totalCost }}
    |
    q-tooltip(:offset='[0, 10]')
      .col-auto
        .row.q-gap-16.justify-between.q-mb-md
          .km-input-label Input cost: {{ inputCost }}
        .row.q-gap-16.justify-between
          .km-input-label Output cost: {{ outputCost }}
        .row.q-gap-16.justify-between.q-mt-md
          .km-input-label Cached cost: {{ cachedCost }}
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
      return parseFloat(result.toPrecision(2))
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
})
</script>

<style scoped>
.notification {
  color: var(--q-secondary-text) !important;
  height: auto;
  width: 100%;
}
</style>
