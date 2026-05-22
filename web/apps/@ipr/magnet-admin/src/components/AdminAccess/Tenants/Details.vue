<template>
  <div class="stack p-md height-100 width-100" data-gap="md">
    <div class="cluster" data-align="center" data-gap="sm" data-wrap="no">
      <km-btn icon="arrow-left" flat label="Back" @click="$router.push('/admin/tenants')" />
      <div class="stack flex-1" data-gap="xs">
        <h2 class="km-h2">{{ tenant?.name || 'Tenant' }}</h2>
        <div v-if="tenant" class="km-description text-grey font-mono">{{ tenant.slug }}</div>
      </div>
      <div class="cluster" data-gap="sm" data-wrap="no">
        <km-chip v-if="tenant?.is_active === false" tone="muted" size="sm" label="inactive" />
        <km-chip v-else-if="tenant" tone="success" size="sm" label="active" />
        <km-btn
          v-if="isSuperuser"
          label="Save"
          data-test="save-tenant-btn"
          :disabled="!isDirty || saveMutation.isLoading.value"
          @click="save"
        />
      </div>
    </div>

    <km-banner v-if="!isSuperuser" rounded dense>
      <template #avatar>
        <km-glyph name="info" size="16px" />
      </template>
      <span class="km-description">
        Tenant editing is reserved for platform superusers.
      </span>
    </km-banner>

    <div v-if="errorMessage" class="bg-error-bg p-md border-radius-6">
      <div class="text-error">{{ errorMessage }}</div>
    </div>

    <div v-if="loading" class="km-description text-grey p-md">Loading…</div>

    <template v-else-if="tenant">
      <!-- Profile -->
      <div class="stack ba-border border-radius-8 bg-white p-md" data-gap="md">
        <h3 class="km-h3">Tenant</h3>
        <div class="cluster" data-gap="md" data-wrap="yes">
          <div class="stack flex-1 min-w-200" data-gap="xs">
            <label class="km-description">Slug</label>
            <km-input v-model="editSlug" :disabled="!isSuperuser" placeholder="acme" />
          </div>
          <div class="stack flex-1 min-w-200" data-gap="xs">
            <label class="km-description">Display name</label>
            <km-input v-model="editName" :disabled="!isSuperuser" placeholder="Acme Corp" />
          </div>
        </div>
        <div class="cluster" data-gap="sm" data-align="center" data-wrap="no">
          <km-checkbox v-model="editActive" :disable="!isSuperuser" />
          <span class="km-description">Active</span>
        </div>
        <div class="cluster" data-gap="md" data-wrap="yes">
          <div class="stack" data-gap="xs">
            <span class="km-description text-grey">Tenant ID</span>
            <span class="font-mono">{{ tenant.id }}</span>
          </div>
          <div v-if="tenant.created_at" class="stack" data-gap="xs">
            <span class="km-description text-grey">Created</span>
            <span>{{ formatDateTime(tenant.created_at as string) }}</span>
          </div>
          <div class="stack" data-gap="xs">
            <span class="km-description text-grey">Users</span>
            <span>{{ tenant.user_count }}</span>
          </div>
          <div class="stack" data-gap="xs">
            <span class="km-description text-grey">Departments</span>
            <span>{{ tenant.department_count }}</span>
          </div>
        </div>
      </div>

      <!-- Users in this tenant -->
      <div class="stack ba-border border-radius-8 bg-white p-md" data-gap="sm">
        <div class="cluster" data-justify="between" data-align="center" data-wrap="no">
          <h3 class="km-h3">Users</h3>
          <km-btn
            v-if="isSuperuser"
            icon="add"
            flat
            label="Move user here"
            data-test="move-user-btn"
            @click="openMoveDialog"
          />
        </div>

        <div v-if="!tenantUsers.length" class="km-description text-grey p-sm">
          No users in this tenant.
        </div>

        <div v-else class="stack" data-gap="xs">
          <div
            v-for="u in tenantUsers"
            :key="u.id"
            class="cluster ba-border border-radius-6 p-sm"
            data-gap="sm"
            data-align="center"
            data-wrap="no"
          >
            <km-glyph name="user" size="14px" />
            <div class="stack flex-1" data-gap="xs">
              <span class="km-title">{{ u.name || u.email || u.id }}</span>
              <span v-if="u.email && u.email !== u.name" class="km-description text-grey">
                {{ u.email }}
              </span>
            </div>
            <km-chip v-if="u.is_superuser" tone="brand" size="sm" label="superuser" />
            <km-chip v-if="!u.is_active" tone="muted" size="sm" label="inactive" />
            <km-btn
              flat
              size="sm"
              label="Open"
              @click="$router.push(`/admin/users/${u.id}`)"
            />
          </div>
        </div>
      </div>
    </template>

    <km-dialog v-if="showMove" v-model="showMove" title="Move user to this tenant">
      <div class="stack p-md" data-gap="md">
        <div class="km-description text-grey">
          Pick an existing user. Moving them strips their roles and department
          memberships from the previous tenant.
        </div>
        <div class="stack" data-gap="xs">
          <label class="km-description">User</label>
          <select v-model="moveUserId" class="km-input">
            <option value="">— select user —</option>
            <option v-for="u in moveCandidates" :key="u.id" :value="u.id">
              {{ u.email || u.name || u.id }} ({{ u.tenant_id?.slice(0, 8) }})
            </option>
          </select>
        </div>
        <div class="cluster" data-justify="end" data-gap="sm" data-wrap="no">
          <km-btn label="Cancel" flat @click="showMove = false" />
          <km-btn
            label="Move"
            :disabled="!moveUserId || moveMutation.isLoading.value"
            @click="submitMove"
          />
        </div>
      </div>
    </km-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { formatDateTime } from '@shared/utils'
