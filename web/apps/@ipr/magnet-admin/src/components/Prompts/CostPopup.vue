<template lang="pug">
.col-auto.q-mb-md
  .col-auto
    .row.q-gap-16.justify-between
      .km-input-label.text-text-grey {{ m.common_model() }}
        km-input(
          ref='input',
          :placeholder='m.prompts_typeYourText()',
          :model-value='modelLabel',
          @input='modelLabel = $event',
          border-radius='8px',
          height='36px',
          type='text',
          readonly
        )
    q-separator.q-my-md
    .row.q-gap-16.justify-between
      .km-input-label.text-text-grey {{ m.agents_totalTokens() }}
        km-input(
          ref='input',
          :placeholder='m.prompts_typeYourText()',
          :model-value='totalTokens',
          @input='totalTokens = $event',
          border-radius='8px',
          height='36px',
          type='text',
          readonly
        )
      .km-input-label.text-text-grey {{ m.agents_totalCost() }}
        km-input(
          ref='input',
          :placeholder='m.prompts_typeYourText()',
          :model-value='totalCost',
          @input='totalCost = $event',
          border-radius='8px',
          height='36px',
          type='text',
          readonly
        )
    q-separator.q-my-md

    .row.q-gap-16.justify-between.q-mb-sm
      .km-input-label.text-text-grey {{ m.agents_inputTokens() }}
        km-input(
          ref='input',
          :placeholder='m.prompts_typeYourText()',
          :model-value='inputTokens',
          @input='inputTokens = $event',
          border-radius='8px',
          height='36px',
          type='text',
          readonly
        )
      .km-input-label.text-text-grey {{ m.agents_inputCost() }}
        km-input(
          ref='input',
          :placeholder='m.prompts_typeYourText()',
          :model-value='inputCost',
          @input='inputCost = $event',
          border-radius='8px',
          height='36px',
          type='text',
          readonly
        )
        .km-description.text-secondary-text {{ m.agents_1mTokensPrice({ price: priceInput }) }}

    .row.q-gap-16.justify-between.q-mb-sm
      .km-input-label.text-text-grey {{ m.agents_outputTokens() }}
        km-input(
          ref='input',
          :placeholder='m.prompts_typeYourText()',
          :model-value='outputTokens',
          @input='outputTokens = $event',
          border-radius='8px',
          height='36px',
          type='text',
          readonly
        )
      .km-input-label.text-text-grey {{ m.agents_outputCost() }}
        km-input(
          ref='input',
          :placeholder='m.prompts_typeYourText()',
          :model-value='outputCost',
          @input='outputCost = $event',
          border-radius='8px',
          height='36px',
          type='text',
          readonly
        )
        .km-description.text-secondary-text {{ m.agents_1mTokensPrice({ price: priceOutput }) }}
    .row.q-gap-16.justify-between.q-mb-sm
      .km-input-label.text-text-grey {{ m.agents_cachedTokens() }}
        km-input(
          ref='input',
          :placeholder='m.prompts_typeYourText()',
          :model-value='cachedTokens',
          @input='cachedTokens = $event',
          border-radius='8px',
          height='36px',
          type='text',
          readonly
        )
      .km-input-label.text-text-grey {{ m.agents_cachedCost() }}
        km-input(
          ref='input',
          :placeholder='m.prompts_typeYourText()',
          :model-value='cachedCost',
          @input='cachedCost = $event',
          border-radius='8px',
          height='36px',
          type='text',
          readonly
        )
        .km-description.text-secondary-text {{ m.agents_1mTokensPrice({ price: priceCached }) }}

    q-separator.q-my-md
    .row.q-gap-16.justify-between
      .km-input-label.text-text-grey {{ m.agents_latency() }}
        km-input(
          ref='input',
          :placeholder='m.prompts_typeYourText()',
          :model-value='latency',
          @input='latency = $event',
          border-radius='8px',
          height='36px',
          type='text',
          readonly
        )
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
