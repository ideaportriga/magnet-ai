<template lang="pug">
div
  .row.q-mb-12
    .col-auto.center-flex-y
      km-input(placeholder='Search', iconBefore='search', v-model='searchString', @input='searchString = $event', clearable) 
    q-space
    .col-auto.center-flex-y
      km-btn.q-mr-12(
        v-if='selected.length > 0',
        icon='delete',
        label='Delete',
        @click='showDeleteDialog = true',
        iconColor='icon',
        hoverColor='primary',
        labelClass='km-title',
        flat,
        iconSize='16px',
        hoverBg='primary-bg'
      )
    .col-auto.center-flex-y
      km-btn.q-mr-12(label='Import', disabled)

    .col-auto.center-flex-y
      km-btn.q-mr-12(label='Add record', @click='openNewDetails')
  .row
    km-table-new(
      @selectRow='selectRecord',
      selection='multiple',
      row-key='id',
      :active-record-id='selectedRow?.id',
      v-model:selected='selected',
      :columns='columns',
      :rows='evaluationSetItems ?? []',
      :pagination='evaluationRecord',
      binary-state-sort
    )

evaluation-sets-create-new-record(:showNewDialog='showNewDialog', @cancel='showNewDialog = false', @addRecord='addRecord', v-if='showNewDialog')
km-popup-confirm(
  :visible='showDeleteDialog',
  confirmButtonLabel='Delete',
  cancelButtonLabel='Cancel',
  notificationIcon='fas fa-triangle-exclamation',
  @confirm='deleteSelected',
  @cancel='showDeleteDialog = false'
)
  .row.item-center.justify-center.km-heading-7 Delete Test Set Records
  .row.text-center.justify-center {{ `You are going to delete ${selected?.length} selected records. Are you sure?` }}
</template>

<script>
import { columnsSettings, evaluationRecord } from '@/config/evaluation_sets/evaluation_set_records'
import { ref } from 'vue'

export default {
  emits: ['openTest'],
  setup() {
    return {
      columns: Object.values(columnsSettings).sort((a, b) => a.columnNumber - b.columnNumber),
      showNewDialog: ref(false),
      selected: ref([]),
      showDeleteDialog: ref(false),
      evaluationRecord,
    }
  },
  computed: {
    selectedRow() {
      return this.$store.getters.evaluation_set_record
    },
    evaluationSetItems: {
      get() {
        return this.$store.getters.evaluation_set?.items || []
      },
      set(value) {
        this.$store.commit('updateEvaluationSetProperty', { key: 'items', value })
      },
    },
  },
  methods: {
    deleteSelected() {
      this.$store.commit('updateEvaluationSetProperty', {
        key: 'items',
        value: this.evaluationSetItems.filter((item) => !this.selected.includes(item)),
      })
      this.selected = []
      this.showDeleteDialog = false
    },
    selectRecord(row) {
      this.$store.commit('setEvaluationSetRecord', row)
    },
    addRecord(newRow) {
      this.$store.commit('updateEvaluationSetProperty', { key: 'items', value: [newRow, ...this.evaluationSetItems] })
    },
    openNewDetails() {
      this.showNewDialog = true
    },
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`/${path}`)
      }
    },
    openDetails() {
      this.navigate('evaluation-sets/details')
    },
  },
}
</script>
