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
    selection='single',
    row-key='system_name',
    :columns='columns',
    :visibleColumns='visibleColumns',
    style='min-width: 1100px',
    ref='table',
    :rows='visibleRows',
    :pagination='pagination'
  )
model-providers-new-provider(:showNewDialog='showNewDialog', @cancel='showNewDialog = false')

</template>
<script setup>
import { ref, computed } from 'vue'
import { debounce } from 'lodash'
import  controls  from '@/config/model_providers/providers'

const columns = computed(() => {
  return Object.values(controls)
})
const visibleColumns = computed(() => {
  return Object.keys(controls)
})

const showNewDialog = ref(false)
const searchString = ref('')
const debouncedUpdateSearch = debounce((value) => {
  searchString.value = value
}, 300)


const visibleRows = computed(() => {
  return []
})
</script>