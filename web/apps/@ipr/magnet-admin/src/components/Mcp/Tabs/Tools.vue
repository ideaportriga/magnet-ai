<template lang="pug">
.full-width.q-pb-lg(v-if='rows?.length')
  .row.q-mb-12
    .col-auto.center-flex-y
      km-input(placeholder='Search', iconBefore='search', v-model='searchString', @input='debouncedUpdateSearch', clearable) 
  km-table.full-width.fit(:columns='columns', :visibleColumns='visibleColumns', :rows='visibleRows', row-key='name', @selectRow='handleRowClick')
template(v-else)
  .column.justify-center.items-center.full-width.full-height
    .col.q-pa-xl.bg-light.border-radius-12
      .row.items-center.justify-center.q-mb-md
        q-icon(name='fa fa-arrow-right-arrow-left', size='48px', color='primary')
      .km-heading-7.text-black You have no MCP tools yet
      .km-description.text-black Sync with the MCP Server to load tools
      .row.items-center.justify-center.q-mt-lg
        km-btn(label='Sync Tools', @click='syncTools')
</template>

<script setup>
import { computed, ref } from 'vue'
import controls from '@/config/mcp/tools'
import { useRouter, useRoute } from 'vue-router'
import { useStore } from 'vuex'
import { useQuasar } from 'quasar'
import { debounce } from 'lodash'

const router = useRouter()
const route = useRoute()
const store = useStore()
const q = useQuasar()

const searchString = ref('')

const visibleColumns = computed(() => {
  return Object.keys(controls).filter((key) => controls[key])
})
const columns = computed(() => {
  return Object.values(controls)
})

const rows = computed(() => {
  return store.getters.mcp_server.tools
})
const debouncedUpdateSearch = debounce((value) => {
  searchString.value = value
}, 300)

const visibleRows = computed(() => {
  if (!searchString.value) return rows.value
  const fields = ['name', 'description']
  return rows.value.filter((item) => {
    return fields.some((field) => {
      return item[field].toLowerCase().includes(searchString.value.toLowerCase())
    })
  })
})

const handleRowClick = (row) => {
  router.push(`${route.path}/tools/${row.name}`)
}

const syncTools = async () => {
  await store.dispatch('saveMcpServer')
  const res = await store.dispatch('syncMcpTools')
  if (res) {
    q.notify({
      position: 'top',
      message: 'MCP Tools have been synced.',
      color: 'positive',
      textColor: 'black',
      timeout: 1000,
    })
  } else {
    q.notify({
      position: 'top',
      message: 'Failed to sync MCP Tools.',
      color: 'negative',
      textColor: 'black',
      timeout: 1000,
    })
  }
}
</script>
