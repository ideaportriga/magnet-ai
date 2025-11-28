<template lang="pug">
.no-wrap.full-height.justify-center.q-pa-16.bg-white.fit.relative-position.bl-border(
  style='max-width: 500px; min-width: 500px !important',
  v-if='open && currentRecord'
)
  .column.full-height.no-wrap
    .col-auto.km-heading-7.q-mb-xs Record details
      q-separator

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
    q-scroll-area.fit
      template(v-if='tab == "cost"')
        .col-auto
          template(v-if='$store.getters.evaluation?.type == "prompt_eval"')
            .row.q-gap-16.justify-between
              .km-input-label.text-text-grey Total tokens
                km-input(
                  ref='input',
                  placeholder='Type your text here',
                  :model-value='totalTokens',
                  @input='totalTokens = $event',
                  border-radius='8px',
                  height='36px',
                  type='text',
                  readonly
                )
              .km-input-label.text-text-grey Total cost
                km-input(
                  ref='input',
                  placeholder='Type your text here',
                  :model-value='totalCost',
                  @input='totalCost = $event',
                  border-radius='8px',
                  height='36px',
                  type='text',
                  readonly
                )
            q-separator.q-my-md

            .row.q-gap-16.justify-between.q-mb-sm
              .km-input-label.text-text-grey Input tokens
                km-input(
                  ref='input',
                  placeholder='Type your text here',
                  :model-value='inputTokens',
                  @input='inputTokens = $event',
                  border-radius='8px',
                  height='36px',
                  type='text',
                  readonly
                )
              .km-input-label.text-text-grey Input cost
                km-input(
                  ref='input',
                  placeholder='Type your text here',
                  :model-value='inputCost',
                  @input='inputCost = $event',
                  border-radius='8px',
                  height='36px',
                  type='text',
                  readonly
                )
                .km-description.text-secondary-text 1M tokens - ${{ priceInput }}

            .row.q-gap-16.justify-between.q-mb-sm
              .km-input-label.text-text-grey Output tokens
                km-input(
                  ref='input',
                  placeholder='Type your text here',
                  :model-value='outputTokens',
                  @input='outputTokens = $event',
                  border-radius='8px',
                  height='36px',
                  type='text',
                  readonly
                )
              .km-input-label.text-text-grey Output cost
                km-input(
                  ref='input',
                  placeholder='Type your text here',
                  :model-value='outputCost',
                  @input='outputCost = $event',
                  border-radius='8px',
                  height='36px',
                  type='text',
                  readonly
                )
                .km-description.text-secondary-text 1M tokens - ${{ priceOutput }}
            .row.q-gap-16.justify-between.q-mb-sm
              .km-input-label.text-text-grey Cached tokens
                km-input(
                  ref='input',
                  placeholder='Type your text here',
                  :model-value='cachedTokens',
                  @input='cachedTokens = $event',
                  border-radius='8px',
                  height='36px',
                  type='text',
                  readonly
                )
              .km-input-label.text-text-grey Cached cost
                km-input(
                  ref='input',
                  placeholder='Type your text here',
                  :model-value='cachedCost',
                  @input='cachedCost = $event',
                  border-radius='8px',
                  height='36px',
                  type='text',
                  readonly
                )
                .km-description.text-secondary-text 1M tokens - ${{ priceCached }}

            q-separator.q-my-md
          .row.q-gap-16.justify-between
            .km-input-label.text-text-grey Latency
              km-input(
                ref='input',
                placeholder='Type your text here',
                :model-value='latency',
                @input='latency = $event',
                border-radius='8px',
                height='36px',
                type='text',
                readonly
              )
      template(v-if='tab == "input_and_output"')
        .col-auto(v-if='routeName != "EvaluationCompare"')
          .km-input-label.text-text-grey Evaluation input
          km-input(
            ref='input',
            autogrow,
            placeholder='Type your text here',
            :model-value='evaluationInput',
            @input='evaluationInput = $event',
            border-radius='8px',
            height='36px',
            type='textarea',
            readonly
          )
        .col-auto.q-mt-md
          .km-input-label.text-text-grey Generated output
          km-input(
            ref='input',
            autogrow,
            placeholder='Type your text here',
            :model-value='generatedOutput',
            @input='generatedOutput = $event',
            border-radius='8px',
            height='36px',
            type='textarea',
            readonly
          ) 
        .col-auto.q-mt-md(v-if='routeName != "EvaluationCompare"')
          .km-input-label.text-text-grey Expected output
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
      .km-input-label.text-text-grey Score
        km-select(
          height='30px',
          placeholder='Score',
          :options='scoreOpiotns',
          v-model='score',
          hasDropdownSearch,
          option-value='value',
          option-label='label',
          emit-value,
          map-options
        )
    .col-auto.q-mt-md(v-if='tab == "input_and_output"')
      .km-input-label.text-text-grey Comment
        km-input(
          ref='input',
          autogrow,
          placeholder='Type your text here',
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
import { defineComponent, ref } from 'vue'

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
    return {
      testText: ref(''),
      text: ref(undefined),
      loading: ref(false),
      tab: ref('input_and_output'),
      tabs: ref([
        { name: 'input_and_output', label: 'Inputs & Outputs' },
        { name: 'cost', label: 'Cost & Latency' },
      ]),
    }
  },
  computed: {
    routeName() {
      return this.$route.name
    },
    model() {
      const toolModel = this.$store.getters?.evaluation?.tool?.variant_object?.system_name_for_model
      const objModel = this.$store.getters['chroma/model'].items?.find((model) => model.system_name == toolModel)
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
        return this.$store.getters?.evaluation_job_record || {}
      },
      set(value) {
        this.$store.commit('setEvaluationJobRecord', value)
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
        { label: '1 - Poor', value: 1 },
        { label: '2 - Fair', value: 2 },
        { label: '3 - Average', value: 3 },
        { label: '4 - Good', value: 4 },
        { label: '5 - Excellent', value: 5 },
      ]
    },
  },
  watch: {},
  methods: {
    async setScore(value) {
      if (!value.score) return

      const payload = {
        id: this.currentRecord?.evaluation_id ? this.currentRecord?.evaluation_id : this.$store.getters?.evaluation?.id,
        result_id: this.currentRecord?.id,
        score: value.score,
        score_comment: value.scoreComment,
      }
      await this.$store.dispatch('setScore', payload)
    },
  },
})
</script>
