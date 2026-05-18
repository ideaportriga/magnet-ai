<template>
  <km-list-page>
    <template #toolbar>
      <km-input
        data-test="user-search"
        placeholder="Search by name or email"
        icon-before="search"
        :model-value="globalFilter"
        clearable
        @input="onSearchInput"
      />
    </template>

    <km-data-table
      :table="table"
      :loading="isLoading"
      :fetching="isFetching"
      fill-height
      row-key="id"
      :no-records-label="globalFilter ? 'No users match the search.' : 'No users in this tenant.'"
      @row-click="openUser"
    />
  </km-list-page>
</template>

<script setup lang="ts">
import { computed, h } from 'vue'
import { useRouter } from 'vue-router'
import { useQuery } from '@tanstack/vue-query'
import type { ColumnDef } from '@tanstack/vue-table'
import { formatDateTime } from '@shared/utils'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
import { listUsers, type AdminUser } from '@/api/adminAccess'
import KmChip from '@ds/components/domain/KmChip.vue'

const router = useRouter()

const usersQuery = useQuery({
  queryKey: ['admin', 'users'],
  queryFn: () => listUsers(),
})
const users = computed<AdminUser[]>(() => usersQuery.data.value ?? [])
const isLoading = computed(() => usersQuery.isLoading.value)
const isFetching = computed(() => usersQuery.isFetching.value)

const columns: ColumnDef<AdminUser, unknown>[] = [
  {
    id: 'name',
    accessorFn: (u) => u.name || u.email || u.preferred_username || u.id,
    header: 'User',
    cell: ({ row }) => {
      const u = row.original
      return h('div', { class: 'stack', 'data-gap': 'xs' }, [
        h('span', { class: 'km-title' }, u.name || u.email || u.preferred_username || u.id),
        u.email && u.email !== u.name
          ? h('span', { class: 'km-description text-grey' }, u.email)
          : null,
      ])
    },
    enableSorting: true,
  },
  {
    id: 'roles',
    accessorFn: (u) => (u.roles || []).join(','),
    header: 'Roles',
    cell: ({ row }) => {
      const slugs = (row.original.roles || []) as string[]
      if (!slugs.length) {
        return h('span', { class: 'km-description text-grey' }, '—')
      }
      return h(
        'div',
        { class: 'cluster', 'data-gap': 'xs', 'data-wrap': 'yes' },
        slugs.map((slug) =>
          h(KmChip, { tone: 'muted', size: 'sm', label: slug, key: slug }),
        ),
      )
    },
    enableSorting: false,
    meta: { class: 'km-data-table__td--wrap' },
  },
  {
    id: 'badges',
    accessorFn: (u) => (u.is_superuser ? 'a' : u.is_active === false ? 'c' : 'b'),
    header: 'Status',
    cell: ({ row }) => {
      const u = row.original
      const chips = []
      if (u.is_superuser) {
        chips.push(h(KmChip, { tone: 'brand', size: 'sm', label: 'superuser', key: 'su' }))
      }
      if (u.is_active === false) {
        chips.push(h(KmChip, { tone: 'muted', size: 'sm', label: 'inactive', key: 'ia' }))
      }
      if (!chips.length) {
        chips.push(h(KmChip, { tone: 'success', size: 'sm', label: 'active', key: 'ac' }))
      }
      return h('div', { class: 'cluster', 'data-gap': 'xs', 'data-wrap': 'no' }, chips)
    },
    enableSorting: true,
    meta: { width: '180px' },
  },
  {
    id: 'last_login_at',
    accessorKey: 'last_login_at',
    header: 'Last login',
    cell: ({ row }) =>
      row.original.last_login_at
        ? formatDateTime(row.original.last_login_at as string)
        : '—',
    enableSorting: true,
    meta: { width: '180px' },
  },
]

const { table, globalFilter } = useLocalDataTable<AdminUser>(users, columns, {
  defaultSort: [{ id: 'name', desc: false }],
  defaultPageSize: 50,
})

function onSearchInput(val: string) {
  globalFilter.value = val
}

function openUser(row: AdminUser) {
  router.push(`/admin/users/${row.id}`)
}
</script>
