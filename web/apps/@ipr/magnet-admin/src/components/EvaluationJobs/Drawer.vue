<template lang="pug">
km-drawer-layout(v-if='open && currentRecord', storageKey="drawer-evaluation-jobs")
  template(#header)
    .km-heading-7 {{ m.evaluation_recordDetails() }}
  .col-auto.q-mb-md
    .row
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
  template(v-if='tab == "cost"')
    .col-auto
      template(v-if='evalStore.evaluation?.type == "prompt_eval"')
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
  template(v-if='tab == "input_and_output"')
    .col-auto(v-if='routeName != "EvaluationCompare"')
      .km-input-label.text-text-grey {{ m.evaluation_input() }}
      km-input(
        ref='input',
        autogrow,
        :placeholder='m.prompts_typeYourText()',
        :model-value='evaluationInput',
        @input='evaluationInput = $event',
        border-radius='8px',
        height='36px',
        type='textarea',
        readonly
      )
    .col-auto.q-mt-md
      .km-input-label.text-text-grey {{ m.evaluation_generatedOutput() }}
      km-input(
        ref='input',
        autogrow,
        :placeholder='m.prompts_typeYourText()',
        :model-value='generatedOutput',
        @input='generatedOutput = $event',
        border-radius='8px',
        height='36px',
        type='textarea',
        readonly
      )
    .col-auto.q-mt-md(v-if='routeName != "EvaluationCompare"')
      .km-input-label.text-text-grey {{ m.evaluation_expectedOutput() }}
      km-input(
        ref='input',
        autogrow,
        :model-value='expectedOutput',
        @input='expectedOutput = $event',
        border-radius='8px',
        height='36px',
        type='textarea',
        readonly
      )
  .col-auto.q-mt-md(v-if='tab == "input_and_output"')
    .km-input-label.text-text-grey {{ m.evaluation_score() }}
      km-select(
        height='30px',
        :placeholder='m.evaluation_score()',
        :options='scoreOpiotns',
        v-model='score',
        hasDropdownSearch,
        option-value='value',
        option-label='label',
        emit-value,
        map-options
      )
  .col-auto.q-mt-md(v-if='tab == "input_and_output"')
    .km-input-label.text-text-grey {{ m.evaluation_comment() }}
      km-input(
        ref='input',
        autogrow,
        :placeholder='m.prompts_typeYourText()',
        :model-value='scoreComment',
        @input='scoreComment = $event',
        @blur='setScore({ score: score, scoreComment: scoreComment })',
        border-radius='8px',
        height='36px',
        type='textarea',
        :readonly='!score'
      )
</template>
<script>
import { defineComponent, ref, computed } from 'vue'
import { m } from '@/paraglide/messages'
import { useEntityQueries } from '@/queries/entities'
import { useEvaluationStore } from '@/stores/evaluationStore'

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
    const { data: modelData } = queries.model.useList()
    const modelItems = computed(() => modelData.value?.items ?? [])
    const evalStore = useEvaluationStore()

    return {
      m,
      evalStore,
      testText: ref(''),
      text: ref(undefined),
      loading: ref(false),
      tab: ref('input_and_output'),
      tabs: ref([
        { name: 'input_and_output', label: m.evaluation_inputsAndOutputs() },
        { name: 'cost', label: m.evaluation_costAndLatency() },
      ]),
      modelItems,
    }
  },
  computed: {
    routeName() {
      return this.$route.name
    },
    model() {
      const toolModel = this.evalStore.evaluation?.tool?.variant_object?.system_name_for_model
      const objModel = this.modelItems?.find((model) => model.system_name == toolModel)
      return objModel
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
        return this.evalStore.evaluationJobRecord || {}
      },
      set(value) {
        this.evalStore.evaluationJobRecord = value
      },
    },
    evaluationInput: {
      get() {
        return this.currentRecord?.user_message
      },
      set(value) {
        this.currentRecord.user_message = value
      },
    },
    expectedOutput: {
      get() {
        return this.currentRecord?.expected_output
      },
      set(value) {
        this.currentRecord.expected_output = value
      },
    },
    generatedOutput: {
      get() {
        return this.currentRecord?.generated_output
      },
      set(value) {
        this.currentRecord.generated_output = value
      },
    },
    scoreComment: {
      get() {
        return this.currentRecord?.score_comment
      },
      set(value) {
        this.currentRecord.score_comment = value
      },
    },
    score: {
      get() {
        return this.currentRecord?.score
      },
      set(value) {
        this.currentRecord.score = value
        this.setScore({ score: value, scoreComment: this.currentRecord?.score_comment })
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
    scoreOpiotns() {
      return [
        { label: m.evaluation_scorePoor(), value: 1 },
        { label: m.evaluation_scoreFair(), value: 2 },
        { label: m.evaluation_scoreAverage(), value: 3 },
        { label: m.evaluation_scoreGood(), value: 4 },
        { label: m.evaluation_scoreExcellent(), value: 5 },
      ]
    },
  },
  watch: {},
  methods: {
    async setScore(value) {
      if (!value.score) return

      const payload = {
        id: this.currentRecord?.evaluation_id ? this.currentRecord?.evaluation_id : this.evalStore.evaluation?.id,
        result_id: this.currentRecord?.id,
        score: value.score,
        score_comment: value.scoreComment,
      }
      await this.evalStore.setScore(payload)
    },
  },
})
</script>
