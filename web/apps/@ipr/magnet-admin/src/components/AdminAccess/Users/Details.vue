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
            <span class="km-description text-grey">Tenant</span>
            <div class="cluster" data-gap="sm" data-align="center" data-wrap="no">
              <span class="font-mono">{{ currentTenantLabel }}</span>
              <km-btn
                v-if="isSuperuser"
                flat
                size="sm"
                label="Change"
                data-test="change-tenant-btn"
                @click="openTenantDialog"
              />
            </div>
          </div>
          <div v-if="user.last_login_at" class="stack" data-gap="xs">
            <span class="km-description text-grey">Last login</span>
            <span>{{ formatDateTime(user.last_login_at as string) }}</span>
          </div>
        </div>
      </div>

      <!-- Departments -->
      <div class="stack ba-border border-radius-8 bg-white p-md" data-gap="sm">
        <div class="cluster" data-justify="between" data-align="center" data-wrap="no">
          <h3 class="km-h3">Departments</h3>
          <div class="cluster" data-gap="sm" data-wrap="no">
            <span v-if="deptDirty" class="km-description text-grey">unsaved changes</span>
            <km-btn
              v-if="canManageUsers"
              label="Save"
              data-test="save-user-depts-btn"
              :disabled="!deptDirty || saveDeptMutation.isLoading.value"
              @click="saveDepartments"
            />
            <km-btn
              v-if="canManageUsers && deptDirty"
              flat
              label="Reset"
              @click="resetDepartments"
            />
          </div>
        </div>
        <km-banner v-if="!canManageUsers" rounded dense>
          <template #avatar>
            <km-glyph name="info" size="16px" />
          </template>
          <span class="km-description">
            Read-only — <span class="font-mono">manage:users</span> required to edit department memberships.
          </span>
        </km-banner>
        <div v-if="!availableDepartments.length" class="km-description text-grey p-sm">
          No departments defined for this tenant yet.
        </div>
        <div v-else class="stack" data-gap="sm">
          <label
            v-for="d in availableDepartments"
            :key="d.id"
            class="cluster ba-border border-radius-6 p-sm"
            data-gap="sm"
            data-align="center"
            data-wrap="no"
            :class="{ 'role-row--checked': deptSelection.has(d.id) }"
            :style="canManageUsers ? 'cursor: pointer' : ''"
          >
            <km-checkbox
              :model-value="deptSelection.has(d.id)"
              :disable="!canManageUsers"
              @update:model-value="toggleDept(d.id)"
            />
            <div class="stack flex-1" data-gap="xs">
              <span class="km-title">{{ d.name }}</span>
              <span class="km-description text-grey font-mono">{{ d.slug }}</span>
            </div>
            <km-chip v-if="deptSelection.has(d.id) && deptLeads.has(d.id)" tone="brand" size="sm" label="lead" />
            <km-btn
              v-if="canManageUsers && deptSelection.has(d.id)"
              flat
              size="sm"
              :label="deptLeads.has(d.id) ? 'Demote' : 'Make lead'"
              @click.prevent="toggleLead(d.id)"
            />
          </label>
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

    <km-dialog v-if="showTenantDialog" v-model="showTenantDialog" title="Change tenant">
      <div class="stack p-md" data-gap="md">
        <div class="km-description text-grey">
          Moving the user wipes their role and department assignments from the
          current tenant.
        </div>
        <div class="stack" data-gap="xs">
          <label class="km-description">Target tenant</label>
          <select v-model="targetTenantId" class="km-input-native">
            <option value="">— select tenant —</option>
            <option
              v-for="t in tenantOptions"
              :key="t.id"
              :value="t.id"
              :disabled="t.id === user?.tenant_id"
            >
              {{ t.name }} ({{ t.slug }})
            </option>
          </select>
        </div>
        <div class="cluster" data-justify="end" data-gap="sm" data-wrap="no">
          <km-btn label="Cancel" flat @click="showTenantDialog = false" />
          <km-btn
            label="Move"
            :disabled="!targetTenantId || moveTenantMutation.isLoading.value"
            @click="submitTenantChange"
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
import { usePermissions } from '@shared'
import { useSharedAuthStore } from '@shared/stores/authStore'
import { useSafeMutation } from '@/composables/useSafeMutation'
import {
  getUser,
  listRoles,
  patchUserRoles,
  type AdminUser,
  type RoleSummary,
} from '@/api/adminAccess'
import {
  listDepartments,
  listUserDepartments,
  replaceUserDepartments,
  type AdminDepartment,
  type UserDepartmentMembership,
} from '@/api/departments'
import { listTenants, moveUserToTenant, type AdminTenant } from '@/api/tenants'

const route = useRoute()
const queryClient = useQueryClient()
const { can } = usePermissions()
const authStore = useSharedAuthStore()
const isSuperuser = computed(() => Boolean(authStore.userInfo?.is_superuser))

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

