<template lang="pug">
div
  .row.q-gap-8.justify-end
    .col-auto.center-flex-y
      km-input(placeholder='Search', iconBefore='search', :modelValue='globalFilter', @input='globalFilter = $event', clearable)
    q-space
    km-btn.q-mr-12(
      v-if='selectedRows.length > 0',
      icon='delete',
      label='Delete',
      iconColor='icon',
      hoverColor='primary',
      labelClass='km-title',
      flat,
      iconSize='16px',
      hoverBg='primary-bg',
      @click='showDeleteDialog = true'
    )
    km-btn(label='Auto-map', @click='autoMap')
    km-btn(label='New', @click='showNewDialog = true')

  .row
    km-data-table(
      :table='table',
      row-key='id',
      :activeRowId='activeMetadataConfig?.id',
      @row-click='selectRecord'
    )

  collections-metadata-new-record(v-if='showNewDialog', :showNewDialog='showNewDialog', @cancel='showNewDialog = false')

  km-popup-confirm(
    :visible='showDeleteDialog',
    confirmButtonLabel='Delete',
    cancelButtonLabel='Cancel',
    notificationIcon='fas fa-triangle-exclamation',
    @confirm='deleteSelected',
    @cancel='showDeleteDialog = false'
  )
    .row.item-center.justify-center.km-heading-7 Delete Metadata Records
    .row.text-center.justify-center {{ `You are going to delete ${selectedRows?.length} selected records. Are you sure?` }}
</template>

<script setup lang="ts">
import { ref, computed, markRaw } from 'vue'
import { useCollectionDetailStore, useCollectionMetadataStore } from '@/stores/entityDetailStores'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
import { selectionColumn, textColumn, componentColumn } from '@/utils/columnHelpers'
import Check from '@/config/collections/components/Check.vue'

const collectionStore = useCollectionDetailStore()
const collectionMetadataStore = useCollectionMetadataStore()

const showNewDialog = ref(false)
const showDeleteDialog = ref(false)

const collectionId = computed(() => collectionStore.entity?.id)
const metadataConfig = computed({
  get() {
    return collectionStore.entity?.metadata_config || []
  },
  set(value) {
    if (collectionStore.entity) {
      collectionStore.entity.metadata_config = value
    }
  },
})
const activeMetadataConfig = computed(() => collectionMetadataStore.activeMetadataConfig)

const data = computed(() => metadataConfig.value)

const columns = [
  selectionColumn(),
  componentColumn('enabled', 'Enabled', markRaw(Check), {
    accessorKey: 'enabled',
    align: 'center',
    props: (row: any) => ({ name: 'enabled' }),
  }),
  textColumn('name', 'Name'),
  textColumn('mapping', 'Mapping'),
]

const { table, globalFilter, selectedRows, clearSelection } = useLocalDataTable(data, columns, {
  enableRowSelection: true,
})

const selectRecord = (row: any) => {
  collectionMetadataStore.setActiveMetadataConfig(row)
}

const deleteSelected = () => {
  const selectedIds = selectedRows.value.map((item: any) => item.id)
  metadataConfig.value = metadataConfig.value.filter((item: any) => !selectedIds.includes(item.id))
  clearSelection()
  showDeleteDialog.value = false
}

const autoMap = async () => {
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
