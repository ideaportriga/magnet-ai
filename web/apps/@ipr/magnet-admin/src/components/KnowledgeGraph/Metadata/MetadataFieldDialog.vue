<template>
  <kg-dialog-base
    :model-value="props.showDialog"
    :title="isEditMode ? 'Edit Metadata Field' : 'Define Metadata Field'"
    :confirm-label="isEditMode ? 'Save Changes' : 'Create Field'"
    :loading="loading"
    :disable-confirm="!isFormValid"
    size="md"
    @update:model-value="emit('update:showDialog', $event)"
    @cancel="emit('cancel')"
    @confirm="onConfirm"
  >
    <div class="column q-gap-24">
      <!-- Basic Info Section -->
      <kg-dialog-section title="Field Identity" description="Define the field name and display properties" icon="label">
        <kg-field-row :cols="2">
          <div>
            <div class="km-input-label q-pb-xs">
              Field Name
              <q-icon name="o_info" size="12px" color="grey-6" class="q-ml-xs cursor-pointer">
                <q-tooltip>Internal identifier, used in API and data. Use snake_case.</q-tooltip>
              </q-icon>
            </div>
            <km-input v-model="fieldName" height="36px" placeholder="field_name" :rules="fieldNameRules" :disable="isEditMode" />
          </div>
          <div>
            <div class="km-input-label q-pb-xs">Display Name</div>
            <km-input v-model="displayName" height="36px" placeholder="Field Display Name" />
          </div>
        </kg-field-row>

        <div class="q-mt-md">
          <div class="km-input-label q-pb-xs">Description</div>
          <km-input
            v-model="description"
            autogrow
            rows="1"
            type="textarea"
            placeholder="Describe what this field represents and how it should be used..."
          />
        </div>
      </kg-dialog-section>

      <!-- Type & Constraints Section -->
      <kg-dialog-section title="Value Configuration" description="Specify the data type and value constraints" icon="tune">
        <kg-field-row :cols="2">
          <div>
            <div class="km-input-label q-pb-xs">Value Type</div>
            <q-select v-model="valueType" :options="valueTypeOptions" dense outlined emit-value map-options class="metadata-type-select">
              <template #option="{ opt, itemProps }">
                <q-item v-bind="itemProps">
                  <q-item-section avatar>
                    <q-icon :name="opt.icon" size="18px" color="grey-7" />
                  </q-item-section>
                  <q-item-section>{{ opt.label }}</q-item-section>
                </q-item>
              </template>
              <template #selected-item="{ opt }">
                <div class="row items-center q-gap-sm">
                  <q-icon :name="opt.icon" size="16px" color="grey-7" />
                  <span>{{ opt.label }}</span>
                </div>
              </template>
            </q-select>
          </div>
          <div>
            <div class="km-input-label q-pb-xs">Default Value</div>
            <km-input v-model="defaultValue" height="36px" placeholder="Optional default" />
          </div>
        </kg-field-row>

        <div class="q-mt-md">
          <div class="km-input-label q-pb-xs">
            Allowed Values
            <q-icon name="o_info" size="12px" color="grey-6" class="q-ml-xs cursor-pointer">
              <q-tooltip>Constrain this field to specific values. LLMs will respect these constraints.</q-tooltip>
            </q-icon>
          </div>
          <q-select
            v-model="allowedValues"
            use-input
            use-chips
            multiple
            hide-dropdown-icon
            input-debounce="0"
            new-value-mode="add-unique"
            placeholder="Type and press Enter to add allowed values"
            dense
            outlined
            class="metadata-values-select"
          >
            <template #selected-item="scope">
              <q-chip removable dense color="primary" text-color="white" class="q-my-xs" @remove="scope.removeAtIndex(scope.index)">
                {{ scope.opt }}
              </q-chip>
            </template>
          </q-select>
        </div>

        <div class="q-mt-md">
          <kg-toggle-field v-model="isRequired" title="Required field" description="Mark documents as incomplete if this field is missing" />
        </div>
      </kg-dialog-section>

      <!-- LLM Extraction Section -->
      <kg-dialog-section title="LLM Extraction" description="Configure how this field should be extracted by AI" icon="smart_toy">
        <div>
          <div class="km-input-label q-pb-xs">
            Extraction Hint
            <q-icon name="o_info" size="12px" color="grey-6" class="q-ml-xs cursor-pointer">
              <q-tooltip>Provide guidance for the LLM on how to identify and extract this field</q-tooltip>
            </q-icon>
          </div>
          <km-input
            v-model="extractionHint"
            height="72px"
            type="textarea"
            placeholder="e.g., Look for the author name in the document header or 'Written by' sections..."
          />
        </div>
      </kg-dialog-section>
    </div>
  </kg-dialog-base>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { KgDialogBase, KgDialogSection, KgFieldRow, KgToggleField } from '../common'
