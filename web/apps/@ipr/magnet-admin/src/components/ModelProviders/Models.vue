<template lang="pug">
.row
  .col-auto.center-flex-y
    km-input(
      placeholder='Search',
      iconBefore='search',
      v-model='searchString',
      @input='searchString = $event',
      clearable
    )
  q-space
  .col-auto.center-flex-y
    km-btn.q-mr-12(label='New', @click='showNewDialog = true')
.row
  km-table(
    @selectRow='openDetails',
    selection='single',
    row-key='id',
    :selected='selectedRow ? [selectedRow] : []',
    :columns='columns',
    :visibleColumns='visibleColumns',
    :rows='filteredRows',
    :pagination='pagination',
    binary-state-sort
  )
model-providers-new-model(:showNewDialog='showNewDialog', @cancel='showNewDialog = false')
</template>

<script>
import { ref, computed } from 'vue'
import { useChroma } from '@shared'

export default {
  setup() {
    const {
      searchString,
      pagination,
      columns,
      visibleColumns,
      visibleRows,
      selectedRow,
    } = useChroma('model')

    return {
      searchString,
      pagination,
      columns,
      visibleColumns,
      visibleRows,
      selectedRow,
      showNewDialog: ref(false),
    }
  },
  computed: {
    provider() {
      return this.$store.getters.provider
    },
    filteredRows() {
      if (!this.provider?.system_name) {
        return []
      }
      return this.visibleRows.filter((item) => item.provider_system_name === this.provider.system_name)
    },
  },
  methods: {
    async openDetails(row) {
      await this.$router.push(`/model/${row.id}`)
    },
  },
}
</script>