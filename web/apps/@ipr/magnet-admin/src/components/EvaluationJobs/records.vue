<template lang="pug">
div(style='min-width: 300px')
  .row.q-mb-12
    .col-auto.center-flex-y
      km-input(placeholder='Search', iconBefore='search', v-model='searchString', @input='searchString = $event', clearable) 
  .row
    km-table(
      @selectRow='selectRecord',
      selection='multiple',
      row-key='id',
      :active-record-id='selectedRow?.id',
      v-model:selected='selected',
      :columns='columns',
      :rows='filteredEvaluationSetItems ?? []',
      :pagination='pagination',
      binary-state-sort
    )
</template>

<script>
import { columnsSettings, evaluationRecord } from '@/config/evaluation_jobs/evaluation_job_records'
import { ref } from 'vue'

export default {
  emits: ['openTest'],
  setup() {
    return {
      columns: Object.values(columnsSettings).sort((a, b) => a.columnNumber - b.columnNumber),
      selected: ref([]),
      evaluationRecord,
      searchString: ref(''),
      pagination: ref({
        rowsPerPage: 10,
        sortBy: 'user_message',
        descending: false,
      }),
    }
  },
  computed: {
    selectedRow() {
      return this.$store.getters.evaluation_job_record
    },
    evaluationSetItems: {
      get() {
        return this.$store.getters.evaluation?.results || []
      },
      set(value) {
        this.$store.commit('updateEvaluationSetProperty', { key: 'items', value })
      },
    },
    filteredEvaluationSetItems() {
      if (!this.searchString) return this.evaluationSetItems
      const lowerCaseSearch = this.searchString.toLowerCase()
      return this.evaluationSetItems.filter((item) => {
        return Object.values(item).some((value) => typeof value === 'string' && value.toLowerCase().includes(lowerCaseSearch))
      })
    },
  },
  mounted() {
    this.selected = [this.selectedRow]
  },
  methods: {
    selectRecord(row) {
      this.selected = []
      this.selected = [row]
      this.$store.commit('setEvaluationJobRecord', row)
    },
  },
}
</script>
