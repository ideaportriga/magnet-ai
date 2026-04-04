<template>
  <kg-dialog-base
    :model-value="modelValue"
    :title="isEditing ? m.knowledgeGraph_editEntity() : m.knowledgeGraph_newEntity()"
    :subtitle="isEditing ? m.knowledgeGraph_configureEntitySubtitle({ name: form.name || m.knowledgeGraph_unnamed() }) : m.knowledgeGraph_defineNewEntitySubtitle()"
    :confirm-label="m.common_save()"
    :loading="loading"
    size="lg"
    max-height="85vh"
    @update:model-value="$emit('update:modelValue', $event)"
    @cancel="onCancel"
    @confirm="onSave"
  >
    <!-- Entity Info Section -->
    <kg-dialog-section
      :title="m.knowledgeGraph_entityInformation()"
      :description="m.knowledgeGraph_entityInfoDesc()"
      icon="o_category"
      icon-color="primary"
    >
      <div class="column q-gap-16">
        <kg-field-row :cols="1" :label="m.knowledgeGraph_entityNameLabel()">
          <km-input v-model="form.name" outlined dense :placeholder="m.knowledgeGraph_entityNamePlaceholder()" />
        </kg-field-row>
        <kg-field-row :cols="1" :label="m.common_description()">
          <km-input
            v-model="form.description"
            outlined
            dense
            :placeholder="m.knowledgeGraph_entityDescPlaceholder()"
            type="textarea"
            autogrow
            :input-style="{ minHeight: '72px', maxHeight: '140px' }"
          />
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
import { m } from '@/paraglide/messages'
import { KgDialogBase, KgDialogSection, KgFieldRow } from '../common'
import EntityColumnsSection from './EntityColumnsSection.vue'
import { cloneEntityDefinitions, createEmptyEntity, type EntityDefinition } from './models'

interface Props {
  modelValue: boolean
  entity?: EntityDefinition | null
  existingEntityNames?: string[]
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  entity: null,
  existingEntityNames: () => [],
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
  columns: [],
})

const validationErrors = computed(() => {
  const errors: string[] = []
  const normalizedEntityName = form.name.trim().toLowerCase()

  if (!form.name.trim()) {
    errors.push(m.knowledgeGraph_entityNameRequired())
  } else if ((props.existingEntityNames || []).some((name) => name.trim().toLowerCase() === normalizedEntityName)) {
    errors.push(m.knowledgeGraph_entityNameMustBeUnique())
  }

  if (form.columns.length === 0) {
    errors.push(m.knowledgeGraph_atLeastOneColumn())
  } else {
    const hasInvalidColumn = form.columns.some((col) => !col.name.trim() || !col.type)
    if (hasInvalidColumn) {
      errors.push(m.knowledgeGraph_allColumnsMustHaveType())
    }

    const normalizedColumnNames = form.columns
      .map((col) => col.name.trim().toLowerCase())
      .filter(Boolean)
    if (normalizedColumnNames.length !== new Set(normalizedColumnNames).size) {
      errors.push(m.knowledgeGraph_columnNamesMustBeUnique())
    }

    const identifierCount = form.columns.filter((col) => col.is_identifier).length
    if (identifierCount !== 1) {
      errors.push(m.knowledgeGraph_exactlyOneIdentifier())
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
  form.columns = clonedEntity.columns
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
  background: var(--q-error-bg);
  border: 1px solid var(--q-error-bg);
  border-radius: var(--radius-md);
}

.entity-validation-errors-list {
  display: flex;
  flex-direction: column;
  gap: 3px;
  font-size: var(--km-font-size-caption);
  color: var(--q-error-text);
}
</style>
