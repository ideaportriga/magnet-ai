<template lang="pug">
.row
  .col-auto.center-flex-y
    km-input(placeholder='Search', iconBefore='search', v-model='searchString', @input='searchString = $event', clearable)
  q-space
  .col-auto.center-flex-y
    km-btn.q-mr-12(label='New', @click='showNewDialog = true')
.row
  km-table(
    @selectRow='openDetails',
    selection='single',
    row-key='id',
    :columns='columns',
    :visibleColumns='visibleColumns',
    :rows='filteredRows',
    :pagination='pagination',
    binary-state-sort
  )
collections-create-new(
  v-if='showNewDialog',
  :showNewDialog='showNewDialog',
  @cancel='showNewDialog = false',
  :providerSystemName='providerSystemName'
)
</template>

<script>
import { ref, computed } from 'vue'
import { useChroma } from '@shared'
import { useRouter } from 'vue-router'

export default {
  setup() {
    const { searchString, pagination, columns, visibleColumns, visibleRows } = useChroma('collections')

    const router = useRouter()

    return {
      searchString,
      pagination,
      columns,
      visibleColumns,
      visibleRows,
      showNewDialog: ref(false),
      router,
    }
  },
  computed: {
    provider() {
      return this.$store.getters.provider
    },
    providerSystemName() {
      return this.provider?.system_name
    },
    filteredRows() {
      if (!this.provider?.system_name) {
        return []
      }
      // Filter collections by provider_system_name
      return this.visibleRows.filter((item) => item.provider_system_name === this.provider.system_name)
    },
  },
  methods: {
    async openDetails(row) {
      // Navigate to collection details
      await this.router.push(`/knowledge-sources/${row.id}`)
    },
  },
}
</script>
