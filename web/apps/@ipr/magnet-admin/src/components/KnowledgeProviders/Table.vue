<template lang="pug">
.row.q-mb-12
  .col-auto.center-flex-y
    km-input(
      placeholder='Search',
      iconBefore='search',
      v-model='searchString',
      @input='debouncedUpdateSearch',
      clearable
    )
  q-space
  .col-auto.center-flex-y
    km-btn.q-mr-12(label='New', @click='showNewDialog = true')
.row
  km-table(
    @selectRow='openDetails',
    selection='single',
    row-key='system_name',
    :columns='columns',
    :visibleColumns='visibleColumns',
    style='min-width: 1100px',
    ref='table',
    :rows='visibleRows',
    :pagination='pagination',
    :selected='selectedRow ? [selectedRow] : []',
    binary-state-sort
  )
knowledge-providers-new-provider(:showNewDialog='showNewDialog', @cancel='showNewDialog = false')

</template>
<script setup>
import { ref, computed } from 'vue'
import { debounce } from 'lodash'
import { useChroma } from '@shared'
import { useRouter } from 'vue-router'
import controls from '@/config/knowledge_providers/providers'

const router = useRouter()
const { visibleRows: providers, pagination, searchString, selectedRow } = useChroma('provider')

// Set default sorting by updated_at descending
pagination.value = {
  ...pagination.value,
  sortBy: 'updated_at',
  descending: true,
}

const columns = computed(() => {
  return Object.values(controls)
})

const visibleColumns = computed(() => {
  return Object.keys(controls)
})

const showNewDialog = ref(false)

const debouncedUpdateSearch = debounce((value) => {
  searchString.value = value
}, 300)

const visibleRows = computed(() => {
  // Filter providers by category 'knowledge' for Knowledge Providers
  return (providers.value || []).filter(provider => provider.category === 'knowledge')
})

const openDetails = async (row) => {
  await router.push(`/knowledge-providers/${row.id}`)
}
</script>
