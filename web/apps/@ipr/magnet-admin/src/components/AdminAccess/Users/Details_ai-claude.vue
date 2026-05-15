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

    <div v-if="error" class="bg-error-bg p-md border-radius-6">
      <div class="text-error">{{ error }}</div>
    </div>

    <div v-if="loading" class="km-description text-grey p-md">Loading…</div>

    <template v-else-if="user">
      <!-- Identity / profile block -->
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
            <span>{{ formatDate(user.last_login_at) }}</span>
          </div>
        </div>
      </div>

      <!-- Role assignment -->
      <div class="stack ba-border border-radius-8 bg-white p-md" data-gap="sm">
        <div class="cluster" data-justify="between" data-align="center" data-wrap="no">
          <h3 class="km-h3">Roles</h3>
          <km-btn
            v-if="canManageUsers"
            label="Save"
            :disabled="!isDirty || saving"
            @click="save"
          />
        </div>
        <div v-if="!canManageUsers" class="km-description text-grey">
          Read-only — `manage:users` permission required to edit.
        </div>
        <div class="stack" data-gap="sm">
          <label
            v-for="r in availableRoles"
            :key="r.id"
            class="cluster ba-border border-radius-6 p-sm"
            data-gap="sm"
            data-align="center"
            data-wrap="no"
          >
            <input
              type="checkbox"
              :checked="selectedRoleIds.has(r.id)"
              :disabled="!canManageUsers"
              @change="toggleRole(r.id)"
            >
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
          <div v-if="!availableRoles.length" class="km-description text-grey">
            No roles available.
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { usePermissions } from '@shared'
import {
  getUser,
  listRoles,
  patchUserRoles,
  type AdminUser,
  type RoleSummary,
} from '@/api/adminAccess_ai-claude'

const route = useRoute()
const { can } = usePermissions()

const user = ref<AdminUser | null>(null)
const allRoles = ref<RoleSummary[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const saving = ref(false)

/** Role IDs currently selected (live state). */
const selectedRoleIds = ref<Set<string>>(new Set())
/** Snapshot of role IDs at load time for dirty / patch-diff. */
const initialRoleIds = ref<Set<string>>(new Set())

const canManageUsers = computed(() => can('manage:users'))

const availableRoles = computed(() =>
  allRoles.value.slice().sort((a, b) => {
    if (a.is_system !== b.is_system) return a.is_system ? -1 : 1
    return a.slug.localeCompare(b.slug)
  }),
)

const isDirty = computed(() => {
  if (selectedRoleIds.value.size !== initialRoleIds.value.size) return true
  for (const id of selectedRoleIds.value) {
    if (!initialRoleIds.value.has(id)) return true
  }
  return false
})

async function load() {
  loading.value = true
  error.value = null
  try {
    const id = String(route.params.id)
    const [u, roles] = await Promise.all([getUser(id), listRoles()])
    user.value = u
    allRoles.value = roles
    // Match assigned role slugs back to role IDs via the catalog.
    const assignedSlugs = new Set((u.roles ?? []) as string[])
    const ids = new Set(
      roles.filter((r) => assignedSlugs.has(r.slug)).map((r) => r.id),
    )
    selectedRoleIds.value = new Set(ids)
    initialRoleIds.value = new Set(ids)
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

function toggleRole(id: string) {
  const next = new Set(selectedRoleIds.value)
  if (next.has(id)) {
    next.delete(id)
  } else {
    next.add(id)
  }
  selectedRoleIds.value = next
}

async function save() {
  if (!user.value || !isDirty.value) return
  saving.value = true
  error.value = null
  try {
    const add: string[] = []
    const remove: string[] = []
    for (const id of selectedRoleIds.value) {
      if (!initialRoleIds.value.has(id)) add.push(id)
    }
    for (const id of initialRoleIds.value) {
      if (!selectedRoleIds.value.has(id)) remove.push(id)
    }
    await patchUserRoles(user.value.id, { add, remove })
    await load()
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    saving.value = false
  }
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

onMounted(load)
</script>
