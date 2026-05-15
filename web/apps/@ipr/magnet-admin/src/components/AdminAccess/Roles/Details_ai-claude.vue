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
          v-if="canEdit"
          label="Save"
          :disabled="!isDirty || saving"
          @click="save"
        />
        <km-btn
          v-if="canDelete"
          icon="trash"
          flat
          interaction-tone="negative"
          label="Delete"
          :disabled="deleting"
          @click="confirmDelete"
        />
      </div>
    </div>

    <div v-if="error" class="bg-error-bg p-md border-radius-6">
      <div class="text-error">{{ error }}</div>
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
        <admin-access-permission-matrix
          v-model="permissionCodes"
          :catalog="catalog"
          :readonly="!canEdit"
        />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePermissions } from '@shared'
import {
  getRole,
  updateRole,
  replaceRolePermissions,
  deleteRole,
  listPermissions,
  type RoleSummary,
  type PermissionEntry,
} from '@/api/adminAccess_ai-claude'
import AdminAccessPermissionMatrix from '@/components/AdminAccess/PermissionMatrix_ai-claude.vue'

const route = useRoute()
const router = useRouter()
const { can } = usePermissions()

const role = ref<RoleSummary | null>(null)
const catalog = ref<PermissionEntry[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const saving = ref(false)
const deleting = ref(false)

const editName = ref('')
const editDescription = ref('')
const permissionCodes = ref<string[]>([])

// Snapshot for dirty detection.
const initialName = ref('')
const initialDescription = ref('')
const initialPermissions = ref<string[]>([])

const canEdit = computed(() => can('write:roles') && role.value !== null && !role.value.is_system)
const canDelete = computed(() => canEdit.value && (role.value?.user_count ?? 0) === 0)

const isDirty = computed(() => {
  if (!role.value) return false
  if (editName.value !== initialName.value) return true
  if ((editDescription.value || '') !== (initialDescription.value || '')) return true
  const a = [...permissionCodes.value].sort()
  const b = [...initialPermissions.value].sort()
  if (a.length !== b.length) return true
  return a.some((code, i) => code !== b[i])
})

async function load() {
  loading.value = true
  error.value = null
  try {
    const id = String(route.params.id)
    const [r, cat] = await Promise.all([getRole(id), listPermissions()])
    role.value = r
    catalog.value = cat
    editName.value = r.name
    editDescription.value = r.description ?? ''
    permissionCodes.value = [...r.permissions]
    initialName.value = r.name
    initialDescription.value = r.description ?? ''
    initialPermissions.value = [...r.permissions]
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

async function save() {
  if (!role.value || !isDirty.value) return
  saving.value = true
  error.value = null
  try {
    const id = role.value.id
    // 1) Update metadata if changed
    const metadataChanged =
      editName.value !== initialName.value ||
      (editDescription.value || '') !== (initialDescription.value || '')
    if (metadataChanged) {
      await updateRole(id, {
        name: editName.value,
        description: editDescription.value || null,
      })
    }
    // 2) Replace permission set if changed
    const permsChanged = !arraysEqual(permissionCodes.value, initialPermissions.value)
    if (permsChanged) {
      await replaceRolePermissions(id, permissionCodes.value)
    }
    await load()
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    saving.value = false
  }
}

async function confirmDelete() {
  if (!role.value) return
  if (!window.confirm(`Delete role "${role.value.name}"? This cannot be undone.`)) {
    return
  }
  deleting.value = true
  error.value = null
  try {
    await deleteRole(role.value.id)
    router.push('/admin/roles')
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
    deleting.value = false
  }
}

function arraysEqual(a: string[], b: string[]): boolean {
  if (a.length !== b.length) return false
  const sa = [...a].sort()
  const sb = [...b].sort()
  return sa.every((v, i) => v === sb[i])
}

onMounted(load)
</script>

<style scoped>
.min-w-200 {
  min-inline-size: 200px;
}
</style>
