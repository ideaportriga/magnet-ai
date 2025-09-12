<template lang="pug">
layouts-details-layout(v-if='tool')
  template(#breadcrumbs)
    .row.q-pb-md.relative-position.q-px-md
      q-breadcrumbs.text-grey(active-color='text-grey', gutter='lg')
        template(v-slot:separator)
          q-icon(size='12px', name='fas fa-chevron-right', color='text-grey')
        q-breadcrumbs-el
          .column
            .km-small-chip.text-grey.text-capitalize MCP Server
            .km-chip.text-grey-8.text-capitalize.breadcrumb-link(@click='navigate(`/mcp/${mcp_server.id}`)') {{ mcp_server.name }}
        q-breadcrumbs-el
          .column
            .km-small-chip.text-grey.text-capitalize MCP Tool
            .km-chip.text-grey-8.text-capitalize.breadcrumb-link {{ tool.name }}
  template(#header)
    .col
      .row.items-center
        .km-heading-4.full-width.text-black {{ tool.name }}
      .row.items-center.q-mt-12
        .km-description.text-black.full-width {{ tool.description }}

  template(#content)
    q-tabs.bb-border.full-width(
      v-model='tab',
      narrow-indicator,
      dense,
      align='left',
      active-color='primary',
      indicator-color='primary',
      active-bg-color='white',
      no-caps,
      content-class='km-tabs'
    )
      template(v-for='t in tabs')
        q-tab(:name='t.name', :label='t.label')
    .column.q-gap-16.overflow-auto.q-pt-lg.q-pb-lg
      template(v-if='tab == "parameters"')
        .row
          km-table(
            :columns='columns',
            :visibleColumns='visibleColumns',
            :rows='rows',
            row-key='name',
            @selectRow='handleRowClick',
            :selected='[selectedRow]'
          )
      template(v-if='tab == "definition"')
        km-input.full-width(rows='18', border-radius='8px', height='36px', type='textarea', :model-value='JSON.stringify(tool, null, 2)', readonly)
  template(#drawer)
    mcp-tool-drawer(:selectedRow='selectedRow', ref='drawer')
</template>
<script setup>
import { ref, computed, watch } from 'vue'
import { useStore } from 'vuex'
import { useRoute, useRouter } from 'vue-router'
import { useChroma } from '@shared'

const store = useStore()
const route = useRoute()
const router = useRouter()
const { items: mcp_servers } = useChroma('mcp_servers')

const tab = ref('parameters')
const tabs = ref([
  {
    name: 'parameters',
    label: 'Parameters',
  },
  {
    name: 'definition',
    label: 'Tool definition',
  },
])

const visibleColumns = ref(['name', 'description'])
const drawer = ref(null)
const columns = ref([
  {
    name: 'name',
    label: 'Name',
    align: 'left',
    field: 'name',
  },
  {
    name: 'description',
    label: 'Description',
    field: 'description',
    align: 'left',
    style: 'white-space: nowrap; max-width: 200px; overflow: hidden; text-overflow: ellipsis;',
  },
])
const mcp_server = computed(() => {
  return mcp_servers.value.find((item) => item.id === route.params.id)
})

const tool = computed(() => {
  return store.getters.mcp_tool(route.params.name)
})

const rows = computed(() => {
  return Object.keys(tool.value.inputSchema.properties).map((key) => {
    return {
      name: key,
      description: tool.value.inputSchema.properties[key].description,
    }
  })
})

const selectedRow = ref(null)

const handleRowClick = (row) => {
  drawer.value.setTab('details')
  console.log(tool.value.inputSchema.properties[row.name])
  selectedRow.value = {
    name: row.name,
    ...tool.value.inputSchema.properties[row.name],
  }
}

const navigate = (path) => {
  router.push(path)
}

watch(tab, (newVal) => {
  drawer.value.regulateTabs(newVal)
})
watch(
  () => mcp_server.value,
  (newVal) => {
    if (!newVal) return
    store.dispatch('setMcpServer', newVal)
  },
  { immediate: true, deep: true }
)
watch(
  () => tool.value,
  (newVal) => {
    if (!newVal) return
    const key = Object.keys(newVal.inputSchema.properties)[0]
    selectedRow.value = {
      name: key,
      ...newVal.inputSchema.properties[key],
    }
  },
  { immediate: true, deep: true }
)
</script>
