<template>
  <kg-dialog-base
    :model-value="props.showDialog"
    :title="isEditMode ? 'Edit Smart Extraction Field' : 'Add Smart Extraction Field'"
    :confirm-label="isEditMode ? 'Save Changes' : 'Add Field'"
    :loading="loading"
    size="lg"
    @update:model-value="emit('update:showDialog', $event)"
    @cancel="emit('cancel')"
    @confirm="onConfirm"
  >
    <div class="column q-gap-16">
      <!-- Field Name Section -->
      <kg-dialog-section title="Field Identity" description="Define the field identifier used for smart extraction" icon="badge">
        <kg-field-row gap="16px">
          <kg-field-row label="Field Name">
            <km-input ref="fieldNameInputRef" v-model="fieldName" height="36px" :rules="fieldNameRules" :disabled="isEditMode" />
          </kg-field-row>
          <kg-field-row label="Extraction Hint" hint="Define how AI should extract this field">
            <km-input
              ref="extractionHintInputRef"
              v-model="extractionHint"
              autogrow
              rows="3"
              type="textarea"
              placeholder="Guide the AI on how to extract this field..."
            />
          </kg-field-row>
        </kg-field-row>
      </kg-dialog-section>

      <!-- Type & Constraints Section -->
      <kg-dialog-section
        title="Type &amp; Constraints"
        description="Define the value type, cardinality, restrictions and extraction requirements"
        icon="rule"
      >
        <kg-field-row :cols="4" gap="12px" class="q-mb-md constraints-row">
          <kg-field-row label="Value Type">
            <kg-dropdown-field v-model="valueTypeModel" :options="valueTypeOptions" placeholder="Select type" dense />
          </kg-field-row>
          <kg-field-row label="Multiple Values">
            <kg-toggle-field v-model="isMultiple" :title="isMultiple ? 'Multiple values' : 'Allow'" />
          </kg-field-row>
          <kg-field-row label="Value Restrictions">
            <kg-toggle-field v-model="restrictToAllowedValues" :title="restrictToAllowedValues ? 'Values predefined' : 'Predefine values'" />
          </kg-field-row>
          <kg-field-row label="Required">
            <kg-toggle-field v-model="isRequired" :title="isRequired ? 'Required field' : 'Mark as required'" />
          </kg-field-row>
        </kg-field-row>

        <!-- Restricted Values -->
        <kg-field-row
          v-if="restrictToAllowedValues"
          label="Predefined Options"
          :error="predefinedOptionsError ? 'At least one predefined option is required' : undefined"
        >
          <div class="value-options-container">
            <div class="value-options-list">
              <div v-for="(av, idx) in allowedValues" :key="idx" class="value-option-chip">
                <span class="value-option-text">{{ av.value }}</span>
                <q-icon name="close" size="14px" class="value-option-remove" @click.stop="removeAllowedValue(idx)" />
              </div>

              <div class="value-options-input-row">
                <km-input
                  v-model="newAllowedValue"
                  height="32px"
                  placeholder="Enter option and press Enter"
                  class="col"
                  @keyup.enter="addAllowedValue"
                />
                <km-btn flat label="Add" @click="addAllowedValue" />
              </div>
            </div>
          </div>
        </kg-field-row>
      </kg-dialog-section>
    </div>
  </kg-dialog-base>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { KgDialogBase, KgDialogSection, KgDropdownField, KgFieldRow, KgToggleField } from '../common'
import { AllowedValue, MetadataValueType, ValueTypeOptions } from './models'

// Default extraction template
const DEFAULT_EXTRACTION_TEMPLATE = ''

export interface SmartExtractionFieldDefinition {
  id: string
  name: string
  value_type: MetadataValueType
  is_multiple: boolean
  is_required: boolean
  allowed_values?: AllowedValue[]
  llm_extraction_hint?: string
}

const props = defineProps<{
  showDialog: boolean
  field?: SmartExtractionFieldDefinition | null
  existingFieldNames?: string[]
}>()

const emit = defineEmits<{
  (e: 'update:showDialog', value: boolean): void
  (e: 'cancel'): void
  (e: 'save', field: SmartExtractionFieldDefinition): void
}>()

// Form state
const fieldName = ref('')
const valueType = ref<MetadataValueType>('string')
const valueTypeModel = computed<string | undefined>({
  get: () => valueType.value,
  set: (v) => {
    valueType.value = (v as MetadataValueType) || 'string'
  },
})
const isMultiple = ref(false)
const isRequired = ref(false)
const restrictToAllowedValues = ref(false)
const allowedValues = ref<AllowedValue[]>([])
const newAllowedValue = ref('')
const extractionHint = ref('')
const loading = ref(false)
const fieldNameInputRef = ref<any>(null)
const showPredefinedOptionsError = ref(false)

