<template>
  <km-list-page>
    <template #toolbar>
      <km-input
        data-test="role-search"
        placeholder="Search by name or slug"
        icon-before="search"
        :model-value="globalFilter"
        clearable
        @input="onSearchInput"
      />
      <div class="km-space" />
      <km-btn
        v-if="canWriteRoles"
        data-test="new-role-btn"
        icon="add-square"
        label="New role"
        @click="openCreateDialog()"
      />
    </template>

    <km-data-table
      :table="table"
      :loading="isLoading"
      :fetching="isFetching"
      fill-height
      row-key="id"
      :no-records-label="globalFilter ? 'No roles match the search.' : 'No roles yet.'"
      @row-click="openRole"
    />

    <template #overlays>
      <km-dialog v-if="showCreate" v-model="showCreate" title="New custom role">
        <div class="stack p-md" data-gap="md">
          <div class="stack" data-gap="xs">
            <label class="km-description">Slug</label>
            <km-input v-model="newSlug" placeholder="reviewer" />
            <div class="km-description text-grey">URL-safe identifier. Cannot be a system slug.</div>
          </div>
          <div class="stack" data-gap="xs">
            <label class="km-description">Name</label>
            <km-input v-model="newName" placeholder="Reviewer" />
          </div>
          <div class="stack" data-gap="xs">
            <label class="km-description">Description (optional)</label>
            <km-input v-model="newDescription" placeholder="Can review submissions" />
          </div>
          <div class="cluster" data-justify="end" data-gap="sm" data-wrap="no">
            <km-btn label="Cancel" flat @click="showCreate = false" />
            <km-btn
              label="Create"
              :disabled="!newSlug || !newName || createMutation.isLoading.value"
              data-test="create-role-confirm"
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
  listRoles,
  createRole,
  type RoleSummary,
} from '@/api/adminAccess'
import KmChip from '@ds/components/domain/KmChip.vue'

const router = useRouter()
const queryClient = useQueryClient()
const { can } = usePermissions()
const canWriteRoles = computed(() => can('write:roles'))

const rolesQuery = useQuery({
  queryKey: ['admin', 'roles'],
  queryFn: () => listRoles(),
})
const roles = computed<RoleSummary[]>(() => rolesQuery.data.value ?? [])
const isLoading = computed(() => rolesQuery.isLoading.value)
const isFetching = computed(() => rolesQuery.isFetching.value)

// ── Columns ───────────────────────────────────────────────────────────
const columns: ColumnDef<RoleSummary, unknown>[] = [
  {
    id: 'type',
    accessorFn: (r) => (r.is_system ? 0 : 1),
    header: '',
    cell: ({ row }) =>
      h(KmChip, {
        tone: row.original.is_system ? 'brand' : 'muted',
        size: 'sm',
        label: row.original.is_system ? 'system' : 'custom',
      }),
    enableSorting: true,
    meta: { width: '92px' },
  },
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
    meta: { width: '160px' },
  },
  {
    id: 'description',
    accessorKey: 'description',
    header: 'Description',
    cell: ({ row }) => row.original.description || '—',
    enableSorting: false,
  },
  {
    id: 'permissions',
    accessorFn: (r) => r.permissions?.length ?? 0,
    header: 'Permissions',
    cell: ({ row }) => String(row.original.permissions?.length ?? 0),
    enableSorting: true,
    meta: { align: 'right', width: '120px' },
  },
  {
    id: 'user_count',
    accessorKey: 'user_count',
    header: 'Users',
    cell: ({ row }) => String(row.original.user_count ?? 0),
    enableSorting: true,
    meta: { align: 'right', width: '80px' },
  },
]

const { table, globalFilter } = useLocalDataTable<RoleSummary>(roles, columns, {
  defaultSort: [{ id: 'type', desc: false }],
  defaultPageSize: 50,
})

function onSearchInput(val: string) {
  globalFilter.value = val
}

function openRole(row: RoleSummary) {
  router.push(`/admin/roles/${row.id}`)
}

// ── Create dialog ─────────────────────────────────────────────────────
const showCreate = ref(false)
const newSlug = ref('')
const newName = ref('')
const newDescription = ref('')
/** When duplicating a role we pre-fill permissions from that role. */
const seedPermissions = ref<string[]>([])

const createMutation = useSafeMutation(
  useMutation({
    mutationFn: (payload: {
      slug: string
      name: string
      description: string | null
      permissions: string[]
    }) => createRole(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'roles'] })
    },
  }),
  { successMessage: 'Role created.' },
)

function openCreateDialog(seed?: { name: string; permissions: string[] }) {
  newSlug.value = ''
  newName.value = seed ? `${seed.name} (copy)` : ''
  newDescription.value = ''
  seedPermissions.value = seed?.permissions ?? []
  showCreate.value = true
}

async function submitCreate() {
  const { success, data } = await createMutation.run({
    slug: newSlug.value.trim(),
    name: newName.value.trim(),
    description: newDescription.value.trim() || null,
    permissions: seedPermissions.value,
  })
  if (success && data) {
    showCreate.value = false
    await router.push(`/admin/roles/${data.id}`)
  }
}
</script>
