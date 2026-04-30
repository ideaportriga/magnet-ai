<template>
  <div>
    <div class="cluster mb-sm" data-align="start">
      <km-btn :label="m.retrieval_addExample()" size="sm" flat @click="openDialog(null)" />
    </div>

    <!--
      §E.1.1 — migrated from <km-table> to <km-data-table> (TanStack Table).
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
        <ds-dropdown-menu-root>
          <ds-dropdown-menu-trigger as-child>
            <km-btn dense flat tone="neutral" icon="more-vertical" @click.stop />
          </ds-dropdown-menu-trigger>
          <ds-dropdown-menu-content side="bottom" align="end" :side-offset="4">
            <ds-dropdown-menu-item @select="openDialog(row)">
              <km-glyph name="edit" size="18px" /><span>{{ m.common_edit() }}</span>
            </ds-dropdown-menu-item>
            <ds-dropdown-menu-separator />
            <ds-dropdown-menu-item variant="destructive" @select="emit('remove', row.id)">
              <km-glyph name="delete" size="18px" /><span>{{ m.common_delete() }}</span>
            </ds-dropdown-menu-item>
          </ds-dropdown-menu-content>
        </ds-dropdown-menu-root>
      </template>

      <template #empty-state>
        <div>
          <km-glyph name="lightbulb" size="24px" tone="muted" class="mr-sm" />
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
  max-inline-size: 200px;
}
</style>
