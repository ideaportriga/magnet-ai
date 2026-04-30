<template>
  <div class="flex-none mb-md">
    <div class="flex-none">
      <div class="cluster" data-gap="lg" data-justify="between">
        <div class="km-input-label text-text-grey">
          {{ m.common_model() }}
          <km-input ref="input" :placeholder="m.prompts_typeYourText()" :model-value="modelLabel" border-radius="8px" height="36px" type="text" readonly @input="modelLabel = $event" />
        </div>
      </div>
      <km-separator class="my-md" />
      <div class="cluster" data-gap="lg" data-justify="between">
        <div class="km-input-label text-text-grey">
          {{ m.agents_totalTokens() }}
          <km-input ref="input" :placeholder="m.prompts_typeYourText()" :model-value="totalTokens" border-radius="8px" height="36px" type="text" readonly @input="totalTokens = $event" />
        </div>
        <div class="km-input-label text-text-grey">
          {{ m.agents_totalCost() }}
          <km-input ref="input" :placeholder="m.prompts_typeYourText()" :model-value="totalCost" border-radius="8px" height="36px" type="text" readonly @input="totalCost = $event" />
        </div>
      </div>
      <km-separator class="my-md" />
      <div class="cluster mb-sm" data-gap="lg" data-justify="between">
        <div class="km-input-label text-text-grey">
          {{ m.agents_inputTokens() }}
          <km-input ref="input" :placeholder="m.prompts_typeYourText()" :model-value="inputTokens" border-radius="8px" height="36px" type="text" readonly @input="inputTokens = $event" />
        </div>
        <div class="km-input-label text-text-grey">
          {{ m.agents_inputCost() }}
          <km-input ref="input" :placeholder="m.prompts_typeYourText()" :model-value="inputCost" border-radius="8px" height="36px" type="text" readonly @input="inputCost = $event" />
          <div class="km-description text-secondary-text">{{ m.agents_1mTokensPrice({ price: priceInput }) }}</div>
        </div>
      </div>
      <div class="cluster mb-sm" data-gap="lg" data-justify="between">
        <div class="km-input-label text-text-grey">
          {{ m.agents_outputTokens() }}
          <km-input ref="input" :placeholder="m.prompts_typeYourText()" :model-value="outputTokens" border-radius="8px" height="36px" type="text" readonly @input="outputTokens = $event" />
        </div>
        <div class="km-input-label text-text-grey">
          {{ m.agents_outputCost() }}
          <km-input ref="input" :placeholder="m.prompts_typeYourText()" :model-value="outputCost" border-radius="8px" height="36px" type="text" readonly @input="outputCost = $event" />
          <div class="km-description text-secondary-text">{{ m.agents_1mTokensPrice({ price: priceOutput }) }}</div>
        </div>
      </div>
      <div class="cluster mb-sm" data-gap="lg" data-justify="between">
        <div class="km-input-label text-text-grey">
          {{ m.agents_cachedTokens() }}
          <km-input ref="input" :placeholder="m.prompts_typeYourText()" :model-value="cachedTokens" border-radius="8px" height="36px" type="text" readonly @input="cachedTokens = $event" />
        </div>
        <div class="km-input-label text-text-grey">
          {{ m.agents_cachedCost() }}
          <km-input ref="input" :placeholder="m.prompts_typeYourText()" :model-value="cachedCost" border-radius="8px" height="36px" type="text" readonly @input="cachedCost = $event" />
          <div class="km-description text-secondary-text">{{ m.agents_1mTokensPrice({ price: priceCached }) }}</div>
        </div>
      </div>
      <km-separator class="my-md" />
      <div class="cluster" data-gap="lg" data-justify="between">
        <div class="km-input-label text-text-grey">
          {{ m.agents_latency() }}
          <km-input ref="input" :placeholder="m.prompts_typeYourText()" :model-value="latency" border-radius="8px" height="36px" type="text" readonly @input="latency = $event" />
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import { defineComponent, ref, computed } from 'vue'
import { m } from '@/paraglide/messages'
import { useEntityQueries } from '@/queries/entities'

export default defineComponent({
  props: {
    open: Boolean,
    record: {
      type: Object,
      default: () => ({}),
    },
  },
  emits: ['update:open', 'update:record'],
  setup() {
    const queries = useEntityQueries()
    const { data: modelListData } = queries.model.useList()
    const modelItems = computed(() => modelListData.value?.items ?? [])

    return {
      m,
      text: ref(undefined),
      loading: ref(false),
      modelItems,
    }
  },
  computed: {
    model() {
      const toolModel = this.currentRecord?.inputs?.system_name_for_model
      const objModel = this.modelItems?.find((model) => model.system_name == toolModel)
      return objModel
    },
    modelLabel() {
      return this.model?.display_name
    },
    priceInput() {
      return this.model?.price_input
    },
    priceOutput() {
      return this.model?.price_output
    },
    priceCached() {
      return this.model?.price_cached
    },
    currentRecord: {
      get() {
        return this.record || {}
      },
    },

    inputTokens: {
      get() {
        return this.currentRecord?.usage?.prompt_tokens
      },
      set(value) {
        this.currentRecord.input_tokens = value
      },
    },
    outputTokens: {
      get() {
        return this.currentRecord?.usage?.completion_tokens
      },
      set(value) {
        this.currentRecord.completion_tokens = value
      },
    },
    inputCost: {
      get() {
        const result = (this.inputTokens * this.priceInput) / 1000000
        const significantDigits = 2
        return parseFloat(result.toPrecision(significantDigits))
      },
      set(value) {
        this.currentRecord.input_cost = value
      },
    },
    outputCost: {
      get() {
        const result = (this.outputTokens * this.priceOutput) / 1000000
        const significantDigits = 2
        return parseFloat(result.toPrecision(significantDigits))
      },
      set(value) {
        this.currentRecord.output_cost = value
      },
    },
    cachedCost: {
      get() {
        const result = (this.cachedTokens * this.priceOutput) / 1000000
        const significantDigits = 2
        return parseFloat(result.toPrecision(significantDigits))
      },
      set(value) {
        this.currentRecord.cached_cost = value
      },
    },
    cachedTokens: {
      get() {
        return this.currentRecord?.usage?.cached_tokens || 0
      },
      set(value) {
        this.currentRecord.cached_tokens = value
      },
    },
    totalTokens() {
      return this.inputTokens + this.outputTokens + this.cachedTokens
    },
    totalCost() {
      const result = this.inputCost + this.outputCost + this.cachedCost
      const significantDigits = 2
      return parseFloat(result.toPrecision(significantDigits))
    },
    latency() {
      const result = this.currentRecord?.latency || 0
      return new Intl.NumberFormat(undefined, {
        style: 'unit',
        unit: 'millisecond',
        unitDisplay: 'short',
        maximumFractionDigits: 0,
      }).format(result)
    },
  },
  watch: {},
  methods: {},
})
</script>
