<template>
  <kg-dialog-base
    :model-value="modelValue"
    :title="isEditing ? 'Edit Entity' : 'New Entity'"
    :subtitle="isEditing ? `Configure the '${form.name || 'Untitled'}' entity definition` : 'Define a new entity type to extract from your documents'"
    confirm-label="Save"
    :loading="loading"
    size="lg"
    max-height="85vh"
    @update:model-value="$emit('update:modelValue', $event)"
    @cancel="onCancel"
    @confirm="onSave"
  >
    <!-- Entity Overview Section -->
    <kg-dialog-section
      title="Entity Overview"
      description="Name this entity, describe what it represents, and choose which sources it is extracted from."
      icon="o_category"
      icon-color="primary"
    >
      <div class="column q-gap-16">
        <kg-field-row :cols="1" label="Entity Name">
          <km-input v-model="form.name" outlined dense placeholder="e.g. Product, Person, Error Code" />
        </kg-field-row>
        <kg-field-row :cols="1" label="Description">
          <km-input
            v-model="form.description"
            outlined
            dense
            placeholder="Describe what this entity represents..."
            type="textarea"
            autogrow
            :input-style="{ minHeight: '72px', maxHeight: '140px' }"
          />
        </kg-field-row>
        <kg-field-row :cols="1" label="Extract from sources">
          <source-tree-dropdown v-model="sourceIdsModel" :sources="sources || []" variant="field" />
        </kg-field-row>
      </div>
    </kg-dialog-section>

    <entity-columns-section v-model:columns="form.columns" />

    <!-- Validation Messages (fixed footer, shown only after save attempt) -->
    <template #footer>
      <div v-if="saveAttempted && validationErrors.length > 0" class="entity-validation-errors">
        <q-icon name="o_warning" size="16px" color="negative" />
        <div class="entity-validation-errors-list">
          <span v-for="(error, idx) in validationErrors" :key="idx">{{ error }}</span>
        </div>
      </div>
    </template>
  </kg-dialog-base>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { KgDialogBase, KgDialogSection, KgFieldRow } from '../common'
import SourceTreeDropdown from '../ContentProfiles/SourceTreeDropdown.vue'
import type { SourceRow } from '../Sources/models'
import EntityColumnsSection from './EntityColumnsSection.vue'
import { cloneEntityDefinitions, createEmptyEntity, type EntityDefinition } from './models'

const ALL_SOURCES_KEY = '__ALL__'
const NONE_SELECTED_KEY = '__NONE__'

interface Props {
  modelValue: boolean
  entity?: EntityDefinition | null
  existingEntityNames?: string[]
  sources?: SourceRow[]
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  entity: null,
  existingEntityNames: () => [],
  sources: () => [],
  loading: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  cancel: []
  save: [entity: EntityDefinition]
}>()

const isEditing = computed(() => !!props.entity)
const saveAttempted = ref(false)

const form = reactive<EntityDefinition>({
  id: '',
  name: '',
  description: '',
  enabled: true,
  columns: [],
  source_ids: [],
})

// - stored `source_ids: []` (or `['__ALL__']`) means any source
// - UI empty selection maps to the explicit `['__NONE__']` marker
// - group keys (`__GROUP__<type>`) and individual source ids are stored as-is
const sourceIdsModel = computed<string[]>({
  get: () => {
    const stored = Array.isArray(form.source_ids) ? form.source_ids : []
    if (stored.includes(NONE_SELECTED_KEY)) {
      return []
    }
    if (stored.length === 0) {
      return [ALL_SOURCES_KEY]
    }
    return stored
  },
  set: (uiValue) => {
    const incoming = Array.isArray(uiValue) ? uiValue.filter(Boolean) : []
    if (incoming.includes(ALL_SOURCES_KEY)) {
      form.source_ids = []
      return
    }
    if (incoming.length === 0) {
      form.source_ids = [NONE_SELECTED_KEY]
      return
    }
    form.source_ids = [...new Set(incoming)]
  },
})

const validationErrors = computed(() => {
  const errors: string[] = []
  const normalizedEntityName = form.name.trim().toLowerCase()

  if (!form.name.trim()) {
    errors.push('Entity name is required')
  } else if ((props.existingEntityNames || []).some((name) => name.trim().toLowerCase() === normalizedEntityName)) {
    errors.push('Entity name must be unique')
  }

  if (form.columns.length === 0) {
    errors.push('At least one column is required')
  } else {
    const hasInvalidColumn = form.columns.some((col) => !col.name.trim() || !col.type)
    if (hasInvalidColumn) {
      errors.push('All columns must have a name and type')
    }

    const normalizedColumnNames = form.columns
      .map((col) => col.name.trim().toLowerCase())
      .filter(Boolean)
    if (normalizedColumnNames.length !== new Set(normalizedColumnNames).size) {
      errors.push('Column names must be unique within an entity')
    }

    const identifierCount = form.columns.filter((col) => col.is_identifier).length
    if (identifierCount > 1) {
      errors.push('At most one column can be marked as identifier')
    }
  }
  return errors
})

const isFormValid = computed(() => validationErrors.value.length === 0)

function applyEntityToForm(entity: EntityDefinition) {
  const [clonedEntity] = cloneEntityDefinitions([entity])
  form.id = clonedEntity.id
  form.name = clonedEntity.name
  form.description = clonedEntity.description
  form.enabled = clonedEntity.enabled !== false
  form.columns = clonedEntity.columns
  form.source_ids = [...(clonedEntity.source_ids || [])]
}

function resetForm() {
  saveAttempted.value = false
  if (props.entity) {
    applyEntityToForm(props.entity)
  } else {
    applyEntityToForm(createEmptyEntity())
  }
}

watch(
  () => props.modelValue,
  (open) => {
    if (open) resetForm()
  },
  { immediate: true }
)

function onCancel() {
  emit('cancel')
  emit('update:modelValue', false)
}

function onSave() {
  saveAttempted.value = true
  if (!isFormValid.value) return

  emit('save', cloneEntityDefinitions([form])[0])
}
</script>

<style scoped>
/* ── Validation ── */
.entity-validation-errors {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 14px;
  background: #ffebee;
  border: 1px solid #ffcdd2;
  border-radius: 6px;
}

.entity-validation-errors-list {
  display: flex;
  flex-direction: column;
  gap: 3px;
  font-size: 12px;
  color: #c62828;
}
</style>