const valueTypeOptions = ValueTypeOptions

const isEditMode = computed(() => !!props.field?.id)

const predefinedOptionsError = computed(() => showPredefinedOptionsError.value && restrictToAllowedValues.value && allowedValues.value.length === 0)

const fieldNameRules = [
  (val: string) => !!(val && val.trim()) || 'Field name is required',
  (val: string) => {
    if (isEditMode.value) return true
    const existing = props.existingFieldNames || []
    return !existing.includes(val) || 'Field name already exists'
  },
]

// Methods for managing allowed values
const addAllowedValue = () => {
  const val = newAllowedValue.value.trim()
  if (val) {
    if (!allowedValues.value.some((av) => av.value === val)) {
      allowedValues.value.push({ value: val })
    }
    // Clear input even if value already exists
    newAllowedValue.value = ''
  }
}

const removeAllowedValue = (idx: number) => {
  allowedValues.value.splice(idx, 1)
}

// Initialize form when dialog opens or field changes
watch(
  () => [props.showDialog, props.field] as const,
  () => {
    if (props.showDialog) {
      if (props.field) {
        fieldName.value = props.field.name
        valueType.value = props.field.value_type || 'string'
        isMultiple.value = !!props.field.is_multiple
        isRequired.value = !!props.field.is_required
        restrictToAllowedValues.value = !!props.field.allowed_values?.length
        allowedValues.value = props.field.allowed_values || []
        extractionHint.value = props.field.llm_extraction_hint || DEFAULT_EXTRACTION_TEMPLATE
        showPredefinedOptionsError.value = false
      } else {
        // Reset for new field
        fieldName.value = ''
        valueType.value = 'string'
        isMultiple.value = false
        isRequired.value = false
        restrictToAllowedValues.value = false
        allowedValues.value = []
        newAllowedValue.value = ''
        extractionHint.value = DEFAULT_EXTRACTION_TEMPLATE
        showPredefinedOptionsError.value = false
      }
    }
  },
  { immediate: true }
)

const onConfirm = () => {
  // Validate field name before saving
  if (fieldNameInputRef.value && !fieldNameInputRef.value.validate()) {
    return
  }

  // Validate predefined options
  showPredefinedOptionsError.value = true
  if (restrictToAllowedValues.value && allowedValues.value.length === 0) {
    return
  }

  const finalExtractionHint = extractionHint.value.trim() || undefined

  const field: SmartExtractionFieldDefinition = {
    id: props.field?.id || crypto.randomUUID(),
    name: fieldName.value.trim(),
    value_type: valueType.value,
    is_multiple: isMultiple.value,
    is_required: isRequired.value,
    allowed_values: restrictToAllowedValues.value && allowedValues.value.length > 0 ? allowedValues.value : undefined,
    llm_extraction_hint: finalExtractionHint || undefined,
  }
  emit('save', field)
}
</script>

<style scoped>
/* Normalize control height across the constraints row */
.constraints-row :deep(.q-field__control) {
  height: 40px !important;
  min-height: 40px !important;
  max-height: 40px !important;
}

.constraints-row :deep(.q-field__native),
.constraints-row :deep(.q-field__input),
.constraints-row :deep(.q-field__marginal) {
  min-height: 40px !important;
}

.constraints-row :deep(.kg-toggle-field) {
  min-height: 40px;
  height: 40px;
  padding: 0 16px;
}

/* Value Options Section */
.value-options-container {
  border: 1px solid var(--q-control-border);
  border-radius: var(--radius-md);
  background: var(--q-white);
  overflow: hidden;
}

.value-options-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px;
  align-items: center;
}

.value-option-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 9px 5px 7px;
  background: var(--q-white);
  border: 1px solid var(--q-control-border);
  border-radius: var(--radius-md);
  font-size: var(--km-font-size-label);
  cursor: default;
  transition: all 0.2s ease;
  user-select: none;
}

.value-option-chip:hover {
  border-color: var(--q-primary);
  background: rgba(var(--q-primary-rgb), 0.03);
}

.value-option-text {
  font-weight: 500;
  color: var(--q-label);
}

.value-option-remove {
  color: var(--q-icon);
  opacity: 0;
  transition: all 0.15s ease;
  margin-left: 2px;
}

.value-option-chip:hover .value-option-remove {
  opacity: 1;
}

.value-option-remove:hover {
  color: var(--q-error);
}

.value-options-input-row {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  flex-basis: 100%;
  margin-top: 4px;
}
</style>
