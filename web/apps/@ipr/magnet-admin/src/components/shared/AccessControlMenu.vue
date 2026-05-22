<template>
  <!--
    Record-level access submenu. Drops directly inside an existing
    `<ds-dropdown-menu-content>` (e.g. the kebab on a details page).

    Renders two siblings (Vue 3 fragment):
      1. "Visibility ▸" submenu with the three options.
      2. "Department ▸" submenu — only when visibility='department'.

    Wire to the entity edit buffer:

      <access-control-menu
        :visibility="draft?.visibility"
        :department-id="draft?.department_id"
        @update:visibility="updateField('visibility', $event)"
        @update:department-id="updateField('department_id', $event)"
      />
  -->
  <ds-dropdown-menu-sub>
    <ds-dropdown-menu-sub-trigger data-test="access-visibility-trigger">
      <km-glyph :name="visibilityIcon" size="14px" />
      <span>{{ m.access_visibilityLabel() }}: {{ visibilityLabel }}</span>
    </ds-dropdown-menu-sub-trigger>
    <ds-dropdown-menu-sub-content :side-offset="4" data-test="access-visibility-menu">
      <ds-dropdown-menu-item
        :class="{ 'access-active': effectiveVisibility === 'private' }"
        data-test="access-visibility-private"
        @select="setVisibility('private')"
      >
        <km-glyph name="lock" size="14px" /><span>{{ m.access_visibilityPrivate() }}</span>
      </ds-dropdown-menu-item>
      <ds-dropdown-menu-item
        :class="{ 'access-active': effectiveVisibility === 'department' }"
        data-test="access-visibility-department"
        @select="setVisibility('department')"
      >
        <km-glyph name="group" size="14px" /><span>{{ m.access_visibilityDepartment() }}</span>
      </ds-dropdown-menu-item>
      <ds-dropdown-menu-item
        :class="{ 'access-active': effectiveVisibility === 'tenant' }"
        data-test="access-visibility-tenant"
        @select="setVisibility('tenant')"
      >
        <km-glyph name="globe" size="14px" /><span>{{ m.access_visibilityTenant() }}</span>
      </ds-dropdown-menu-item>
    </ds-dropdown-menu-sub-content>
  </ds-dropdown-menu-sub>
  <ds-dropdown-menu-sub v-if="effectiveVisibility === 'department'">
    <ds-dropdown-menu-sub-trigger data-test="access-department-trigger">
      <km-glyph name="group" size="14px" />
      <span>{{ m.access_departmentLabel() }}: {{ departmentDisplay }}</span>
    </ds-dropdown-menu-sub-trigger>
    <ds-dropdown-menu-sub-content :side-offset="4" data-test="access-department-menu">
      <template v-if="departmentOptions.length">
        <ds-dropdown-menu-item
          v-for="dept in departmentOptions"
          :key="dept.id"
          :class="{ 'access-active': dept.id === departmentId }"
          @select="setDepartmentId(dept.id)"
        >
          {{ dept.name }}
        </ds-dropdown-menu-item>
      </template>
      <ds-dropdown-menu-item v-else disabled>
        {{ m.access_noDepartments() }}
      </ds-dropdown-menu-item>
    </ds-dropdown-menu-sub-content>
  </ds-dropdown-menu-sub>
</template>

<script setup>
import { computed } from 'vue'
import { m } from '@/paraglide/messages'
import { useDepartments } from '@/composables/useDepartments'

const props = defineProps({
  visibility: {
    type: String,
    default: 'tenant',
  },
  departmentId: {
    type: String,
    default: null,
  },
})

const emit = defineEmits(['update:visibility', 'update:department-id'])

const { data: departmentsData } = useDepartments()
const departmentOptions = computed(() => departmentsData.value ?? [])

const effectiveVisibility = computed(() => props.visibility || 'tenant')

const visibilityIcon = computed(() => {
  switch (effectiveVisibility.value) {
    case 'private': return 'lock'
    case 'department': return 'group'
    case 'tenant':
    default: return 'globe'
  }
})

const visibilityLabel = computed(() => {
  switch (effectiveVisibility.value) {
    case 'private': return m.access_visibilityPrivate()
    case 'department': return m.access_visibilityDepartment()
    case 'tenant':
    default: return m.access_visibilityTenant()
  }
})

const departmentDisplay = computed(() => {
  if (!props.departmentId) return m.access_departmentPlaceholder()
  const found = departmentOptions.value.find((d) => d.id === props.departmentId)
  return found?.name || props.departmentId.slice(0, 8)
})

function setVisibility(val) {
  emit('update:visibility', val)
  if (val !== 'department' && props.departmentId) {
    emit('update:department-id', null)
  }
}

function setDepartmentId(val) {
  emit('update:department-id', val || null)
}
</script>

<style scoped>
.access-active {
  background: var(--ds-color-overlay-subtle, rgba(0, 0, 0, 0.04));
  font-weight: 500;
}
</style>
