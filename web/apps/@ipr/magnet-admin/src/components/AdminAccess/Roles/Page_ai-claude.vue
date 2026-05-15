<template>
  <div class="stack p-md height-100 width-100" data-gap="md">
    <div class="cluster" data-align="center" data-justify="between" data-wrap="no">
      <div class="stack" data-gap="xs">
        <h2 class="km-h2">Roles</h2>
        <div class="km-description text-grey">
          System roles are shared and immutable. Custom roles are scoped to your tenant.
        </div>
      </div>
      <km-btn
        v-if="canWriteRoles"
        icon="add-square"
        label="New role"
        @click="openCreateDialog"
      />
    </div>

    <div v-if="error" class="bg-error-bg p-md border-radius-6">
      <div class="text-error">{{ error }}</div>
    </div>

    <div v-if="loading" class="km-description text-grey p-md">Loading…</div>

    <div v-else class="stack ba-border border-radius-8 bg-white" data-gap="0">
      <div
        v-for="role in roles"
        :key="role.id"
        class="cluster p-md bb-border"
        data-align="center"
        data-wrap="no"
        data-test="role-row"
        style="cursor: pointer"
        @click="openRole(role.id)"
      >
        <km-glyph
          class="mr-sm"
          :name="role.is_system ? 'shield-check' : 'user'"
          size="18px"
          :tone="role.is_system ? 'brand' : 'neutral'"
        />
        <div class="stack flex-1" data-gap="xs">
          <div class="cluster" data-gap="sm" data-align="center" data-wrap="no">
            <span class="km-title">{{ role.name }}</span>
            <km-chip
              :tone="role.is_system ? 'brand' : 'muted'"
              size="sm"
              :label="role.is_system ? 'system' : 'custom'"
            />
          </div>
          <div class="km-description text-grey">
            <span class="font-mono">{{ role.slug }}</span>
            <span v-if="role.description"> · {{ role.description }}</span>
          </div>
        </div>
        <div class="cluster" data-gap="md" data-wrap="no" data-align="center">
          <span class="km-description text-grey">
            {{ role.permissions.length }} perm
          </span>
          <span class="km-description text-grey">
            {{ role.user_count }} user{{ role.user_count === 1 ? '' : 's' }}
          </span>
          <km-glyph name="chevron-right" size="16px" />
        </div>
      </div>
      <div v-if="!roles.length" class="km-description text-grey p-md">
        No roles found.
      </div>
    </div>

    <!-- Create dialog -->
    <km-dialog v-if="showCreate" v-model="showCreate" title="New custom role">
      <div class="stack p-md" data-gap="md">
        <div class="stack" data-gap="xs">
          <label class="km-description">Slug</label>
          <km-input v-model="newSlug" placeholder="reviewer" />
        </div>
        <div class="stack" data-gap="xs">
          <label class="km-description">Name</label>
          <km-input v-model="newName" placeholder="Reviewer" />
        </div>
        <div class="stack" data-gap="xs">
          <label class="km-description">Description (optional)</label>
          <km-input v-model="newDescription" placeholder="Can review submissions" />
        </div>
        <div v-if="createError" class="text-error">{{ createError }}</div>
        <div class="cluster" data-justify="end" data-gap="sm" data-wrap="no">
          <km-btn label="Cancel" flat @click="showCreate = false" />
          <km-btn
            label="Create"
            :disabled="!newSlug || !newName || creating"
            @click="submitCreate"
          />
        </div>
      </div>
    </km-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { usePermissions } from '@shared'
import { listRoles, createRole, type RoleSummary } from '@/api/adminAccess_ai-claude'

const router = useRouter()
const { can } = usePermissions()

const roles = ref<RoleSummary[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const canWriteRoles = computed(() => can('write:roles'))

const showCreate = ref(false)
const newSlug = ref('')
const newName = ref('')
const newDescription = ref('')
const creating = ref(false)
const createError = ref<string | null>(null)

async function load() {
  loading.value = true
  error.value = null
  try {
    roles.value = await listRoles()
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

function openCreateDialog() {
  newSlug.value = ''
  newName.value = ''
  newDescription.value = ''
  createError.value = null
  showCreate.value = true
}

async function submitCreate() {
  creating.value = true
  createError.value = null
  try {
    const created = await createRole({
      slug: newSlug.value.trim(),
      name: newName.value.trim(),
      description: newDescription.value.trim() || null,
      permissions: [],
    })
    showCreate.value = false
    await router.push(`/admin/roles/${created.id}`)
  } catch (e) {
    createError.value = e instanceof Error ? e.message : String(e)
  } finally {
    creating.value = false
  }
}

function openRole(id: string) {
  router.push(`/admin/roles/${id}`)
}

onMounted(load)
</script>
