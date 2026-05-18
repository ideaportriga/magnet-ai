<template>
  <div class="stack p-md height-100 width-100" data-gap="md">
    <div class="cluster" data-align="center" data-gap="sm" data-wrap="no">
      <km-btn icon="arrow-left" flat label="Back" @click="$router.push('/admin/users')" />
      <div class="stack flex-1" data-gap="xs">
        <h2 class="km-h2">{{ user?.name || user?.email || 'User' }}</h2>
        <div v-if="user" class="km-description text-grey">{{ user.email }}</div>
      </div>
      <div class="cluster" data-gap="sm" data-wrap="no">
        <km-chip v-if="user?.is_superuser" tone="brand" size="sm" label="superuser" />
        <km-chip v-if="user?.is_active === false" tone="muted" size="sm" label="inactive" />
      </div>
    </div>

    <div v-if="errorMessage" class="bg-error-bg p-md border-radius-6">
      <div class="text-error">{{ errorMessage }}</div>
    </div>

    <div v-if="loading" class="km-description text-grey p-md">Loading…</div>

    <template v-else-if="user">
      <!-- Profile -->
      <div class="stack ba-border border-radius-8 bg-white p-md" data-gap="sm">
        <h3 class="km-h3">Profile</h3>
        <div class="cluster" data-gap="md" data-wrap="yes">
          <div class="stack" data-gap="xs">
            <span class="km-description text-grey">User ID</span>
            <span class="font-mono">{{ user.id }}</span>
          </div>
          <div v-if="user.tenant_id" class="stack" data-gap="xs">
            <span class="km-description text-grey">Tenant ID</span>
            <span class="font-mono">{{ user.tenant_id }}</span>
          </div>
          <div v-if="user.last_login_at" class="stack" data-gap="xs">
            <span class="km-description text-grey">Last login</span>
            <span>{{ formatDateTime(user.last_login_at as string) }}</span>
          </div>
        </div>
      </div>

      <!-- Role assignment -->
      <div class="stack ba-border border-radius-8 bg-white p-md" data-gap="sm">
        <div class="cluster" data-justify="between" data-align="center" data-wrap="no">
          <h3 class="km-h3">Roles</h3>
          <div class="cluster" data-gap="sm" data-wrap="no">
            <span v-if="isDirty" class="km-description text-grey">
              {{ pendingAdd }} to add · {{ pendingRemove }} to remove
            </span>
            <km-btn
              v-if="canManageUsers"
              label="Save"
              data-test="save-user-roles-btn"
              :disabled="!isDirty || saveMutation.isLoading.value"
              @click="save"
            />
            <km-btn
              v-if="canManageUsers && isDirty"
              flat
              label="Reset"
              @click="resetSelection"
            />
          </div>
        </div>
        <km-banner v-if="!canManageUsers" rounded dense>
          <template #avatar>
            <km-glyph name="info" size="16px" />
          </template>
          <span class="km-description">
            Read-only — the <span class="font-mono">manage:users</span> permission is required to edit role assignments.
          </span>
        </km-banner>
        <div class="stack" data-gap="sm">
          <label
            v-for="r in availableRoles"
            :key="r.id"
            class="cluster ba-border border-radius-6 p-sm"
            data-gap="sm"
            data-align="center"
            data-wrap="no"
            :class="{ 'role-row--checked': selectedRoleIds.has(r.id) }"
            :style="canManageUsers ? 'cursor: pointer' : ''"
          >
            <km-checkbox
              :model-value="selectedRoleIds.has(r.id)"
              :disable="!canManageUsers"
              data-test="role-toggle"
              @update:model-value="toggleRole(r.id)"
            />
            <km-glyph
              :name="r.is_system ? 'shield-check' : 'user'"
              size="14px"
              :tone="r.is_system ? 'brand' : 'neutral'"
            />
            <div class="stack flex-1" data-gap="xs">
              <span class="km-title">{{ r.name }}</span>
              <span class="km-description text-grey font-mono">{{ r.slug }}</span>
            </div>
            <km-chip
              :tone="r.is_system ? 'brand' : 'muted'"
              size="sm"
              :label="r.is_system ? 'system' : 'custom'"
            />
            <span class="km-description text-grey">{{ r.permissions.length }} perm</span>
          </label>
          <km-banner v-if="!availableRoles.length" rounded dense>
            <span class="km-description">No roles available in this tenant.</span>
          </km-banner>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { formatDateTime } from '@shared/utils'
