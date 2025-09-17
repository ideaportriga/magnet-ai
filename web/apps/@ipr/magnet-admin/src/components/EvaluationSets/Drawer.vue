<template lang="pug">
.no-wrap.full-height.justify-center.q-pa-16.bg-white.fit.relative-position.bl-border(
  style='max-width: 500px; min-width: 500px !important',
  v-if='open && currentRecord'
)
  .column.full-height
    .col-auto.km-heading-7.q-mb-xs Test Set item details
      q-separator.q-mb-md
    .column.q-gap-12
      .col-auto(v-if='selectedEvaluationSet?.type === "rag_tool"')
        retrieval-metadata-filter(
          v-model='currentRecord.metadata_filter',
          label='Evaluation metadata filter',
          labelClass='km-input-label text-text-grey q-mr-xs'
        )
      .col-auto
        .km-input-label.text-text-grey Evaluation input
        km-input(
          ref='input',
          rows='16',
          placeholder='Type your text here',
          :model-value='evaluationInput',
          @input='evaluationInput = $event',
          border-radius='8px',
          height='36px',
          type='textarea'
        )
      .col-auto
        .km-input-label.text-text-grey Expected output
        km-input(
          ref='input',
          rows='16',
          placeholder='Type your text here',
          :model-value='expectedOutput',
          @input='expectedOutput = $event',
          border-radius='8px',
          height='36px',
          type='textarea'
        )
</template>
<script>
import { defineComponent, ref } from 'vue'
import { useChroma } from '@shared'

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
    const { selectedRow: selectedEvaluationSet } = useChroma('evaluation_sets')
    return {
      testText: ref(''),
      text: ref(undefined),
      loading: ref(false),
      selectedEvaluationSet,
    }
  },
  computed: {
    currentRecord: {
      get() {
        return this.$store.getters?.evaluation_set_record || {}
      },
      set(value) {
        this.$store.commit('setEvaluationSetRecord', value)
      },
    },
    evaluationInput: {
      get() {
        return this.currentRecord?.user_input
      },
      set(value) {
        this.currentRecord.user_input = value
      },
    },
    expectedOutput: {
      get() {
        return this.currentRecord?.expected_result
      },
      set(value) {
        this.currentRecord.expected_result = value
      },
    },
  },
  watch: {},
  methods: {},
})
</script>
