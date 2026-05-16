<template>
  <div class="stack full-height" data-gap="0">
    <div class="collection-container mx-auto full-width stack full-height px-md pt-lg" data-gap="0">
      <km-tabs v-model="tab" class="bb-border mb-md" narrow-indicator dense align="left" no-caps content-class="km-tabs">
        <km-tab name="configurations" :label="m.common_configurations()" />
        <km-tab name="providers" :label="m.noteTaker_botProviders()" />
      </km-tabs>
      <template v-if="tab === &quot;configurations&quot;">
        <div class="flex-1 ba-border border-radius-12 bg-white p-lg stack" style="min-block-size: 0" data-gap="0">
          <div class="cluster mb-md">
            <div class="flex-none center-flex-y">
              <km-input :placeholder="m.common_search()" icon-before="search" :model-value="globalFilter" clearable @input="globalFilter = $event" />
            </div>
            <div class="km-space" />
            <div class="flex-none center-flex-y">
              <km-btn v-if="canCreate" class="mr-md" :label="m.common_new()" @click="showNewDialog = true" />
            </div>
          </div>
          <div class="flex-1" style="min-block-size: 0">
            <km-data-table fill-height :table="table" row-key="key" @row-click="openDetails" />
          </div>
        </div>
      </template>
      <note-taker-providers v-if="tab === &quot;providers&quot;" />
      <note-taker-create-new :show-new-dialog="showNewDialog" @cancel="showNewDialog = false" @created="onConfigCreated" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, markRaw, h } from 'vue'
import { useRouter } from 'vue-router'
import { usePermissions } from '@shared'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
import { textColumn, chipCopyColumn, dateColumn, componentColumn } from '@/utils/columnHelpers'
import { m } from '@/paraglide/messages'
import { useNoteTakerStore } from '@/stores/noteTakerStore'
import NoteTakerCreateNew from './CreateNew.vue'
import NoteTakerProviders from './NoteTakerProviders.vue'

const ntStore = useNoteTakerStore()
const router = useRouter()

// Persist active tab in the store so it survives keep-alive cache eviction
const tab = computed({
  get: () => ntStore.activeListTab,
  set: (val: string) => { ntStore.activeListTab = val },
})
const showNewDialog = ref(false)

const { can } = usePermissions()
const canCreate = computed(() => can('write:note_taker'))

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
        icon: 'robot',
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
