<template lang="pug">
.ba-border.bg-white.border-radius-12.q-pa-sm.full-width(style='min-width: 300px')
  .row.q-mx-sm.items-baseline
    .col-auto
      km-btn(
        flat,
        simple,
        label='Previous',
        iconSize='16px',
        icon='fas fa-chevron-left',
        @click='evalInputIndex = evalInputIndex - 1',
        :disable='evalInputIndex === 0'
      )
    .col
      .row.justify-center.fit.q-gap-16.items-center
        .col-auto
          div Test Set item {{ evalInputIndex + 1 }} of {{ evalInuptList?.length }}
    .col-auto
      km-btn(
        flat,
        simple,
        label='Next',
        iconSize='16px',
        iconAfter='fas fa-chevron-right',
        @click='evalInputIndex = evalInputIndex + 1',
        :disable='evalInputIndex === evalInuptList.length - 1'
      )
  .q-px-md
    .row.q-mb-md.q-mt-sm
      .column
        .col-auto
          .km-label.text-text-grey Evaluation input
          div {{ input?.user_message }}
        .col-auto(v-if='input?.expected_output')
          .km-label.text-text-grey Expected output
          div {{ input?.expected_output }}
    .row
      km-table(
        @selectRow='selectRecord',
        selection='multiple',
        row-key='id',
        :active-record-id='selectedRow?.id',
        v-model:selected='selected',
        :columns='columns',
        :rows='filteredEvaluationSetItems ?? []',
        :pagination='evaluationRecord',
        binary-state-sort
      )
</template>

<script>
import { columnsCompareSettings, evaluationRecord } from '@/config/evaluation_jobs/evaluation_job_records'
import { ref } from 'vue'
import _ from 'lodash'

export default {
  props: {},
  emits: ['openTest'],
  setup() {
    return {
      columns: Object.values(columnsCompareSettings).sort((a, b) => a.columnNumber - b.columnNumber),
      selected: ref([]),
      evaluationRecord,
      searchString: ref(''),
      evalInputIndex: ref(null),
    }
  },
  computed: {
    input() {
      return this.evalInuptList[this.evalInputIndex]
    },
    evalInuptList() {
      const pairs =
        this.evaluationSetItems?.map(({ user_message, expected_output }) => ({
          user_message,
          expected_output,
        })) ?? []

      return _.uniqWith(pairs, _.isEqual)
    },
    selectedRow() {
      return this.$store.getters.evaluation_job_record
    },
    evaluationSetItems: {
      get() {
        return this.transformData(this.$store.getters.evaluation_list || []).results
      },
    },
    filteredEvaluationSetItems() {
      const items = this.evaluationSetItems.filter((el) => el?.user_message === this.input?.user_message)
      return items
    },
  },
  watch: {
    input: {
      deep: true,
      handler() {
        this.$store.commit('setEvaluationJobRecord', this.filteredEvaluationSetItems[0])
        this.selected = [this.filteredEvaluationSetItems[0]]
      },
    },
  },
  mounted() {
    this.evalInputIndex = 0
  },
  methods: {
    transformData(input) {
      const combinedResults = []

      input.forEach((entry) => {
        const { id: evaluation_id, tool, results } = entry
        console.log('entry', entry)
        results.forEach((result) => {
          const enhancedResult = {
            ..._.pick(result, [
              'id',
              'evaluated_at',
              'expected_output',
              'generated_output',
              'iteration',
              'latency',
              'model_version',
              'score',
              'score_comment',
              'test_set',
              'usage',
              'user_message',
            ]),
            evaluation_id,
            system_name: tool.system_name,
            variant: tool.variant_name,
          }
          combinedResults.push(enhancedResult)
        })
      })

      return {
        results: combinedResults,
      }
    },
    selectRecord(row) {
      this.selected = []
      this.selected = [row]
      this.$store.commit('setEvaluationJobRecord', row)
    },
  },
}
</script>
