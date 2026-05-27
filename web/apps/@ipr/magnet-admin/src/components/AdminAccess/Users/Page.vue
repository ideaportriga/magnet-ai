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
      <div class="km-space" />
      <km-btn
        v-if="canManage"
        data-test="new-user-btn"
        icon="add-square"
        label="New user"
        @click="openCreate()"
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

    <template #overlays>
      <km-dialog v-if="showCreate" v-model="showCreate" title="New user">
        <div class="stack p-md" data-gap="md">
          <div class="stack" data-gap="xs">
            <label class="km-description">Email</label>
            <km-input
              ref="emailRef"
              v-model="newEmail"
              type="email"
              placeholder="user@example.com"
              :max-length="320"
              :rules="[required(), validEmail()]"
            />
          </div>
          <div class="stack" data-gap="xs">
            <label class="km-description">Password</label>
            <km-input
              ref="passwordRef"
              v-model="newPassword"
              type="password"
              autocomplete="new-password"
              :max-length="128"
              :rules="[required(), minLength(8)]"
            />
            <div class="km-description text-grey">At least 8 characters. The user can change it after signing in.</div>
          </div>
          <div class="stack" data-gap="xs">
            <label class="km-description">Name (optional)</label>
            <km-input ref="nameRef" v-model="newName" placeholder="Jane Doe" :max-length="255" />
          </div>
          <div class="cluster" data-justify="end" data-gap="sm" data-wrap="no">
            <km-btn label="Cancel" flat @click="showCreate = false" />
            <km-btn
              label="Create"
              data-test="create-user-confirm"
              :disabled="!newEmail || !newPassword || createMutation.isLoading.value"
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
import { usePermissions } from '@shared'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
import { useSafeMutation } from '@/composables/useSafeMutation'
import { required, validEmail, minLength } from '@/utils/validationRules'
import { validateRef } from '@/utils/validateRef'
import { listUsers, createUser, type AdminUser, type UserCreatePayload } from '@/api/adminAccess'
import KmChip from '@ds/components/domain/KmChip.vue'

const router = useRouter()
const queryClient = useQueryClient()
const { can } = usePermissions()
const canManage = computed(() => can('manage:users'))

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

// ── Create dialog ──
const showCreate = ref(false)
const newEmail = ref('')
const newPassword = ref('')
const newName = ref('')
const emailRef = ref<{ validate?: () => boolean } | null>(null)
const passwordRef = ref<{ validate?: () => boolean } | null>(null)
const nameRef = ref<{ validate?: () => boolean } | null>(null)

const createMutation = useSafeMutation(
  useMutation({
    mutationFn: (payload: UserCreatePayload) => createUser(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] })
    },
  }),
  { successMessage: 'User created.' },
)

function openCreate() {
  newEmail.value = ''
  newPassword.value = ''
  newName.value = ''
  showCreate.value = true
}

async function submitCreate() {
  const validStates = [
    validateRef(emailRef.value),
    validateRef(passwordRef.value),
    validateRef(nameRef.value),
  ]
  if (validStates.includes(false)) return
  const { success, data } = await createMutation.run({
    email: newEmail.value.trim(),
    password: newPassword.value,
    name: newName.value.trim() || null,
  })
  if (success && data) {
    showCreate.value = false
    await router.push(`/admin/users/${data.id}`)
  }
}
</script>