import { usePermissions } from '@shared'
import { useSafeMutation } from '@/composables/useSafeMutation'
import {
  getUser,
  listRoles,
  patchUserRoles,
  type AdminUser,
  type RoleSummary,
} from '@/api/adminAccess'

const route = useRoute()
const queryClient = useQueryClient()
const { can } = usePermissions()

const userId = computed(() => String(route.params.id))

const userQuery = useQuery({
  queryKey: computed(() => ['admin', 'users', userId.value]),
  queryFn: () => getUser(userId.value),
  enabled: computed(() => Boolean(userId.value) && userId.value !== 'undefined'),
})
const rolesQuery = useQuery({
  queryKey: ['admin', 'roles'],
  queryFn: () => listRoles(),
})

const user = computed<AdminUser | null>(() => userQuery.data.value ?? null)
const allRoles = computed<RoleSummary[]>(() => rolesQuery.data.value ?? [])
const loading = computed(() => userQuery.isLoading.value || rolesQuery.isLoading.value)

const canManageUsers = computed(() => can('manage:users'))

const availableRoles = computed(() =>
  allRoles.value.slice().sort((a, b) => {
    if (a.is_system !== b.is_system) return a.is_system ? -1 : 1
    return a.slug.localeCompare(b.slug)
  }),
)

const selectedRoleIds = ref<Set<string>>(new Set())
const initialRoleIds = ref<Set<string>>(new Set())

/** Re-hydrate selection state when either query updates. */
watch(
  [user, allRoles],
  ([u, roles]) => {
    if (!u || !roles.length) return
    const assignedSlugs = new Set((u.roles ?? []) as string[])
    const ids = new Set(
      roles.filter((r) => assignedSlugs.has(r.slug)).map((r) => r.id),
    )
    selectedRoleIds.value = new Set(ids)
    initialRoleIds.value = new Set(ids)
  },
  { immediate: true },
)

const isDirty = computed(() => {
  if (selectedRoleIds.value.size !== initialRoleIds.value.size) return true
  for (const id of selectedRoleIds.value) {
    if (!initialRoleIds.value.has(id)) return true
  }
  return false
})

const pendingAdd = computed(() => {
  let n = 0
  for (const id of selectedRoleIds.value) {
    if (!initialRoleIds.value.has(id)) n++
  }
  return n
})

const pendingRemove = computed(() => {
  let n = 0
  for (const id of initialRoleIds.value) {
    if (!selectedRoleIds.value.has(id)) n++
  }
  return n
})

function toggleRole(id: string) {
  if (!canManageUsers.value) return
  const next = new Set(selectedRoleIds.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  selectedRoleIds.value = next
}

function resetSelection() {
  selectedRoleIds.value = new Set(initialRoleIds.value)
}

const errorMessage = ref<string | null>(null)

const saveMutation = useSafeMutation(
  useMutation({
    mutationFn: (args: { id: string; add: string[]; remove: string[] }) =>
      patchUserRoles(args.id, { add: args.add, remove: args.remove }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'users', userId.value] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'roles'] })
    },
  }),
  {
    successMessage: 'Roles updated.',
    onError: (err) => {
      errorMessage.value = err.message
      return false
    },
  },
)

async function save() {
  if (!user.value || !isDirty.value) return
  errorMessage.value = null
  const add: string[] = []
  const remove: string[] = []
  for (const id of selectedRoleIds.value) {
    if (!initialRoleIds.value.has(id)) add.push(id)
  }
  for (const id of initialRoleIds.value) {
    if (!selectedRoleIds.value.has(id)) remove.push(id)
  }
  await saveMutation.run({ id: user.value.id, add, remove })
}
</script>

<style scoped>
.role-row--checked {
  background: var(--km-color-bg-subtle, rgba(0, 0, 0, 0.02));
}
</style>
