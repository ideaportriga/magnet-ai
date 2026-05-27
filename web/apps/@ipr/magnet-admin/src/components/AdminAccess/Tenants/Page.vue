<template>
  <km-list-page>
    <template #toolbar>
      <km-input
        data-test="tenant-search"
        placeholder="Search by slug or name"
        icon-before="search"
        :model-value="globalFilter"
        clearable
        @input="onSearchInput"
      />
      <div class="km-space" />
      <km-btn
        v-if="isSuperuser"
        data-test="new-tenant-btn"
        icon="add-square"
        label="New tenant"
        @click="openCreate()"
      />
    </template>

    <km-banner v-if="!isSuperuser" rounded dense>
      <template #avatar>
        <km-glyph name="info" size="16px" />
      </template>
      <span class="km-description">
        Tenant management is reserved for platform superusers.
      </span>
    </km-banner>

    <km-data-table
      v-else
      :table="table"
      :loading="isLoading"
      :fetching="isFetching"
      fill-height
      row-key="id"
      :no-records-label="globalFilter ? 'No tenants match the search.' : 'No tenants yet.'"
      @row-click="openTenant"
    />

    <template #overlays>
      <km-dialog v-if="showCreate" v-model="showCreate" title="New tenant">
        <div class="stack p-md" data-gap="md">
          <div class="stack" data-gap="xs">
            <label class="km-description">Slug</label>
            <km-input
              ref="slugRef"
              v-model="newSlug"
              placeholder="acme"
              :max-length="100"
              :rules="[required(), validSlug()]"
            />
            <div class="km-description text-grey">URL-safe tenant identifier. Lowercase, no spaces.</div>
          </div>
          <div class="stack" data-gap="xs">
            <label class="km-description">Display name</label>
            <km-input
              ref="nameRef"
              v-model="newName"
              placeholder="Acme Corp"
              :max-length="255"
              :rules="[required(), noInvisibleChars()]"
            />
          </div>
          <div class="cluster" data-gap="sm" data-align="center" data-wrap="no">
            <km-checkbox v-model="newActive" />
            <span class="km-description">Active</span>
          </div>
          <div class="cluster" data-justify="end" data-gap="sm" data-wrap="no">
            <km-btn label="Cancel" flat @click="showCreate = false" />
            <km-btn
              label="Create"
              :disabled="!newSlug || !newName || createMutation.isLoading.value"
              data-test="create-tenant-confirm"
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
import { formatDateTime } from '@shared/utils'
import { useSharedAuthStore } from '@shared/stores/authStore'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
import { useSafeMutation } from '@/composables/useSafeMutation'
import { required, validSlug, noInvisibleChars } from '@/utils/validationRules'
import { validateRef } from '@/utils/validateRef'
import { listTenants, createTenant, type AdminTenant } from '@/api/tenants'
import KmChip from '@ds/components/domain/KmChip.vue'

const router = useRouter()
const queryClient = useQueryClient()
const authStore = useSharedAuthStore()
const isSuperuser = computed(() => Boolean(authStore.userInfo?.is_superuser))

const tenantsQuery = useQuery({
  queryKey: ['admin', 'tenants'],
  queryFn: () => listTenants(),
  enabled: isSuperuser,
})
const tenants = computed<AdminTenant[]>(() => tenantsQuery.data.value ?? [])
const isLoading = computed(() => tenantsQuery.isLoading.value)
const isFetching = computed(() => tenantsQuery.isFetching.value)

const columns: ColumnDef<AdminTenant, unknown>[] = [
  {
    id: 'slug',
    accessorKey: 'slug',
    header: 'Slug',
    cell: ({ row }) => h('span', { class: 'font-mono' }, row.original.slug),
    enableSorting: true,
    meta: { width: '180px' },
  },
  {
    id: 'name',
    accessorKey: 'name',
    header: 'Name',
    cell: ({ row }) => row.original.name || '—',
    enableSorting: true,
  },
  {
    id: 'is_active',
    accessorFn: (t) => (t.is_active ? 0 : 1),
    header: 'Status',
    cell: ({ row }) =>
      row.original.is_active
        ? h(KmChip, { tone: 'success', size: 'sm', label: 'active' })
        : h(KmChip, { tone: 'muted', size: 'sm', label: 'inactive' }),
    enableSorting: true,
    meta: { width: '100px' },
  },
  {
    id: 'user_count',
    accessorKey: 'user_count',
    header: 'Users',
    cell: ({ row }) => String(row.original.user_count ?? 0),
    enableSorting: true,
    meta: { align: 'right', width: '90px' },
  },
  {
    id: 'department_count',
    accessorKey: 'department_count',
    header: 'Departments',
    cell: ({ row }) => String(row.original.department_count ?? 0),
    enableSorting: true,
    meta: { align: 'right', width: '120px' },
  },
  {
    id: 'created_at',
    accessorKey: 'created_at',
    header: 'Created',
    cell: ({ row }) =>
      row.original.created_at ? formatDateTime(row.original.created_at as string) : '—',
    enableSorting: true,
    meta: { width: '180px' },
  },
]

const { table, globalFilter } = useLocalDataTable<AdminTenant>(tenants, columns, {
  defaultSort: [{ id: 'slug', desc: false }],
  defaultPageSize: 50,
})

function onSearchInput(val: string) {
  globalFilter.value = val
}

function openTenant(row: AdminTenant) {
  router.push(`/admin/tenants/${row.id}`)
}

// ── Create dialog ──
const showCreate = ref(false)
const newSlug = ref('')
const newName = ref('')
const newActive = ref(true)
const slugRef = ref<{ validate?: () => boolean } | null>(null)
const nameRef = ref<{ validate?: () => boolean } | null>(null)

const createMutation = useSafeMutation(
  useMutation({
    mutationFn: (payload: { slug: string; name: string; is_active: boolean }) =>
      createTenant(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'tenants'] })
    },
  }),
  { successMessage: 'Tenant created.' },
)

function openCreate() {
  newSlug.value = ''
  newName.value = ''
  newActive.value = true
  showCreate.value = true
}

async function submitCreate() {
  const slugValid = validateRef(slugRef.value)
  const nameValid = validateRef(nameRef.value)
  if (!slugValid || !nameValid) return
  const { success, data } = await createMutation.run({
    slug: newSlug.value.trim(),
    name: newName.value.trim(),
    is_active: newActive.value,
  })
  if (success && data) {
    showCreate.value = false
    await router.push(`/admin/tenants/${data.id}`)
  }
}
</script>
