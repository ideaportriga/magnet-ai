<template>
  <div>
    <div class="row justify-start items-center q-mb-sm">
      <km-btn :label="m.retrieval_addExample()" size="sm" flat @click="openDialog(null)" />
    </div>

    <!--
      §E.1.1 — migrated from <q-table> to <km-data-table> (TanStack Table).
      Named cell slots (#cell-<colId>) replace q-table's body-cell-<name>
      templates. Empty state and menu/action cells use the same shape.
    -->
    <km-data-table
      :table="table"
      row-key="id"
      hide-pagination
      :no-records-label="m.retrieval_noExamplesYet()"
      @row-click="openDialog"
    >
      <template #cell-index="{ row }">
        {{ indexOf(row) + 1 }}
      </template>

      <template #cell-title="{ row }">
        <span>{{ row.title || '—' }}</span>
      </template>

      <template #cell-input="{ row }">
        <span class="truncate-text">{{ row.input || '—' }}</span>
      </template>

      <template #cell-menu="{ row }">
        <q-btn dense flat color="dark" icon="more_vert" @click.stop>
          <q-menu anchor="bottom right" self="top right" auto-close>
            <q-list dense>
              <q-item clickable @click="openDialog(row)">
                <q-item-section thumbnail>
                  <q-icon name="edit" color="primary" size="20px" class="q-ml-sm" />
                </q-item-section>
                <q-item-section>{{ m.common_edit() }}</q-item-section>
              </q-item>
              <q-separator />
              <q-item clickable @click="emit('remove', row.id)">
                <q-item-section thumbnail>
                  <q-icon name="delete" color="negative" size="20px" class="q-ml-sm" />
                </q-item-section>
                <q-item-section>{{ m.common_delete() }}</q-item-section>
              </q-item>
            </q-list>
          </q-menu>
        </q-btn>
      </template>

      <template #empty-state>
        <div>
          <q-icon name="lightbulb" size="24px" color="grey-5" class="q-mr-sm" />
          <span class="text-grey-6">{{ m.retrieval_noExamplesYet() }}</span>
        </div>
      </template>
    </km-data-table>

    <guided-example-dialog :show-dialog="showDialog" :example="editingExample" @update:show-dialog="showDialog = $event" @save="handleSave" />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, toRefs } from 'vue'
import type { ColumnDef } from '@tanstack/vue-table'
import { m } from '@/paraglide/messages'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
import GuidedExampleDialog from './GuidedExampleDialog.vue'
import type { RetrievalExample } from './models'

const props = defineProps<{
  examples: RetrievalExample[]
}>()

const emit = defineEmits<{
  (e: 'save', example: RetrievalExample): void
  (e: 'remove', id: string): void
}>()

const { examples } = toRefs(props)

const showDialog = ref(false)
const editingExample = ref<RetrievalExample | null>(null)

// Columns — cell rendering delegated to named slots in template above.
const columns: ColumnDef<RetrievalExample, unknown>[] = [
  { id: 'index', header: '#', enableSorting: false, meta: { align: 'center', width: '50px' } },
  { id: 'title', header: m.retrieval_exampleLabel(), accessorKey: 'title', meta: { align: 'left', width: '180px' } },
  { id: 'input', header: m.retrieval_userMessage(), accessorKey: 'input', meta: { align: 'left' } },
  { id: 'menu', header: '', enableSorting: false, meta: { align: 'right', width: '60px' } },
]

const { table } = useLocalDataTable<RetrievalExample>(examples, columns, {
  defaultPageSize: 1000, // effectively disables pagination to match hide-pagination
})

// Used by the index cell to render a 1-based row number that survives sorting.
const rowIndex = computed(() => {
  const map = new Map<string, number>()
  table.getRowModel().rows.forEach((r, i) => map.set((r.original as RetrievalExample).id, i))
  return map
})
function indexOf(row: RetrievalExample): number {
  return rowIndex.value.get(row.id) ?? 0
}

const openDialog = (example: RetrievalExample | null) => {
  editingExample.value = example
  showDialog.value = true
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
</style>
