<template>
  <div class="stack p-md height-100 width-100" data-gap="md">
    <div class="cluster" data-align="center" data-wrap="no" data-gap="sm">
      <km-btn icon="arrow-left" flat label="Back" @click="$router.push('/admin/roles')" />
      <div class="stack flex-1" data-gap="xs">
        <div class="cluster" data-align="center" data-gap="sm" data-wrap="no">
          <h2 class="km-h2">{{ role?.name || 'Role' }}</h2>
          <km-chip
            v-if="role"
            :tone="role.is_system ? 'brand' : 'muted'"
            size="sm"
            :label="role.is_system ? 'system' : 'custom'"
          />
        </div>
        <div v-if="role" class="km-description text-grey font-mono">{{ role.slug }}</div>
      </div>
      <div class="cluster" data-gap="sm" data-wrap="no">
        <km-btn
          v-if="role?.is_system && canWriteRoles"
          icon="copy"
          label="Duplicate as custom"
          data-test="duplicate-role-btn"
          @click="duplicateAsCustom"
        />
        <km-btn
          v-if="canEdit"
          label="Save"
          data-test="save-role-btn"
          :disabled="!isDirty || saveMutation.isLoading.value"
          @click="save"
        />
        <km-btn
          v-if="canDelete"
          icon="trash"
          flat
          interaction-tone="danger"
          label="Delete"
          :disabled="deleteMutation.isLoading.value"
          @click="confirmDelete"
        />
      </div>
    </div>

    <km-banner v-if="role?.is_system" rounded dense>
      <template #avatar>
        <km-glyph name="info" size="18px" tone="brand" />
      </template>
      <div class="stack" data-gap="xs">
        <strong>System role — managed by the platform.</strong>
        <span class="km-description">
          Name, description and permissions can't be changed here. Use
          <em>Duplicate as custom</em> to fork this role into an editable tenant copy.
        </span>
      </div>
    </km-banner>

    <div v-if="errorMessage" class="bg-error-bg p-md border-radius-6">
      <div class="text-error">{{ errorMessage }}</div>
    </div>

    <div v-if="loading" class="km-description text-grey p-md">Loading…</div>

    <template v-else-if="role">
      <div class="stack ba-border border-radius-8 bg-white p-md" data-gap="md">
        <div class="cluster" data-gap="md" data-wrap="yes">
          <div class="stack flex-1 min-w-200" data-gap="xs">
            <label class="km-description">Name</label>
            <km-input
              v-model="editName"
              :disabled="!canEdit"
              placeholder="Reviewer"
            />
          </div>
          <div class="stack flex-1 min-w-200" data-gap="xs">
            <label class="km-description">Description</label>
            <km-input
              v-model="editDescription"
              :disabled="!canEdit"
              placeholder="Optional"
            />
          </div>
        </div>
        <div class="cluster" data-gap="md" data-wrap="yes">
          <div class="cluster" data-gap="xs" data-align="center" data-wrap="no">
            <km-glyph name="users" size="14px" />
            <span class="km-description">{{ role.user_count }} user{{ role.user_count === 1 ? '' : 's' }} assigned</span>
          </div>
          <div class="cluster" data-gap="xs" data-align="center" data-wrap="no">
            <km-glyph name="shield-check" size="14px" />
            <span class="km-description">{{ permissionCodes.length }} permissions</span>
          </div>
        </div>
      </div>

      <div class="stack" data-gap="sm">
        <h3 class="km-h3">Permissions</h3>
        <div v-if="!catalog.length" class="km-description text-grey p-md">
          Loading permission catalog…
        </div>
        <admin-access-permission-matrix
          v-else
          v-model="permissionCodes"
          :catalog="catalog"
          :readonly="!canEdit"
        />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { usePermissions } from '@shared'
import { useSafeMutation } from '@/composables/useSafeMutation'
import {
  getRole,
  updateRole,
  replaceRolePermissions,
  deleteRole,
  listPermissions,
  createRole,
  type RoleSummary,
  type PermissionEntry,
  type RoleUpdatePayload,
} from '@/api/adminAccess'
import AdminAccessPermissionMatrix from '@/components/AdminAccess/PermissionMatrix.vue'

const route = useRoute()
const router = useRouter()
const queryClient = useQueryClient()
const { can } = usePermissions()

const roleId = computed(() => String(route.params.id))

const roleQuery = useQuery({
  queryKey: computed(() => ['admin', 'roles', roleId.value]),
  queryFn: () => getRole(roleId.value),
  enabled: computed(() => Boolean(roleId.value) && roleId.value !== 'undefined'),
})
const catalogQuery = useQuery({
  queryKey: ['admin', 'permissions-catalog'],
  queryFn: () => listPermissions(),
  staleTime: 5 * 60_000,
})

