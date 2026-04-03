<template lang="pug">
.column.no-wrap.full-height
  .collection-container.q-mx-auto.full-width.column.full-height.q-px-md.q-pt-16

    //- ── Tabs ───────────────────────────────────────────────
    q-tabs.bb-border.q-mb-md(
      v-model='tab',
      narrow-indicator,
      dense,
      align='left',
      active-color='primary',
      indicator-color='primary',
      no-caps,
      content-class='km-tabs'
    )
      q-tab(name='configurations', :label='m.common_configurations()')
      q-tab(name='providers', :label='m.noteTaker_botProviders()')

    //- ── Configurations tab ─────────────────────────────────
    template(v-if='tab === "configurations"')
      .col.ba-border.border-radius-12.bg-white.q-pa-16.column(style='min-height: 0')
        .row.q-mb-12
          .col-auto.center-flex-y
            km-input(:placeholder='m.common_search()', iconBefore='search', :modelValue='globalFilter', @input='globalFilter = $event', clearable)
          q-space
          .col-auto.center-flex-y
            km-btn.q-mr-12(:label='m.common_new()', @click='showNewDialog = true')
        .col(style='min-height: 0')
          km-data-table(
            fill-height,
            :table='table',
            row-key='key',
            @row-click='openDetails'
          )

    //- ── Providers tab ──────────────────────────────────────
    note-taker-providers(v-if='tab === "providers"')

    note-taker-create-new(:showNewDialog='showNewDialog', @cancel='showNewDialog = false', @created='onConfigCreated')
</template>

<script setup lang="ts">
import { ref, computed, onMounted, markRaw, h } from 'vue'
import { useRouter } from 'vue-router'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
import { textColumn, chipCopyColumn, dateColumn, componentColumn } from '@/utils/columnHelpers'
import { m } from '@/paraglide/messages'
import { useNoteTakerStore } from '@/stores/noteTakerStore'
import NoteTakerCreateNew from './CreateNew.vue'
import NoteTakerProviders from './NoteTakerProviders.vue'

const ntStore = useNoteTakerStore()
const router = useRouter()

const tab = ref('configurations')
const showNewDialog = ref(false)

const BotStatusChip = markRaw({
  props: ['row'],
  setup(props: any) {
    return () => {
      const value = props.row?.bot_credentials
      if (!value) return h('span', { class: 'text-grey-5' }, '\u2014')
      return h('q-chip', {
        color: value.client_id ? 'positive' : 'grey-4',
        textColor: value.client_id ? 'white' : 'grey-7',
        dense: true,
        icon: 'smart_toy',
      }, value.client_id ? 'Configured' : 'Not set')
    }
  },
})

const configs = computed(() => {
  const configsData = ntStore.settingsRecords
  return Array.isArray(configsData) ? configsData : []
})

const columns = [
  textColumn('name', m.common_name()),
  textColumn('description', m.common_description()),
  chipCopyColumn(m.common_systemName()),
  componentColumn('bot', 'Bot', BotStatusChip, {
    accessorKey: 'bot_credentials',
  }),
  dateColumn('created_at', m.common_created()),
  dateColumn('updated_at', m.common_lastUpdated()),
]

const { table, globalFilter } = useLocalDataTable(configs, columns)

onMounted(async () => {
  await ntStore.fetchSettings(true)
})

const openDetails = (row: any) => {
  const id = row?.id || row?.system_name || row?.key
  router.push(`/note-taker/${id}`)
}

const onConfigCreated = (configId: string) => {
  router.push(`/note-taker/${configId}`)
}
</script>