import { MetadataFieldDefinition, MetadataValueType, ValueTypeOptions } from './models'

const props = defineProps<{
  showDialog: boolean
  field?: MetadataFieldDefinition | null
  existingFieldNames?: string[]
}>()

const emit = defineEmits<{
  (e: 'update:showDialog', value: boolean): void
  (e: 'cancel'): void
  (e: 'save', field: MetadataFieldDefinition): void
  (e: 'delete', fieldId: string): void
}>()

// Form state
const fieldName = ref('')
const displayName = ref('')
const description = ref('')
const valueType = ref<MetadataValueType>('string')
const defaultValue = ref('')
const allowedValues = ref<string[]>([])
const extractionHint = ref('')
const isSearchable = ref(true)
const isFilterable = ref(true)
const isRequired = ref(false)
const loading = ref(false)

const valueTypeOptions = ValueTypeOptions

const isEditMode = computed(() => !!props.field?.id)

const fieldNameRules = [
  (val: string) => !!(val && val.trim()) || 'Field name is required',
  (val: string) => /^[a-z][a-z0-9_]*$/.test(val || '') || 'Use lowercase letters, numbers, and underscores',
  (val: string) => {
    if (isEditMode.value) return true
    const existing = props.existingFieldNames || []
    return !existing.includes(val) || 'Field name already exists'
  },
]

const isFormValid = computed(() => {
  return fieldName.value.trim() && /^[a-z][a-z0-9_]*$/.test(fieldName.value)
})

// Initialize form when dialog opens or field changes
watch(
  () => [props.showDialog, props.field] as const,
  () => {
    if (props.showDialog) {
      if (props.field) {
        fieldName.value = props.field.name
        displayName.value = props.field.display_name || ''
        description.value = props.field.description || ''
        valueType.value = props.field.value_type || 'string'
        defaultValue.value = props.field.default_value || ''
        allowedValues.value = props.field.allowed_values || []
        extractionHint.value = props.field.llm_extraction_hint || ''
        isSearchable.value = props.field.is_searchable ?? true
        isFilterable.value = props.field.is_filterable ?? true
        isRequired.value = props.field.is_required ?? false
      } else {
        // Reset for new field
        fieldName.value = ''
        displayName.value = ''
        description.value = ''
        valueType.value = 'string'
        defaultValue.value = ''
        allowedValues.value = []
        extractionHint.value = ''
        isSearchable.value = true
        isFilterable.value = true
        isRequired.value = false
      }
    }
  },
  { immediate: true }
)

// Auto-generate display name from field name
watch(fieldName, (newVal) => {
  if (!isEditMode.value && !displayName.value) {
    displayName.value = newVal
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ')
  }
})

const onConfirm = () => {
  const field: MetadataFieldDefinition = {
    id: props.field?.id || crypto.randomUUID(),
    name: fieldName.value.trim(),
    display_name: displayName.value.trim() || fieldName.value.trim(),
    description: description.value.trim(),
    value_type: valueType.value,
    is_searchable: isSearchable.value,
    is_filterable: isFilterable.value,
    is_required: isRequired.value,
    allowed_values: allowedValues.value.length > 0 ? allowedValues.value : undefined,
    default_value: defaultValue.value.trim() || undefined,
    llm_extraction_hint: extractionHint.value.trim() || undefined,
  }
  emit('save', field)
}
</script>

<style scoped>
.metadata-type-select :deep(.q-field__control) {
  min-height: 36px;
  padding: 0 12px;
}

.metadata-values-select {
  min-height: 36px;
}

.metadata-values-select :deep(.q-field__control) {
  min-height: 36px;
  padding: 4px 8px;
}

.metadata-values-select :deep(.q-field__native) {
  min-height: 24px;
  padding: 0;
}

.metadata-values-select :deep(.q-chip) {
  margin: 2px;
}
</style>
