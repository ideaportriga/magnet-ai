<template>
  <!--
    Shared record-level access editor (PR 11 of access-control plan).
    Used in entity create dialogs. For editing on a saved record see
    AccessControlMenu, which lives inside the kebab dropdown on details
    pages.

    Bind with `v-model:visibility` and `v-model:department-id`:

      <access-control
        v-model:visibility="newRow.visibility"
        v-model:department-id="newRow.department_id"
      />

    The 'department' option is only meaningful with a department picked;
    we surface the picker conditionally and validate via :rules so the
    parent dialog's km-popup-confirm validation catches the empty case.
  -->
  <div class="stack" data-gap="md">
    <div class="km-field text-secondary-text pl-sm">
      {{ m.access_visibilityLabel() }}
      <div class="stack mt-xs" data-gap="0">
        <km-radio :model-value="visibility" class="my-2xs" name="visibility" dense :label="m.access_visibilityPrivate()" val="private" data-test="visibility-private" @update:model-value="setVisibility" />
        <km-radio :model-value="visibility" class="my-2xs" name="visibility" dense :label="m.access_visibilityDepartment()" val="department" data-test="visibility-department" @update:model-value="setVisibility" />
        <km-radio :model-value="visibility" class="my-2xs" name="visibility" dense :label="m.access_visibilityTenant()" val="tenant" data-test="visibility-tenant" @update:model-value="setVisibility" />
      </div>
      <div class="km-description text-secondary-text pt-2xs">{{ visibilityHint }}</div>
    </div>
    <div v-if="effectiveVisibility === 'department'" class="km-field text-secondary-text pl-sm">
      {{ m.access_departmentLabel() }}
      <div class="full-width">
        <km-select
          ref="departmentRef"
          :model-value="departmentId"
          data-test="access-department-select"
          height="30px"
          option-label="name"
          option-value="id"
          emit-value
          map-options
          has-dropdown-search
          :placeholder="m.access_departmentPlaceholder()"
          :options="departmentOptions"
          :loading="isLoadingDepartments"
          :rules="departmentRules"
          @update:model-value="setDepartmentId"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
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
  required: {
    type: Boolean,
    default: true,
  },
})

const emit = defineEmits(['update:visibility', 'update:department-id'])

const departmentRef = ref(null)
const { data: departmentsData, isLoading: isLoadingDepartments } = useDepartments()
const departmentOptions = computed(() => departmentsData.value ?? [])

const effectiveVisibility = computed(() => props.visibility || 'tenant')

const visibilityHint = computed(() => {
  switch (effectiveVisibility.value) {
    case 'private':
      return m.access_visibilityPrivateHint()
    case 'department':
      return m.access_visibilityDepartmentHint()
    case 'tenant':
    default:
      return m.access_visibilityTenantHint()
  }
})

const departmentRules = computed(() => {
  if (!props.required || effectiveVisibility.value !== 'department') return []
  return [(val) => !!val || m.access_departmentRequired()]
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

defineExpose({ departmentRef })
</script>
