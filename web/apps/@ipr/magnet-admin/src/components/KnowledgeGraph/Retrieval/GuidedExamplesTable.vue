<template>
  <div>
    <div class="row justify-start items-center q-mb-sm">
      <km-btn label="Add Example" size="sm" flat @click="openDialog(null)" />
    </div>

    <q-table
      :rows="examples"
      :columns="columns"
      row-key="id"
      flat
      bordered
      hide-pagination
      table-header-class="bg-primary-light"
      @row-click="onRowClick"
    >
      <template #body-cell-index="slotProps">
        <q-td :props="slotProps">
          {{ slotProps.rowIndex + 1 }}
        </q-td>
      </template>

      <template #body-cell-title="slotProps">
        <q-td :props="slotProps">
          <span>{{ slotProps.row.title || '—' }}</span>
        </q-td>
      </template>

      <template #body-cell-input="slotProps">
        <q-td :props="slotProps">
          <span class="truncate-text">{{ slotProps.row.input || '—' }}</span>
        </q-td>
      </template>

      <template #body-cell-menu="slotProps">
        <q-td :props="slotProps">
          <q-btn dense flat color="dark" icon="more_vert" @click.stop>
            <q-menu anchor="bottom right" self="top right" auto-close>
              <q-list dense>
                <q-item clickable @click="openDialog(slotProps.row)">
                  <q-item-section thumbnail>
                    <q-icon name="edit" color="primary" size="20px" class="q-ml-sm" />
                  </q-item-section>
                  <q-item-section>Edit</q-item-section>
                </q-item>
                <q-separator />
                <q-item clickable @click="$emit('remove', slotProps.row.id)">
                  <q-item-section thumbnail>
                    <q-icon name="delete" color="negative" size="20px" class="q-ml-sm" />
                  </q-item-section>
                  <q-item-section>Delete</q-item-section>
                </q-item>
              </q-list>
            </q-menu>
          </q-btn>
        </q-td>
      </template>

      <template #no-data>
        <div>
          <q-icon name="lightbulb" size="24px" color="grey-5" class="q-mr-sm" />
          <span class="text-grey-6">No examples yet. Add one to guide the agent's behavior.</span>
        </div>
      </template>
    </q-table>

    <guided-example-dialog :show-dialog="showDialog" :example="editingExample" @update:show-dialog="showDialog = $event" @save="handleSave" />
  </div>
</template>

<script setup lang="ts">
import type { QTableColumn } from 'quasar'
import { ref } from 'vue'
import GuidedExampleDialog from './GuidedExampleDialog.vue'
import type { RetrievalExample } from './models'

defineProps<{
  examples: RetrievalExample[]
}>()

const emit = defineEmits<{
  (e: 'save', example: RetrievalExample): void
  (e: 'remove', id: string): void
}>()

const showDialog = ref(false)
const editingExample = ref<RetrievalExample | null>(null)

const columns: QTableColumn[] = [
  {
    name: 'index',
    label: '#',
    field: 'id',
    align: 'center',
    style: 'width: 50px',
  },
  {
    name: 'title',
    label: 'Label',
    field: 'title',
    align: 'left',
    style: 'width: 180px',
  },
  {
    name: 'input',
    label: 'User Message',
    field: 'input',
    align: 'left',
  },
  {
    name: 'menu',
    label: '',
    field: 'id',
    align: 'right',
    style: 'width: 60px',
  },
]

const openDialog = (example: RetrievalExample | null) => {
  editingExample.value = example
  showDialog.value = true
}

const onRowClick = (_evt: Event, row: RetrievalExample) => {
  openDialog(row)
}

const handleSave = (example: RetrievalExample) => {
  emit('save', example)
}
</script>

<style scoped>
.truncate-text {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}

:deep(.q-table__card .q-table thead tr, .q-table__card thead tr) {
  background-color: #f5f5f5;
}

:deep(.q-table__card .q-table thead th, .q-table__card thead th) {
  padding: 16px 12px;
  color: #1a1a1a;
  border-bottom: none;
  font-size: 0.8rem;
  font-weight: 600;
}
</style>
