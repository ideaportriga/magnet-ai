<template>
  <km-drawer-layout v-if="open &amp;&amp; currentRecord" storage-key="drawer-evaluation-sets" no-scroll>
    <template #header>
      <div class="km-heading-7">{{ m.dialog_testSetItemDetails() }}</div>
    </template>
    <div class="stack" data-gap="md">
      <div v-if="selectedEvaluationSet?.type === &quot;rag_tool&quot;" class="flex-none">
        <retrieval-metadata-filter v-model="currentRecord.metadata_filter" :label="m.evaluationJobs_metadataFilter()" label-class="km-input-label text-text-grey mr-xs" />
      </div>
      <div class="flex-none">
        <div class="km-input-label text-text-grey">{{ m.evaluation_input() }}</div>
        <km-input ref="input" rows="16" :placeholder="m.placeholder_typeYourTextHere()" :model-value="evaluationInput" border-radius="8px" height="36px" type="textarea" @input="evaluationInput = $event" />
      </div>
      <div class="flex-none">
        <div class="km-input-label text-text-grey">{{ m.evaluation_expectedOutput() }}</div>
        <km-input ref="input" rows="16" :placeholder="m.placeholder_typeYourTextHere()" :model-value="expectedOutput" border-radius="8px" height="36px" type="textarea" @input="expectedOutput = $event" />
      </div>
    </div>
  </km-drawer-layout>
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
      m,
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
