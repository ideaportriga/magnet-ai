<template>
  <div class="stack p-md height-100 width-100" data-gap="md">
    <div class="cluster" data-align="center" data-gap="sm" data-wrap="no">
      <km-btn icon="arrow-left" flat label="Back" @click="$router.push('/admin/departments')" />
      <div class="stack flex-1" data-gap="xs">
        <h2 class="km-h2">{{ department?.name || 'Department' }}</h2>
        <div v-if="department" class="km-description text-grey font-mono">{{ department.slug }}</div>
      </div>
      <div class="cluster" data-gap="sm" data-wrap="no">
        <km-btn
          v-if="canManage"
          label="Save"
          data-test="save-department-btn"
          :disabled="!isDirty || saveMutation.isLoading.value"
          @click="save"
        />
        <km-btn
          v-if="canManage"
          icon="trash"
          flat
          interaction-tone="danger"
          label="Delete"
          :disabled="deleteMutation.isLoading.value"
          @click="confirmDelete"
        />
      </div>
    </div>

    <km-banner v-if="!canManage" rounded dense>
      <template #avatar>
        <km-glyph name="info" size="16px" />
      </template>
      <span class="km-description">
        Read-only — the <span class="font-mono">manage:users</span> permission is required to edit departments.
      </span>
    </km-banner>

    <div v-if="errorMessage" class="bg-error-bg p-md border-radius-6">
      <div class="text-error">{{ errorMessage }}</div>
    </div>

    <div v-if="loading" class="km-description text-grey p-md">Loading…</div>

    <template v-else-if="department">
      <!-- Department profile -->
      <div class="stack ba-border border-radius-8 bg-white p-md" data-gap="md">
        <h3 class="km-h3">Department</h3>
        <div class="cluster" data-gap="md" data-wrap="yes">
          <div class="stack flex-1 min-w-200" data-gap="xs">
            <label class="km-description">Slug</label>
            <km-input
              ref="slugRef"
              v-model="editSlug"
              :disabled="!canManage"
              placeholder="engineering"
              :max-length="100"
              :rules="[required(), validSlug()]"
            />
          </div>
          <div class="stack flex-1 min-w-200" data-gap="xs">
            <label class="km-description">Name</label>
            <km-input
              ref="nameRef"
              v-model="editName"
              :disabled="!canManage"
              placeholder="Engineering"
              :max-length="255"
              :rules="[required(), noInvisibleChars()]"
            />
          </div>
          <div class="stack flex-1 min-w-200" data-gap="xs">
            <label class="km-description">Parent department</label>
            <select v-model="editParentId" class="km-input" :disabled="!canManage">
              <option value="">— none —</option>
              <option
                v-for="d in parentOptions"
                :key="d.id"
                :value="d.id"
              >
                {{ d.name }} ({{ d.slug }})
              </option>
            </select>
          </div>
        </div>
      </div>

      <!-- Members -->
      <div class="stack ba-border border-radius-8 bg-white p-md" data-gap="sm">
        <div class="cluster" data-justify="between" data-align="center" data-wrap="no">
          <h3 class="km-h3">Members</h3>
          <km-btn
            v-if="canManage"
            icon="add"
            flat
            label="Add user"
            data-test="add-member-btn"
            @click="openAddMember"
          />
        </div>

        <div v-if="!members.length" class="km-description text-grey p-sm">
          No members yet.
        </div>

        <div v-else class="stack" data-gap="xs">
          <div
            v-for="m in members"
            :key="m.user_id"
            class="cluster ba-border border-radius-6 p-sm"
            data-gap="sm"
            data-align="center"
            data-wrap="no"
          >
            <km-glyph :name="m.is_lead ? 'shield-check' : 'user'" size="14px" :tone="m.is_lead ? 'brand' : 'neutral'" />
            <div class="stack flex-1" data-gap="xs">
              <span class="km-title">{{ m.name || m.email || m.user_id }}</span>
              <span v-if="m.email && m.email !== m.name" class="km-description text-grey">
                {{ m.email }}
              </span>
            </div>
            <km-chip v-if="m.is_lead" tone="brand" size="sm" label="lead" />
            <km-btn
              v-if="canManage"
              flat
              size="sm"
              :label="m.is_lead ? 'Demote' : 'Make lead'"
              @click="toggleLead(m)"
            />
            <km-btn
              v-if="canManage"
              icon="trash"
              flat
              size="sm"
              interaction-tone="danger"
              @click="confirmRemove(m)"
            />
          </div>
        </div>
      </div>
    </template>

    <km-dialog v-if="showAdd" v-model="showAdd" title="Add member">
      <div class="stack p-md" data-gap="md">
        <div class="stack" data-gap="xs">
          <label class="km-description">User</label>
          <select v-model="addUserId" class="km-input">
            <option value="">— select user —</option>
            <option
              v-for="u in addCandidates"
              :key="u.id"
              :value="u.id"
            >
              {{ u.name || u.email || u.id }}
            </option>
          </select>
        </div>
        <div class="cluster" data-gap="sm" data-align="center" data-wrap="no">
          <km-checkbox v-model="addAsLead" />
          <span class="km-description">Mark as department lead</span>
        </div>
        <div class="cluster" data-justify="end" data-gap="sm" data-wrap="no">
          <km-btn label="Cancel" flat @click="showAdd = false" />
          <km-btn
            label="Add"
            :disabled="!addUserId || addMutation.isLoading.value"
            @click="submitAdd"
          />
        </div>
      </div>
    </km-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { usePermissions } from '@shared'
