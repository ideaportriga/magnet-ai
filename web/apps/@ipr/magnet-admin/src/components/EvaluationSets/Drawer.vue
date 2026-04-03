<template lang="pug">
km-drawer-layout(v-if='open && currentRecord', storageKey="drawer-evaluation-sets", noScroll)
  template(#header)
    .km-heading-7 Test Set item details
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
import { defineComponent, ref, computed } from 'vue'
import { m } from '@/paraglide/messages'
import { useRoute } from 'vue-router'
import { useEntityQueries } from '@/queries/entities'
import { useEvaluationSetRecordStore } from '@/stores/entityDetailStores'

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
    const route = useRoute()
    const queries = useEntityQueries()
    const evalSetRecordStore = useEvaluationSetRecordStore()
    const routeId = computed(() => route.params.id)
    const { data: selectedEvaluationSet } = queries.evaluation_sets.useDetail(routeId)
    return {
      testText: ref(''),
      text: ref(undefined),
      loading: ref(false),
      selectedEvaluationSet,
      evalSetRecordStore,
    }
  },
  computed: {
    currentRecord: {
      get() {
        return this.evalSetRecordStore.record || {}
      },
      set(value) {
        this.evalSetRecordStore.setRecord(value)
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