const role = computed<RoleSummary | null>(() => roleQuery.data.value ?? null)
const catalog = computed<PermissionEntry[]>(() => catalogQuery.data.value ?? [])
const loading = computed(() => roleQuery.isLoading.value || catalogQuery.isLoading.value)

const canWriteRoles = computed(() => can('write:roles'))
const canEdit = computed(
  () => canWriteRoles.value && role.value !== null && !role.value.is_system,
)
const canDelete = computed(
  () => canEdit.value && (role.value?.user_count ?? 0) === 0,
)

// ── Edit state, hydrated from the query ───────────────────────────────
const editName = ref('')
const editDescription = ref('')
const permissionCodes = ref<string[]>([])
const initialName = ref('')
const initialDescription = ref('')
const initialPermissions = ref<string[]>([])

watch(
  role,
  (r) => {
    if (!r) return
    const perms = Array.isArray(r.permissions) ? r.permissions : []
    editName.value = r.name ?? ''
    editDescription.value = r.description ?? ''
    permissionCodes.value = [...perms]
    initialName.value = r.name ?? ''
    initialDescription.value = r.description ?? ''
    initialPermissions.value = [...perms]
  },
  { immediate: true },
)

const isDirty = computed(() => {
  if (!role.value) return false
  if (editName.value !== initialName.value) return true
  if ((editDescription.value || '') !== (initialDescription.value || '')) return true
  const a = [...permissionCodes.value].sort()
  const b = [...initialPermissions.value].sort()
  if (a.length !== b.length) return true
  return a.some((code, i) => code !== b[i])
})

function arraysEqual(a: string[], b: string[]): boolean {
  if (a.length !== b.length) return false
  const sa = [...a].sort()
  const sb = [...b].sort()
  return sa.every((v, i) => v === sb[i])
}

// ── Mutations ─────────────────────────────────────────────────────────
const errorMessage = ref<string | null>(null)

const saveMutation = useSafeMutation(
  useMutation({
    mutationFn: async (args: {
      id: string
      metaChanged: boolean
      permsChanged: boolean
      meta: RoleUpdatePayload
      perms: string[]
    }) => {
      if (args.metaChanged) {
        await updateRole(args.id, args.meta)
      }
      if (args.permsChanged) {
        await replaceRolePermissions(args.id, args.perms)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'roles'] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'roles', roleId.value] })
    },
  }),
  {
    successMessage: 'Role saved.',
    onError: (err) => {
      errorMessage.value = err.message
      return false
    },
  },
)

const deleteMutation = useSafeMutation(
  useMutation({
    mutationFn: (id: string) => deleteRole(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'roles'] })
    },
  }),
  { successMessage: 'Role deleted.' },
)

const duplicateMutation = useSafeMutation(
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
  { successMessage: 'Custom role created.' },
)

async function save() {
  if (!role.value || !isDirty.value) return
  errorMessage.value = null
  const metaChanged =
    editName.value !== initialName.value ||
    (editDescription.value || '') !== (initialDescription.value || '')
  const permsChanged = !arraysEqual(permissionCodes.value, initialPermissions.value)
  if (!metaChanged && !permsChanged) return
  await saveMutation.run({
    id: role.value.id,
    metaChanged,
    permsChanged,
    meta: { name: editName.value, description: editDescription.value || null },
    perms: permissionCodes.value,
  })
}

async function confirmDelete() {
  if (!role.value) return
  if (!window.confirm(`Delete role "${role.value.name}"? This cannot be undone.`)) {
    return
  }
  const { success } = await deleteMutation.run(role.value.id)
  if (success) {
    router.push('/admin/roles')
  }
}

async function duplicateAsCustom() {
  if (!role.value) return
  const base = role.value
  // Suggest a slug that isn't one of the reserved system ones.
  const suggestedSlug = `${base.slug}-copy`
  const slug = window.prompt('Slug for the new custom role:', suggestedSlug)?.trim()
  if (!slug) return
  if (['admin', 'user', 'viewer'].includes(slug)) {
    errorMessage.value = `Slug '${slug}' is reserved for system roles.`
    return
  }
  const { success, data } = await duplicateMutation.run({
    slug,
    name: `${base.name} (copy)`,
    description: base.description ?? null,
    permissions: [...base.permissions],
  })
  if (success && data) {
    router.push(`/admin/roles/${data.id}`)
  }
}
</script>

<style scoped>
.min-w-200 {
  min-inline-size: 200px;
}
</style>