import { useSafeMutation } from '@/composables/useSafeMutation'
import { required, validSlug, noInvisibleChars } from '@/utils/validationRules'
import { validateRef } from '@/utils/validateRef'
import {
  getDepartment,
  updateDepartment,
  deleteDepartment,
  listDepartments,
  addDepartmentMember,
  updateDepartmentMember,
  removeDepartmentMember,
  type AdminDepartmentDetail,
  type AdminDepartment,
  type DepartmentMember,
} from '@/api/departments'
import { listUsers, type AdminUser } from '@/api/adminAccess'

const route = useRoute()
const router = useRouter()
const queryClient = useQueryClient()
const { can } = usePermissions()
const canManage = computed(() => can('manage:users'))

const deptId = computed(() => String(route.params.id))

const deptQuery = useQuery({
  queryKey: computed(() => ['admin', 'departments', deptId.value]),
  queryFn: () => getDepartment(deptId.value),
  enabled: computed(() => Boolean(deptId.value) && deptId.value !== 'undefined'),
})
const listQuery = useQuery({
  queryKey: ['admin', 'departments'],
  queryFn: () => listDepartments(),
})
const usersQuery = useQuery({
  queryKey: ['admin', 'users'],
  queryFn: () => listUsers(),
})

const department = computed<AdminDepartmentDetail | null>(() => deptQuery.data.value ?? null)
const allDepartments = computed<AdminDepartment[]>(() => listQuery.data.value ?? [])
const allUsers = computed<AdminUser[]>(() => usersQuery.data.value ?? [])
const members = computed<DepartmentMember[]>(() => department.value?.members ?? [])
const loading = computed(() => deptQuery.isLoading.value)

const parentOptions = computed(() =>
  allDepartments.value.filter((d) => d.id !== deptId.value),
)

// ── Edit state ──
const editSlug = ref('')
const editName = ref('')
const editParentId = ref('')
const initial = ref({ slug: '', name: '', parent_id: '' })
const slugRef = ref<{ validate?: () => boolean } | null>(null)
const nameRef = ref<{ validate?: () => boolean } | null>(null)

