<template>
  <div class="km-small-chip">
    <div class="km-field">
      {{ totalCost }}
      <km-tooltip :offset="[0, 10]">
        <div class="flex-none">
          <div class="cluster mb-md" data-gap="lg" data-justify="between">
            <div class="km-input-label">Input cost: {{ inputCost }}</div>
          </div>
          <div class="cluster" data-gap="lg" data-justify="between">
            <div class="km-input-label">Output cost: {{ outputCost }}</div>
          </div>
          <div class="cluster mt-md" data-gap="lg" data-justify="between">
            <div class="km-input-label">Cached cost: {{ cachedCost }}</div>
          </div>
        </div>
      </km-tooltip>
    </div>
  </div>
</template>

<script>
import { defineComponent } from 'vue'
import { getCachedItems } from '@/queries/getCachedItems'

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
      return getCachedItems('model')?.find((model) => model.system_name === this.modelSystemName) || {}
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
  },
})
</script>

<style scoped>
.notification {
  color: var(--ds-color-secondary-text) !important;
  block-size: auto;
  inline-size: 100%;
}
</style>
