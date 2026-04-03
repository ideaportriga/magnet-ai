<template lang="pug">
.row.q-mx-sm.items-baseline
  .col-auto
    km-btn(
      flat,
      simple,
      :label='m.common_previous()',
      iconSize='16px',
      icon='fas fa-chevron-left',
      @click='evalInputIndex = evalInputIndex - 1',
      :disable='evalInputIndex === 0'
    )
  .col
    .row.justify-center.fit.q-gap-16.items-center
      .col-auto
        div Test Set item {{ evalInputIndex + 1 }} of {{ evalInputList?.length }}
  .col-auto
    km-btn(
      flat,
      simple,
      :label='m.common_next()',
      iconSize='16px',
      iconAfter='fas fa-chevron-right',
      @click='evalInputIndex = evalInputIndex + 1',
      :disable='evalInputIndex === evalInputList.length - 1'
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
    km-data-table(
      :table='table',
      row-key='id',
      :activeRowId='selectedRow?.id',
      @row-click='selectRecord'
    )
</template>

<script setup>
import { ref, computed, watch, onMounted, markRaw } from 'vue'
import { m } from '@/paraglide/messages'
import _ from 'lodash'
import { useEvaluationStore } from '@/stores/evaluationStore'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
import { selectionColumn, textColumn, componentColumn } from '@/utils/columnHelpers'
import TextWrap from '@/config/evaluation_jobs/component/TextWrap.vue'

const emit = defineEmits(['openTest'])

const evalStore = useEvaluationStore()
const evalInputIndex = ref(null)

const selectedRow = computed(() => evalStore.evaluationJobRecord)

const transformData = (input) => {
  const combinedResults = []

  input.forEach((entry) => {
    const { id: evaluation_id, tool, results } = entry

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
}

const evaluationSetItems = computed(() => {
  return transformData(evalStore.evaluationList || []).results
})

const evalInputList = computed(() => {
  const pairs =
    evaluationSetItems.value?.map(({ user_message, expected_output }) => ({
      user_message,
      expected_output,
    })) ?? []

  return _.uniqWith(pairs, _.isEqual)
})

const input = computed(() => {
  return evalInputList.value[evalInputIndex.value]
})

const filteredEvaluationSetItems = computed(() => {
  return evaluationSetItems.value.filter((el) => el?.user_message === input.value?.user_message)
})

const columns = [
  selectionColumn(),
  textColumn('iteration', 'Iteration'),
  textColumn('variant', 'Variant', {
    format: (val) => {
      const match = val?.match(/variant_(\d+)/)
      return match ? `Variant ${match[1]}` : val
    },
  }),
  componentColumn('generated_output', 'Generated output', markRaw(TextWrap), {
    accessorKey: 'generated_output',
    sortable: true,
    props: (row) => ({ name: 'generated_output' }),
  }),
  textColumn('score', 'Score'),
]

const { table, selectedRows, clearSelection } = useLocalDataTable(filteredEvaluationSetItems, columns, {
  enableRowSelection: true,
  defaultPageSize: 5,
})

watch(input, () => {
  evalStore.evaluationJobRecord = filteredEvaluationSetItems.value[0]
}, { deep: true })

onMounted(() => {
  evalInputIndex.value = 0
})

const selectRecord = (row) => {
  clearSelection()
  evalStore.evaluationJobRecord = row
}
</script>
