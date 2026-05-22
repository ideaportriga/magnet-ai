<template>
  <km-list-page>
    <template #toolbar>
      <km-input
        data-test="department-search"
        placeholder="Search by slug or name"
        icon-before="search"
        :model-value="globalFilter"
        clearable
        @input="onSearchInput"
      />
      <div class="km-space" />
      <km-btn
        v-if="canManage"
        data-test="new-department-btn"
        icon="add-square"
        label="New department"
        @click="openCreate()"
      />
    </template>

    <km-data-table
      :table="table"
      :loading="isLoading"
      :fetching="isFetching"
      fill-height
      row-key="id"
      :no-records-label="globalFilter ? 'No departments match the search.' : 'No departments yet.'"
      @row-click="openDepartment"
    />

    <template #overlays>
      <km-dialog v-if="showCreate" v-model="showCreate" title="New department">
        <div class="stack p-md" data-gap="md">
          <div class="stack" data-gap="xs">
            <label class="km-description">Slug</label>
            <km-input v-model="newSlug" placeholder="engineering" />
            <div class="km-description text-grey">URL-safe identifier. Unique inside this tenant.</div>
          </div>
          <div class="stack" data-gap="xs">
            <label class="km-description">Name</label>
            <km-input v-model="newName" placeholder="Engineering" />
          </div>
          <div class="stack" data-gap="xs">
            <label class="km-description">Parent department (optional)</label>
            <select v-model="newParentId" class="km-input">
              <option value="">— none —</option>
              <option v-for="d in departments" :key="d.id" :value="d.id">
                {{ d.name }} ({{ d.slug }})
              </option>
            </select>
          </div>
          <div class="cluster" data-justify="end" data-gap="sm" data-wrap="no">
            <km-btn label="Cancel" flat @click="showCreate = false" />
            <km-btn
              label="Create"
              :disabled="!newSlug || !newName || createMutation.isLoading.value"
              data-test="create-department-confirm"
              @click="submitCreate"
            />
          </div>
        </div>
      </km-dialog>
    </template>
  </km-list-page>
</template>

<script setup lang="ts">
import { computed, h, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import type { ColumnDef } from '@tanstack/vue-table'
import { usePermissions } from '@shared'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
import { useSafeMutation } from '@/composables/useSafeMutation'
import {
  listDepartments,
  createDepartment,
  type AdminDepartment,
} from '@/api/departments'

const router = useRouter()
const queryClient = useQueryClient()
const { can } = usePermissions()
const canManage = computed(() => can('manage:users'))

const deptQuery = useQuery({
  queryKey: ['admin', 'departments'],
  queryFn: () => listDepartments(),
})
const departments = computed<AdminDepartment[]>(() => deptQuery.data.value ?? [])
const isLoading = computed(() => deptQuery.isLoading.value)
const isFetching = computed(() => deptQuery.isFetching.value)

const parentNameById = computed(() => {
  const map: Record<string, string> = {}
  for (const d of departments.value) map[d.id] = d.name
  return map
})

const columns: ColumnDef<AdminDepartment, unknown>[] = [
  {
    id: 'name',
    accessorKey: 'name',
    header: 'Name',
    cell: ({ row }) => row.original.name || '—',
    enableSorting: true,
  },
  {
    id: 'slug',
    accessorKey: 'slug',
    header: 'Slug',
    cell: ({ row }) => h('span', { class: 'font-mono' }, row.original.slug),
    enableSorting: true,
    meta: { width: '180px' },
  },
  {
    id: 'parent',
    accessorFn: (d) => (d.parent_id ? parentNameById.value[d.parent_id] || '' : ''),
    header: 'Parent',
    cell: ({ row }) =>
      row.original.parent_id
        ? parentNameById.value[row.original.parent_id] || '—'
        : '—',
    enableSorting: true,
    meta: { width: '200px' },
  },
  {
    id: 'member_count',
    accessorKey: 'member_count',
    header: 'Members',
    cell: ({ row }) => String(row.original.member_count ?? 0),
    enableSorting: true,
    meta: { align: 'right', width: '120px' },
  },
]

const { table, globalFilter } = useLocalDataTable<AdminDepartment>(departments, columns, {
  defaultSort: [{ id: 'name', desc: false }],
  defaultPageSize: 50,
})

function onSearchInput(val: string) {
  globalFilter.value = val
}

function openDepartment(row: AdminDepartment) {
  router.push(`/admin/departments/${row.id}`)
}

// ── Create dialog ──
const showCreate = ref(false)
const newSlug = ref('')
const newName = ref('')
const newParentId = ref('')

const createMutation = useSafeMutation(
  useMutation({
    mutationFn: (payload: { slug: string; name: string; parent_id: string | null }) =>
      createDepartment(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'departments'] })
    },
  }),
  { successMessage: 'Department created.' },
)

function openCreate() {
  newSlug.value = ''
  newName.value = ''
  newParentId.value = ''
  showCreate.value = true
}

async function submitCreate() {
  const { success, data } = await createMutation.run({
    slug: newSlug.value.trim(),
    name: newName.value.trim(),
    parent_id: newParentId.value || null,
  })
  if (success && data) {
    showCreate.value = false
    await router.push(`/admin/departments/${data.id}`)
  }
}
</script>

<style scoped>
.km-input {
  padding: 6px 10px;
  border: 1px solid var(--km-color-border, #d0d3da);
  border-radius: 6px;
  font: inherit;
}
</style>
