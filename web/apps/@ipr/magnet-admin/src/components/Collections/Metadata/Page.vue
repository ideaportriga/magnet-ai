<template>
  <div class="row q-gap-8 justify-end">
    <div class="col-auto.center-flex-y">
      <km-input v-model="searchString" placeholder="Search" icon-before="search" clearable @input="searchString = $event" />
    </div>
    <q-space />
    <km-btn
      v-if="selected.length > 0"
      class="q-mr-12"
      icon="delete"
      label="Delete"
      icon-color="icon"
      hover-color="primary"
      :label-class="'km-title'"
      flat
      icon-size="16px"
      hover-bg="primary-bg"
      @click="showDeleteDialog = true"
    />
    <km-btn label="Auto-map" @click="autoMap" />
    <km-btn label="New" @click="showNewDialog = true" />
  </div>

  <div class="row">
    <km-table-new
      v-model:selected="selected"
      selection="multiple"
      row-key="id"
      :active-record-id="activeMetadataConfig?.id"
      :columns="columns"
      :rows="filteredMetadataConfig"
      binary-state-sort
      @select-row="selectRecord"
    />
  </div>

  <collections-metadata-new-record v-if="showNewDialog" :show-new-dialog="showNewDialog" @cancel="showNewDialog = false" />

  <km-popup-confirm
    :visible="showDeleteDialog"
    confirm-button-label="Delete"
    cancel-button-label="Cancel"
    notification-icon="fas fa-triangle-exclamation"
    @confirm="deleteSelected"
    @cancel="showDeleteDialog = false"
  >
    <div class="row item-center justify-center km-heading-7">Delete Metadata Records</div>
    <div class="row text-center justify-center">
      {{ `You are going to delete ${selected?.length} selected records. Are you sure?` }}
    </div>
  </km-popup-confirm>
</template>

<script setup lang="ts">
import { columnsSettings } from '@/config/collections/metadataConfig'
import { ref, computed } from 'vue'
import { useStore } from 'vuex'

// States & Stores
const store = useStore()

const selected = ref([])
const columns = Object.values(columnsSettings).filter((item) => item.display).sort((a, b) => a.columnNumber - b.columnNumber)
const showNewDialog = ref(false)
const showDeleteDialog = ref(false)
const searchString = ref('')

const collectionId = computed(() => store.getters.knowledge?.id)
const metadataConfig = computed({
  get() {
    return store.getters.knowledge?.metadata_config || []
  },
  set(value) {
    store.getters.knowledge.metadata_config = value
  },
})
const activeMetadataConfig = computed(() => store.getters.activeMetadataConfig)

const filteredMetadataConfig = computed(() => {
  const query = (searchString.value || '').trim().toLowerCase()
  if (!query) return metadataConfig.value
  return metadataConfig.value.filter((item: any) => {
    const name = String(item?.name ?? '').toLowerCase()
    const mapping = String(item?.mapping ?? '').toLowerCase()
    return name.includes(query) || mapping.includes(query)
  })
})

const selectRecord = (row) => {
  store.commit('setActiveMetadataConfig', row)
}

const deleteSelected = () => {
  const selectedIds = selected.value.map((item) => item.id)
  metadataConfig.value = metadataConfig.value.filter((item) => !selectedIds.includes(item.id))
  selected.value = []
  showDeleteDialog.value = false
}

const autoMap = async () => {
  const autoMapMetadataConfig = await store.dispatch('autoMapMetadata', {
    collection_id: collectionId.value,
    exclude_fields: metadataConfig.value.map((item) => item.name),
  })
  metadataConfig.value = [
    ...metadataConfig.value,
    ...Object.values(autoMapMetadataConfig).map((mapping: any) => ({ id: crypto.randomUUID(), ...mapping })),
  ]
}
</script>
