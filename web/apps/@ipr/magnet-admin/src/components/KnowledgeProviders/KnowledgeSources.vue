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
    :columns='columns',
    :visibleColumns='visibleColumns',
    :rows='filteredRows',
    :pagination='pagination',
    binary-state-sort
  )
collections-create-new(v-if='showNewDialog', :showNewDialog='showNewDialog', @cancel='showNewDialog = false', :providerId='providerId')
</template>

<script>
import { ref, computed } from 'vue'
import { useChroma } from '@shared'
import { useRouter } from 'vue-router'

export default {
  setup() {
    const {
      searchString,
      pagination,
      columns,
      visibleColumns,
      visibleRows,
    } = useChroma('collections')

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
    providerId() {
      return this.provider?.id
    },
    filteredRows() {
      if (!this.provider?.id) {
        return []
      }
      // Filter collections by provider_id
      return this.visibleRows.filter((item) => item.provider_id === this.provider.id)
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