import { useSharedAuthStore } from '@shared/stores/authStore'
import { useSafeMutation } from '@/composables/useSafeMutation'
import {
  getTenant,
  updateTenant,
  listTenantUsers,
  listTenants,
  moveUserToTenant,
  type AdminTenant,
  type TenantUserSummary,
} from '@/api/tenants'

const route = useRoute()
const queryClient = useQueryClient()
const authStore = useSharedAuthStore()
const isSuperuser = computed(() => Boolean(authStore.userInfo?.is_superuser))

const tenantId = computed(() => String(route.params.id))

const tenantQuery = useQuery({
  queryKey: computed(() => ['admin', 'tenants', tenantId.value]),
  queryFn: () => getTenant(tenantId.value),
  enabled: computed(() => Boolean(tenantId.value) && tenantId.value !== 'undefined' && isSuperuser.value),
})
const usersQuery = useQuery({
  queryKey: computed(() => ['admin', 'tenants', tenantId.value, 'users']),
  queryFn: () => listTenantUsers(tenantId.value),
  enabled: computed(() => Boolean(tenantId.value) && tenantId.value !== 'undefined' && isSuperuser.value),
})

const tenant = computed<AdminTenant | null>(() => tenantQuery.data.value ?? null)
const tenantUsers = computed<TenantUserSummary[]>(() => usersQuery.data.value ?? [])
const loading = computed(() => tenantQuery.isLoading.value)

const editSlug = ref('')
const editName = ref('')
const editActive = ref(true)
const initial = ref({ slug: '', name: '', is_active: true })

watch(
  tenant,
  (t) => {
    if (!t) return
    editSlug.value = t.slug
    editName.value = t.name
    editActive.value = t.is_active
    initial.value = { slug: t.slug, name: t.name, is_active: t.is_active }
  },
  { immediate: true },
)

const isDirty = computed(
  () =>
    editSlug.value !== initial.value.slug ||
    editName.value !== initial.value.name ||
    editActive.value !== initial.value.is_active,
)

const errorMessage = ref<string | null>(null)

const saveMutation = useSafeMutation(
  useMutation({
    mutationFn: (args: { id: string; slug: string; name: string; is_active: boolean }) =>
      updateTenant(args.id, {
        slug: args.slug,
        name: args.name,
        is_active: args.is_active,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'tenants'] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'tenants', tenantId.value] })
    },
  }),
  {
    successMessage: 'Tenant saved.',
    onError: (err) => {
      errorMessage.value = err.message
      return false
    },
  },
)

async function save() {
  if (!tenant.value || !isDirty.value) return
  errorMessage.value = null
  await saveMutation.run({
    id: tenant.value.id,
    slug: editSlug.value.trim(),
    name: editName.value.trim(),
    is_active: editActive.value,
  })
}

// ── Move user dialog ──
const showMove = ref(false)
const moveUserId = ref('')

const allTenantsQuery = useQuery({
  queryKey: ['admin', 'tenants'],
  queryFn: () => listTenants(),
  enabled: computed(() => showMove.value && isSuperuser.value),
})

// Fetch users from other tenants to allow moving in.
const otherTenantUsersQuery = useQuery({
  queryKey: computed(() => ['admin', 'tenants', tenantId.value, 'movable']),
  queryFn: async () => {
    const all = allTenantsQuery.data.value ?? []
    const others = all.filter((t) => t.id !== tenantId.value)
    const lists = await Promise.all(others.map((t) => listTenantUsers(t.id)))
    return lists.flatMap((users, idx) =>
      users.map((u) => ({ ...u, tenant_id: others[idx].id })),
    )
  },
  enabled: computed(() => showMove.value && (allTenantsQuery.data.value?.length ?? 0) > 0),
})

const moveCandidates = computed(() => otherTenantUsersQuery.data.value ?? [])

function openMoveDialog() {
  moveUserId.value = ''
  showMove.value = true
}

const moveMutation = useSafeMutation(
  useMutation({
    mutationFn: (args: { userId: string; tenantId: string }) =>
      moveUserToTenant(args.userId, args.tenantId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'tenants'] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] })
    },
  }),
  { successMessage: 'User moved.' },
)

async function submitMove() {
  if (!moveUserId.value || !tenant.value) return
  const { success } = await moveMutation.run({
    userId: moveUserId.value,
    tenantId: tenant.value.id,
  })
  if (success) {
    showMove.value = false
  }
}
</script>

<style scoped>
.min-w-200 { min-inline-size: 200px; }
.km-input {
  padding: 6px 10px;
  border: 1px solid var(--km-color-border, #d0d3da);
  border-radius: 6px;
  font: inherit;
}
</style>
