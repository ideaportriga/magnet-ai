<template lang="pug">
km-inner-loading(:showing='!tool')
layouts-details-layout(v-if='tool')
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
          km-data-table(
            :table='table',
            row-key='name',
            :activeRowId='selectedRow?.name',
            @row-click='handleRowClick'
          )
      template(v-if='tab == "definition"')
        km-input.full-width(rows='18', border-radius='8px', height='36px', type='textarea', :model-value='JSON.stringify(tool, null, 2)', readonly)
  template(#drawer)
    mcp-tool-drawer(:selectedRow='selectedRow', ref='drawer')
</template>
<script setup>
import { m } from '@/paraglide/messages'
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
import { textColumn } from '@/utils/columnHelpers'

const { draft } = useEntityDetail('mcp_servers')
const route = useRoute()
const router = useRouter()

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

const drawer = ref(null)

const tool = computed(() => {
  return draft.value?.tools?.find((t) => t.name === route.params.name)
})

const rows = computed(() => {
  if (!tool.value?.inputSchema?.properties) return []
  return Object.keys(tool.value.inputSchema.properties).map((key) => {
    return {
      name: key,
      description: tool.value.inputSchema.properties[key].description,
    }
  })
})

const columns = [
  textColumn('name', 'Name'),
  textColumn('description', 'Description'),
]

const { table } = useLocalDataTable(rows, columns)

const selectedRow = ref(null)

const handleRowClick = (row) => {
  drawer.value?.setTab('details')
  selectedRow.value = {
    name: row.name,
    ...tool.value.inputSchema.properties[row.name],
  }
}

const navigate = (path) => {
  router.push(path)
}

watch(tab, (newVal) => {
  drawer.value?.regulateTabs(newVal)
})
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
