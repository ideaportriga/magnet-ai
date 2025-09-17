<template lang="pug">
.row.no-wrap.overflow-hidden.full-height
  q-scroll-area.fit
    .row.no-wrap.full-height.justify-center.fit
      .col-auto.collection-container
        .full-height.q-pb-md.relative-position.q-px-md
          .border.border-radius-12.bg-white.ba-border.q-my-16.q-pa-16.q-gap-16.full-width
            .row.q-mb-12
              .col-auto.center-flex-y
                km-input(placeholder='Search', iconBefore='search', v-model='searchString', @input='searchString = $event', clearable) 
              q-space
              .col-auto.q-mr-sm(v-if='selected.length > 0')
                km-btn(
                  label='Delete',
                  @click='showConfirmDialog = true',
                  :disable='selected.length === 0',
                  icon='fa fa-trash',
                  iconSize='16px',
                  flat
                )
              .col-auto.center-flex-y
                km-btn.q-mr-12(label='New', @click='showNewDialog = true')
            .row
              km-table-new(
                selection='multiple',
                row-key='id',
                :columns='columns',
                :rows='rows',
                :visibleColumns='visibleColumns',
                style='min-width: 1100px',
                :pagination='pagination',
                v-model:selected='selected',
                ref='table'
              )
      api-keys-create-new(:showNewDialog='showNewDialog', @cancel='showNewDialog = false')
      km-popup-confirm(
        :visible='showConfirmDialog',
        confirmButtonLabel='Ok, delete',
        cancelButtonLabel='Cancel',
        notificationIcon='fas fa-triangle-exclamation',
        @confirm='deleteSelected',
        @cancel='showConfirmDialog = false'
      )
        .row.item-center.justify-center.km-heading-7.q-mb-md {{ deleteTitle }}
        .row.text-center.justify-center Access granted by this key will be immediately revoked, and any applications or services using it will no longer be able to connect. This action cannot be undone.
</template>
<script setup>
import { ref, computed } from 'vue'
import { useChroma } from '@shared'

const { columns, visibleRows, visibleColumns, pagination, delete: deleteApiKey } = useChroma('api_keys')

const searchString = ref('')
const showNewDialog = ref(false)
const showConfirmDialog = ref(false)
const selected = ref([])
const rows = computed(() => {
  if (!searchString.value) return visibleRows.value
  return visibleRows.value.filter((row) => {
    return row.name.toLowerCase().includes(searchString.value.toLowerCase())
  })
})

const deleteTitle = computed(() => {
  if (selected.value.length === 1) {
    return `You are about to delete an API Key`
  }
  return `You are about to delete ${selected.value.length} API Keys`
})

const deleteSelected = async () => {
  await Promise.all(selected.value.map((item) => deleteApiKey({ id: item.id })))
  selected.value = []
  showConfirmDialog.value = false
}
</script>
