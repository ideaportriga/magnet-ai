<template>
  <div>
    <div class="cluster" data-gap="sm" data-justify="end">
      <div class="flex-none center-flex-y">
        <km-input :placeholder="m.common_search()" icon-before="search" :model-value="globalFilter" clearable @input="globalFilter = $event" />
      </div>
      <div class="km-space" />
      <km-btn v-if="!collectionReadonly && selectedRows.length &gt; 0" class="mr-md" icon="delete" :label="m.common_delete()" interaction-tone="brand" label-class="km-title" flat icon-size="16px" @click="showDeleteDialog = true" />
      <km-btn v-if="!collectionReadonly" :label="m.collections_autoMap()" @click="autoMap" />
      <km-btn v-if="!collectionReadonly" :label="m.common_new()" @click="showNewDialog = true" />
    </div>
    <div class="cluster">
      <km-data-table :table="table" row-key="id" :active-row-id="activeMetadataConfig?.id" @row-click="selectRecord" />
    </div>
    <collections-metadata-new-record v-if="showNewDialog" :show-new-dialog="showNewDialog" @cancel="showNewDialog = false" />
    <km-popup-confirm :visible="showDeleteDialog" :confirm-button-label="m.common_delete()" :cancel-button-label="m.common_cancel()" notification-icon="warning" @confirm="deleteSelected" @cancel="showDeleteDialog = false">
      <div class="cluster" data-justify="center">{{ m.collections_deleteMetadataRecords() }}</div>
      <div class="cluster text-center" data-justify="center">{{ m.agents_deleteConfirmMessage({ count: selectedRows?.length ?? 0 }) }}</div>
    </km-popup-confirm>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, inject, markRaw } from 'vue'
import { m } from '@/paraglide/messages'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { useCollectionMetadataStore } from '@/stores/entityDetailStores'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
import { selectionColumn, textColumn, componentColumn } from '@/utils/columnHelpers'
import Check from '@/config/collections/components/Check.vue'

const { draft, updateField } = useEntityDetail('collections')
const collectionMetadataStore = useCollectionMetadataStore()
const collectionReadonlyRef = inject('collectionReadonly', null)
const collectionReadonly = computed(() => Boolean(collectionReadonlyRef?.value))

const showNewDialog = ref(false)
const showDeleteDialog = ref(false)

const collectionId = computed(() => draft.value?.id)
const metadataConfig = computed({
  get() {
    return draft.value?.metadata_config || []
  },
  set(value) {
    updateField('metadata_config', value)
  },
})
const activeMetadataConfig = computed(() => collectionMetadataStore.activeMetadataConfig)

const data = computed(() => metadataConfig.value)

const columns = [
  selectionColumn(),
  componentColumn('enabled', m.common_enabled(), markRaw(Check), {
    accessorKey: 'enabled',
    align: 'center',
    props: (row: any) => ({ name: 'enabled' }),
  }),
  textColumn('name', m.common_name()),
  textColumn('mapping', m.common_mapping()),
]

const { table, globalFilter, selectedRows, clearSelection } = useLocalDataTable(data, columns, {
  enableRowSelection: true,
})

const selectRecord = (row: any) => {
  collectionMetadataStore.setActiveMetadataConfig(row)
}

const deleteSelected = () => {
  if (collectionReadonly.value) return
  const selectedIds = selectedRows.value.map((item: any) => item.id)
  metadataConfig.value = metadataConfig.value.filter((item: any) => !selectedIds.includes(item.id))
  clearSelection()
  showDeleteDialog.value = false
}

const autoMap = async () => {
  if (collectionReadonly.value) return
  const autoMapMetadataConfig = await store.dispatch('autoMapMetadata', {
    collection_id: collectionId.value,
    exclude_fields: metadataConfig.value.map((item: any) => item.name),
  })
  metadataConfig.value = [
    ...metadataConfig.value,
    ...Object.values(autoMapMetadataConfig).map((mapping: any) => ({ id: crypto.randomUUID(), ...mapping })),
  ]
}
</script>
