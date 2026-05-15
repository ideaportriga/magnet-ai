<template>
  <div class="stack p-md height-100 width-100" data-gap="md">
    <div class="stack" data-gap="xs">
      <h2 class="km-h2">Users</h2>
      <div class="km-description text-grey">
        All users in your tenant. Click a row to manage their roles.
      </div>
    </div>

    <div class="cluster" data-align="center" data-gap="sm" data-wrap="no">
      <km-input
        v-model="search"
        placeholder="Search by name or email"
        icon-before="search"
        clearable
        style="max-inline-size: 320px"
      />
      <span class="km-description text-grey">{{ filtered.length }} of {{ users.length }}</span>
    </div>

    <div v-if="error" class="bg-error-bg p-md border-radius-6">
      <div class="text-error">{{ error }}</div>
    </div>

    <div v-if="loading" class="km-description text-grey p-md">Loading…</div>

    <div v-else class="stack ba-border border-radius-8 bg-white" data-gap="0">
      <div
        v-for="user in filtered"
        :key="user.id"
        class="cluster p-md bb-border"
        data-align="center"
        data-wrap="no"
        data-test="user-row"
        style="cursor: pointer"
        @click="openUser(user.id)"
      >
        <km-glyph class="mr-sm" name="user" size="18px" />
        <div class="stack flex-1" data-gap="xs">
          <div class="cluster" data-gap="sm" data-align="center" data-wrap="no">
            <span class="km-title">{{ user.name || user.email || user.preferred_username || user.id }}</span>
            <km-chip
              v-if="user.is_superuser"
              tone="brand"
              size="sm"
              label="superuser"
            />
            <km-chip
              v-if="user.is_active === false"
              tone="muted"
              size="sm"
              label="inactive"
            />
          </div>
          <div class="km-description text-grey">{{ user.email }}</div>
        </div>
        <div class="cluster" data-gap="sm" data-wrap="yes" style="max-inline-size: 50%">
          <km-chip
            v-for="slug in user.roles || []"
            :key="slug"
            tone="muted"
            size="sm"
            :label="slug"
          />
        </div>
        <km-glyph class="ml-sm" name="chevron-right" size="16px" />
      </div>
      <div v-if="!filtered.length" class="km-description text-grey p-md">
        No matching users.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { listUsers, type AdminUser } from '@/api/adminAccess_ai-claude'

const router = useRouter()
const users = ref<AdminUser[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const search = ref('')

async function load() {
  loading.value = true
  error.value = null
  try {
    users.value = await listUsers()
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

const filtered = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return users.value
  return users.value.filter((u) => {
    const haystack = `${u.name ?? ''} ${u.email ?? ''} ${u.preferred_username ?? ''}`.toLowerCase()
    return haystack.includes(q)
  })
})

function openUser(id: string) {
  router.push(`/admin/users/${id}`)
}

onMounted(load)
</script>