watch(
  department,
  (d) => {
    if (!d) return
    editSlug.value = d.slug
    editName.value = d.name
    editParentId.value = d.parent_id ?? ''
    initial.value = { slug: d.slug, name: d.name, parent_id: d.parent_id ?? '' }
  },
  { immediate: true },
)

const isDirty = computed(
  () =>
    editSlug.value !== initial.value.slug ||
    editName.value !== initial.value.name ||
    editParentId.value !== initial.value.parent_id,
)

const errorMessage = ref<string | null>(null)

const saveMutation = useSafeMutation(
  useMutation({
    mutationFn: (args: { id: string; slug: string; name: string; parent_id: string | null }) =>
      updateDepartment(args.id, {
        slug: args.slug,
        name: args.name,
        parent_id: args.parent_id,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'departments'] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'departments', deptId.value] })
    },
  }),
  {
    successMessage: 'Department saved.',
    onError: (err) => {
      errorMessage.value = err.message
      return false
    },
  },
)

async function save() {
  if (!department.value || !isDirty.value) return
  const slugValid = validateRef(slugRef.value)
  const nameValid = validateRef(nameRef.value)
  if (!slugValid || !nameValid) return
  errorMessage.value = null
  await saveMutation.run({
    id: department.value.id,
    slug: editSlug.value.trim(),
    name: editName.value.trim(),
    parent_id: editParentId.value || null,
  })
}

const deleteMutation = useSafeMutation(
  useMutation({
    mutationFn: (id: string) => deleteDepartment(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'departments'] })
    },
  }),
  { successMessage: 'Department deleted.' },
)

async function confirmDelete() {
  if (!department.value) return
  if (!window.confirm(`Delete department "${department.value.name}"? This removes all memberships.`)) {
    return
  }
  const { success } = await deleteMutation.run(department.value.id)
  if (success) router.push('/admin/departments')
}

// ── Members ──
const showAdd = ref(false)
const addUserId = ref('')
const addAsLead = ref(false)

const addCandidates = computed(() => {
  const taken = new Set(members.value.map((m) => m.user_id))
  return allUsers.value.filter((u) => !taken.has(u.id))
})

function openAddMember() {
  addUserId.value = ''
  addAsLead.value = false
  showAdd.value = true
}

const addMutation = useSafeMutation(
  useMutation({
    mutationFn: (args: { deptId: string; user_id: string; is_lead: boolean }) =>
      addDepartmentMember(args.deptId, { user_id: args.user_id, is_lead: args.is_lead }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'departments', deptId.value] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'departments'] })
    },
  }),
  { successMessage: 'Member added.' },
)

async function submitAdd() {
  if (!department.value || !addUserId.value) return
  const { success } = await addMutation.run({
    deptId: department.value.id,
    user_id: addUserId.value,
    is_lead: addAsLead.value,
  })
  if (success) {
    showAdd.value = false
  }
}

const toggleLeadMutation = useSafeMutation(
  useMutation({
    mutationFn: (args: { deptId: string; userId: string; is_lead: boolean }) =>
      updateDepartmentMember(args.deptId, args.userId, args.is_lead),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'departments', deptId.value] })
    },
  }),
  { successMessage: 'Member updated.' },
)

async function toggleLead(m: DepartmentMember) {
  if (!department.value) return
  await toggleLeadMutation.run({
    deptId: department.value.id,
    userId: m.user_id,
    is_lead: !m.is_lead,
  })
}

const removeMutation = useSafeMutation(
  useMutation({
    mutationFn: (args: { deptId: string; userId: string }) =>
      removeDepartmentMember(args.deptId, args.userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'departments', deptId.value] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'departments'] })
    },
  }),
  { successMessage: 'Member removed.' },
)

async function confirmRemove(m: DepartmentMember) {
  if (!department.value) return
  if (!window.confirm(`Remove ${m.name || m.email || m.user_id} from this department?`)) return
  await removeMutation.run({ deptId: department.value.id, userId: m.user_id })
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
