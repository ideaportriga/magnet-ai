<template>
  <kg-dialog-base
    :model-value="props.showDialog"
    :title="isEditMode ? 'Edit Smart Extraction Field' : 'Add Smart Extraction Field'"
    :confirm-label="isEditMode ? 'Save Changes' : 'Add Field'"
    :loading="loading"
    size="md"
    @update:model-value="emit('update:showDialog', $event)"
    @cancel="emit('cancel')"
    @confirm="onConfirm"
  >
    <div class="column q-gap-16">
      <!-- Field Name Section -->
      <kg-dialog-section title="Field Identity" description="Define the field identifier used for smart extraction" icon="edit">
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

      <!-- Data Type Section -->
      <kg-dialog-section title="Data Type" description="Choose the type of values this field will store" icon="tune">
        <kg-field-row>
          <kg-dropdown-field v-model="valueTypeModel" :options="valueTypeOptions" placeholder="Select type" dense />
        </kg-field-row>
      </kg-dialog-section>

      <!-- Input Constraints Section -->
      <kg-dialog-section title="Input Constraints" description="Define cardinality and value restrictions" icon="list_alt">
        <kg-field-row :cols="2" class="q-mb-md">
          <kg-toggle-field v-model="isMultiple" title="Accept multiple values" />
          <kg-toggle-field v-model="restrictToAllowedValues" title="Limit to predefined options" />
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
        restrictToAllowedValues.value = !!props.field.allowed_values?.length
        allowedValues.value = props.field.allowed_values || []
        extractionHint.value = props.field.llm_extraction_hint || DEFAULT_EXTRACTION_TEMPLATE
        showPredefinedOptionsError.value = false
      } else {
        // Reset for new field
        fieldName.value = ''
        valueType.value = 'string'
        isMultiple.value = false
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
    allowed_values: restrictToAllowedValues.value && allowedValues.value.length > 0 ? allowedValues.value : undefined,
    llm_extraction_hint: finalExtractionHint || undefined,
  }
  emit('save', field)
}
</script>

<style scoped>
/* Value Options Section */
.value-options-container {
  border: 1px solid var(--q-control-border);
  border-radius: 6px;
  background: #fff;
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
  background: white;
  border: 1px solid var(--q-control-border);
  border-radius: 6px;
  font-size: 13px;
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
  color: #444;
}

.value-option-remove {
  color: #999;
  opacity: 0;
  transition: all 0.15s ease;
  margin-left: 2px;
}

.value-option-chip:hover .value-option-remove {
  opacity: 1;
}

.value-option-remove:hover {
  color: #c00;
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
