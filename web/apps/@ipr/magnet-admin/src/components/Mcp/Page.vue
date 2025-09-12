<template lang="pug">
.row.no-wrap.overflow-hidden.full-height
  q-scroll-area.fit
    .row.no-wrap.full-height.justify-center.fit
      .col-auto.collection-container
        .full-height.q-pb-md.relative-position.q-px-md
          .border.border-radius-12.bg-white.ba-border.q-my-16.q-pa-16.q-gap-16.full-width
            .row.q-mb-12
              .col-auto.center-flex-y
                km-input(placeholder='Search', iconBefore='search', v-model='searchString', @input='debouncedUpdateSearch', clearable) 
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
                @selectRow='handleRowClick'
              )
  mcp-new-server(:showNewDialog='showNewDialog', @cancel='showNewDialog = false')
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { debounce } from 'lodash'
import controls from '@/config/mcp/servers'
import { useRouter } from 'vue-router'
import { useChroma } from '@shared'

const searchString = ref('')
const showNewDialog = ref(false)
const router = useRouter()

// Create debounced function to update search string
const debouncedUpdateSearch = debounce((value) => {
  searchString.value = value
}, 300)

const visibleColumns = computed(() => {
  return Object.keys(controls).filter((key) => controls[key])
})
const columns = computed(() => {
  return Object.values(controls)
})

const visibleRows = computed(() => {
  if (!searchString.value) return items.value
  const fields = ['name', 'system_name']
  return items.value.filter((item) => {
    return fields.some((field) => {
      return item[field].toLowerCase().includes(searchString.value.toLowerCase())
    })
  })
})

const handleRowClick = (row) => {
  router.push(`/mcp/${row.id}`)
}

const { items, ...servers } = useChroma('mcp_servers')

onMounted(async () => {
  const data = await servers.get()
})
</script>
