<template lang="pug">
.row.no-wrap.overflow-hidden.full-height(style='max-width: 1200px; margin: 0 auto')
  q-scroll-area.fit
    .row.no-wrap.full-height.justify-center.fit
      .col-auto.collection-container.full-width
        .full-height.q-pb-md.relative-position.q-px-md
          .border.border-radius-12.bg-white.ba-border.q-my-16.q-pa-16.q-gap-16.full-width
            template(v-if='items.length')
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
                  @selectRow='handleRowClick',
                  :pagination='pagination'
                )
            template(v-else)
              .row.items-center.justify-center
                .col-auto.q-pa-xl.bg-light.border-radius-12
                  .row.items-center.justify-center.q-mb-md
                    q-icon(name='fa fa-arrow-right-arrow-left', size='48px', color='primary')
                  .km-heading-7.text-black You have no API Servers yet
                  .km-description.text-black Use an API specification or add an API Server manually
                  .row.items-center.justify-center.q-mt-lg
                    km-btn(label='Add API Server', @click='showNewDialog = true')
  api-servers-new-server(:showNewDialog='showNewDialog', @cancel='showNewDialog = false')
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { debounce } from 'lodash'
import controls from '@/config/api_servers/api_servers'
import { useRouter } from 'vue-router'
import { useChroma } from '@shared'

const searchString = ref('')
const showNewDialog = ref(false)
const router = useRouter()

const pagination = ref({
  rowsPerPage: 10,
  page: 1,
  sortBy: 'updated_at',
  descending: true,
})

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
  router.push(`/api-servers/${row.id}`)
}

const { items, ...servers } = useChroma('api_servers')

onMounted(async () => {
  const data = await servers.get()
})
</script>