// ── Departments ────────────────────────────────────────────────────────
const deptListQuery = useQuery({
  queryKey: ['admin', 'departments'],
  queryFn: () => listDepartments(),
})
const userDeptQuery = useQuery({
  queryKey: computed(() => ['admin', 'users', userId.value, 'departments']),
  queryFn: () => listUserDepartments(userId.value),
  enabled: computed(() => Boolean(userId.value) && userId.value !== 'undefined'),
})

const availableDepartments = computed<AdminDepartment[]>(
  () => deptListQuery.data.value ?? [],
)
const userMemberships = computed<UserDepartmentMembership[]>(
  () => userDeptQuery.data.value ?? [],
)

const deptSelection = ref<Set<string>>(new Set())
const deptLeads = ref<Set<string>>(new Set())
const initialDeptSelection = ref<Set<string>>(new Set())
const initialDeptLeads = ref<Set<string>>(new Set())

watch(
  userMemberships,
  (memberships) => {
    deptSelection.value = new Set(memberships.map((m) => m.department_id))
    deptLeads.value = new Set(
      memberships.filter((m) => m.is_lead).map((m) => m.department_id),
    )
    initialDeptSelection.value = new Set(deptSelection.value)
    initialDeptLeads.value = new Set(deptLeads.value)
  },
  { immediate: true },
)

const deptDirty = computed(() => {
  if (deptSelection.value.size !== initialDeptSelection.value.size) return true
  for (const id of deptSelection.value) {
    if (!initialDeptSelection.value.has(id)) return true
  }
  if (deptLeads.value.size !== initialDeptLeads.value.size) return true
  for (const id of deptLeads.value) {
    if (!initialDeptLeads.value.has(id)) return true
  }
  return false
})

function toggleDept(id: string) {
  if (!canManageUsers.value) return
  const next = new Set(deptSelection.value)
  const leads = new Set(deptLeads.value)
  if (next.has(id)) {
    next.delete(id)
    leads.delete(id)
  } else {
    next.add(id)
  }
  deptSelection.value = next
  deptLeads.value = leads
}

function toggleLead(id: string) {
  if (!canManageUsers.value) return
  if (!deptSelection.value.has(id)) return
  const next = new Set(deptLeads.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  deptLeads.value = next
}

function resetDepartments() {
  deptSelection.value = new Set(initialDeptSelection.value)
  deptLeads.value = new Set(initialDeptLeads.value)
}

const saveDeptMutation = useSafeMutation(
  useMutation({
    mutationFn: (args: { id: string; memberships: { department_id: string; is_lead: boolean }[] }) =>
      replaceUserDepartments(args.id, args.memberships),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users', userId.value, 'departments'] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'departments'] })
    },
  }),
  { successMessage: 'Department memberships updated.' },
)

async function saveDepartments() {
  if (!user.value || !deptDirty.value) return
  const memberships = Array.from(deptSelection.value).map((id) => ({
    department_id: id,
    is_lead: deptLeads.value.has(id),
  }))
  await saveDeptMutation.run({ id: user.value.id, memberships })
}

// ── Tenant change (superuser) ─────────────────────────────────────────
const showTenantDialog = ref(false)
const targetTenantId = ref('')

const tenantsQuery = useQuery({
  queryKey: ['admin', 'tenants'],
  queryFn: () => listTenants(),
  enabled: computed(() => isSuperuser.value && showTenantDialog.value),
})
const tenantOptions = computed<AdminTenant[]>(() => tenantsQuery.data.value ?? [])

const currentTenantLabel = computed(() => {
  if (!user.value?.tenant_id) return ''
  const match = tenantOptions.value.find((t) => t.id === user.value?.tenant_id)
  return match ? `${match.name} (${match.slug})` : user.value.tenant_id
})

function openTenantDialog() {
  targetTenantId.value = ''
  showTenantDialog.value = true
}

const moveTenantMutation = useSafeMutation(
  useMutation({
    mutationFn: (args: { userId: string; tenantId: string }) =>
      moveUserToTenant(args.userId, args.tenantId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'users', userId.value] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'users', userId.value, 'departments'] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'tenants'] })
    },
  }),
  { successMessage: 'User moved to new tenant.' },
)

async function submitTenantChange() {
  if (!user.value || !targetTenantId.value) return
  const { success } = await moveTenantMutation.run({
    userId: user.value.id,
    tenantId: targetTenantId.value,
  })
  if (success) {
    showTenantDialog.value = false
  }
}
</script>

<style scoped>
.role-row--checked {
  background: var(--km-color-bg-subtle, rgba(0, 0, 0, 0.02));
}
.km-input-native {
  padding: 6px 10px;
  border: 1px solid var(--km-color-border, #d0d3da);
  border-radius: 6px;
  font: inherit;
}
</style>
