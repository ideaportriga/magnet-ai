<template lang="pug">
.row.no-wrap.overflow-hidden.full-height(style='max-width: 1200px; margin: 0 auto')
  q-scroll-area.fit
    .row.no-wrap.full-height.justify-center.fit
      .col-auto.collection-container.full-width
        .full-height.q-pb-md.relative-position.q-px-md.q-mt-lg
          .border.border-radius-12.bg-white.ba-border.q-my-16.q-pa-16.q-gap-16.full-width
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
knowledge-providers-new-provider(:showNewDialog='showNewDialog', @cancel='showNewDialog = false')
</template>
<script setup>
import { ref, computed } from 'vue'
import { debounce } from 'lodash'
import controls from '@/config/knowledge_providers/providers'



const rows = ref([])

const columns = computed(() => {
  return Object.values(controls)
})
const visibleColumns = computed(() => {
  return Object.keys(controls)
})

const searchString = ref('')
const showNewDialog = ref(false)
const debouncedUpdateSearch = debounce((value) => {
  searchString.value = value
}, 300)

const visibleRows = computed(() => {
  return rows.value.filter((row) => {
    return row.name.toLowerCase().includes(searchString.value.toLowerCase()) //change to fields
  })
})

const pagination = ref({
  rowsPerPage: 10,
  page: 1,
  sortBy: 'updated_at',
  descending: true,
})

</script>