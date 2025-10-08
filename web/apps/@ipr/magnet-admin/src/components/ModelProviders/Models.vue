<template lang="pug">
.row
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
    :columns='columns',
    :visibleColumns='visibleColumns',
    :rows='rows'
  )
model-providers-new-model(:showNewDialog='showNewDialog', @cancel='showNewDialog = false')
</template>
<script setup>
import { ref, computed } from 'vue'
import { debounce } from 'lodash'
import controls from '@/config/model_providers/models'


const searchString = ref('')
const showNewDialog = ref(false)
const debouncedUpdateSearch = debounce((value) => {
  searchString.value = value
}, 300)

const columns = computed(() => {
  return Object.values(controls)
})
const visibleColumns = computed(() => {
  return Object.keys(controls)
})
const rows = ref([])

const visibleRows = computed(() => {
  return rows.value.filter((row) => {
    return row.name.toLowerCase().includes(searchString.value.toLowerCase()) //change to fields
  })
})

</script>