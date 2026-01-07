<template>
  <kg-dialog-base
    :model-value="props.showDialog"
    :title="isEditMode ? 'Edit Metadata Field' : 'Define Metadata Field'"
    :confirm-label="isEditMode ? 'Save Changes' : 'Create Field'"
    :loading="loading"
    size="md"
    @update:model-value="emit('update:showDialog', $event)"
    @cancel="emit('cancel')"
    @confirm="onConfirm"
  >
    <div class="column q-gap-16">
      <!-- Basic Info Section -->
      <kg-dialog-section title="Field Identity" description="Define the field name and display properties" icon="edit">
        <kg-field-row :cols="2">
          <kg-field-row label="Field Name" hint="Internal identifier, can be used in API or by AI for smart extraction. Use snake_case.">
            <km-input
              ref="fieldNameInputRef"
              v-model="fieldName"
              height="36px"
              placeholder="field_name"
              :rules="fieldNameRules"
              :disabled="isEditMode"
            />
          </kg-field-row>
          <kg-field-row label="Display Name">
            <km-input v-model="displayName" height="36px" placeholder="Field Display Name" />
          </kg-field-row>
        </kg-field-row>

        <kg-field-row label="Description" class="q-mt-md">
          <km-input
            v-model="description"
            autogrow
            rows="1"
            type="textarea"
            placeholder="Describe what this field represents and how it should be used..."
            height="36px"
          />
        </kg-field-row>
      </kg-dialog-section>

      <!-- Field Configuration -->
      <kg-dialog-section title="Data Type" description="Choose the type of values this field will store" icon="tune">
        <kg-field-row>
          <kg-dropdown-field v-model="valueTypeModel" :options="valueTypeOptions" placeholder="Select type" dense />
        </kg-field-row>
      </kg-dialog-section>

      <!-- Values Configuration -->
      <kg-dialog-section title="Input Constraints" description="Define cardinality and value restrictions" icon="list_alt">
        <kg-field-row :cols="2" class="q-mb-md">
          <kg-toggle-field v-model="isMultiple" title="Accept multiple values" />
          <kg-toggle-field v-model="restrictToAllowedValues" title="Limit to predefined options" />
        </kg-field-row>

        <!-- Free Value (no restriction) -->
        <kg-field-row v-if="!restrictToAllowedValues" :label="isMultiple ? 'Default Values' : 'Default Value'">
          <km-input v-if="!isMultiple" v-model="defaultValue" height="36px" />
          <km-input v-else v-model="defaultValuesText" height="36px" placeholder="Comma-separated values" />
        </kg-field-row>

        <!-- Restricted Values -->
        <kg-field-row
          v-if="restrictToAllowedValues"
          label="Predefined Options"
          :suffix="allowedValues.length > 0 ? '(click to set as default)' : ''"
          :error="predefinedOptionsError ? 'At least one predefined option is required' : undefined"
        >
          <div class="value-options-container">
            <div class="value-options-list">
              <div
                v-for="(av, idx) in allowedValues"
                :key="idx"
                class="value-option-chip"
                :class="{ 'value-option-chip--default': isValueDefault(av.value) }"
                @click="toggleDefault(av.value)"
              >
                <q-icon :name="isValueDefault(av.value) ? 'check_circle' : 'radio_button_unchecked'" size="16px" class="value-option-check" />
                <span class="value-option-text">{{ av.value }}</span>
                <q-icon name="close" size="14px" class="value-option-remove" @click.stop="removeAllowedValue(idx)" />
                <q-tooltip v-if="isValueDefault(av.value)" anchor="top middle" self="bottom middle">
                  Default value{{ isMultiple ? '' : ' (click another to change)' }}
                </q-tooltip>
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

      <!-- Smart Extraction Section -->
      <kg-dialog-section
        title="Smart Extraction"
        description="Define how AI should extract this field, variables can be used to insert dynamic values into the instructions"
        icon="smart_toy"
      >
        <template #header-actions>
          <kg-section-control v-model="extractionMode" :options="extractionModeOptions" />
        </template>

        <div class="extraction-content" :class="{ 'extraction-content--disabled': extractionMode === 'disabled' }">
          <km-input
            ref="extractionHintInputRef"
            v-model="extractionHint"
            autogrow
            rows="3"
            type="textarea"
            placeholder="Guide the AI on how to extract this field..."
            :disabled="extractionMode === 'disabled'"
          />

          <div class="row justify-between">
            <div class="extraction-variables-list">
              <q-chip
                v-for="v in EXTRACTION_VARIABLES"
                :key="v.key"
                clickable
                dense
                outline
                :disable="extractionMode === 'disabled'"
                class="extraction-var-chip"
                @mousedown.prevent
                @click="insertExtractionVariable(v.key)"
              >
                <span class="extraction-var-token">{{ formatExtractionVariableToken(v.key) }}</span>
              </q-chip>
            </div>

            <div class="extraction-subtoolbar">
              <div class="extraction-toolbar">
                <q-btn
                  flat
                  dense
                  size="sm"
                  icon="restart_alt"
                  color="grey-6"
                  :disable="extractionMode === 'disabled'"
                  @click="resetToDefaultTemplate"
                >
                  <q-tooltip>Reset to default template</q-tooltip>
                </q-btn>
                <q-btn
                  flat
                  dense
                  size="sm"
                  :icon="showPreview ? 'visibility_off' : 'visibility'"
                  color="grey-6"
                  :disable="extractionMode === 'disabled'"
                  @click="showPreview = !showPreview"
                >
                  <q-tooltip>{{ showPreview ? 'Hide' : 'Show' }} preview</q-tooltip>
                </q-btn>
              </div>
            </div>
          </div>

          <div v-if="showPreview && extractionMode !== 'disabled'" class="extraction-preview">{{ renderedExtractionHint }}</div>
        </div>
      </kg-dialog-section>

      <!-- Per-Source Overrides -->
      <kg-dialog-section
        title="Source Overrides"
        description="Override this field for specific sources with constant values applied during ingestion"
        icon="layers"
      >
        <div v-if="!hasSourceOptions" class="text-caption text-grey-6 italic">No sources available in this knowledge graph.</div>

        <kg-field-row v-else gap="8px">
          <div v-for="ov in sourceOverrides" :key="ov._id" class="overrides-row">
            <kg-field-row :cols="2" gap="12px">
              <div class="overrides-source-cell">
                <div class="overrides-source-logo">
                  <q-img v-if="getSourceVisual(ov.source_type_key).image" :src="getSourceVisual(ov.source_type_key).image" no-spinner no-transition />
                  <q-icon v-else :name="getSourceVisual(ov.source_type_key).icon" size="18px" color="grey-8" />
                </div>
                <span class="overrides-source-name">{{ ov.source_name }}</span>
              </div>

              <km-input v-if="!isMultiple" v-model="ov.constant_value" height="36px" placeholder="Set a constant value for this source" />
              <km-input v-else v-model="ov.constant_values_text" height="36px" placeholder="Set constant values for this source (comma-separated)" />
            </kg-field-row>
          </div>
        </kg-field-row>
      </kg-dialog-section>
    </div>
  </kg-dialog-base>
</template>

<script setup lang="ts">
import confluenceImage from '@/assets/brands/atlassian-confluence.png'
import fluidTopicsImage from '@/assets/brands/fluid-topics.png'
import sharepointImage from '@/assets/brands/sharepoint.svg'
import { computed, nextTick, ref, watch } from 'vue'
import { KgDialogBase, KgDialogSection, KgDropdownField, KgFieldRow, KgSectionControl, KgToggleField } from '../common'
import { type SourceRow } from '../Sources/models'
import { AllowedValue, MetadataFieldDefinition, MetadataFieldSourceOverride, MetadataValueType, PRESET_FIELDS, ValueTypeOptions } from './models'

// Source type visuals (image or icon)
const sourceTypeVisuals: Record<string, { image?: string; icon?: string }> = {
  upload: { icon: 'fas fa-upload' },
  sharepoint: { image: sharepointImage },
  fluid_topics: { image: fluidTopicsImage },
  confluence: { image: confluenceImage },
}

const getSourceVisual = (type: string) => {
  return sourceTypeVisuals[type] || { icon: 'description' }
}

// Extraction mode options
type ExtractionMode = 'disabled' | 'optional' | 'mandatory'
const extractionModeOptions = [
  { label: 'Disabled', value: 'disabled' },
  { label: 'Optional', value: 'optional' },
  { label: 'Mandatory', value: 'mandatory' },
]

// Default extraction template (same for optional and mandatory)
const DEFAULT_EXTRACTION_TEMPLATE = `Extract {display_name} ({type}, {cardinality}).
Allowed: {values}. Default: {defaults}.`

type ExtractionVariableKey = 'field_name' | 'display_name' | 'type' | 'values' | 'defaults' | 'cardinality'

const EXTRACTION_VARIABLES: Array<{ key: ExtractionVariableKey }> = [
  { key: 'field_name' },
  { key: 'display_name' },
  { key: 'type' },
  { key: 'values' },
  { key: 'defaults' },
  { key: 'cardinality' },
]

const props = defineProps<{
  showDialog: boolean
  field?: MetadataFieldDefinition | null
  existingFieldNames?: string[]
  sources?: SourceRow[]
}>()

const emit = defineEmits<{
  (e: 'update:showDialog', value: boolean): void
  (e: 'cancel'): void
  (e: 'save', field: MetadataFieldDefinition): void
}>()

// Form state
const fieldName = ref('')
const displayName = ref('')
const description = ref('')
const valueType = ref<MetadataValueType>('string')
const valueTypeModel = computed<string | undefined>({
  get: () => valueType.value,
  set: (v) => {
    valueType.value = (v as MetadataValueType) || 'string'
  },
})
const isMultiple = ref(false)
const restrictToAllowedValues = ref(false)
const extractionMode = ref<ExtractionMode>('disabled')
const isRequired = computed(() => extractionMode.value === 'mandatory')
const defaultValue = ref('')
const defaultValues = ref<string[]>([])
const defaultValuesText = computed<string>({
  get: () => defaultValues.value.join(', '),
  set: (v) => {
    const parsed = (v || '')
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean)
    defaultValues.value = Array.from(new Set(parsed))
  },
})
const allowedValues = ref<AllowedValue[]>([])
const newAllowedValue = ref('')
const extractionHint = ref('')
const showPreview = ref(false)
const loading = ref(false)
const extractionHintInputRef = ref<any>(null)
const fieldNameInputRef = ref<any>(null)
const showPredefinedOptionsError = ref(false)

type SourceOverrideDraft = {
  _id: string
  source_id: string
  source_name: string
  source_type_key: string
  constant_value: string
  constant_values_text: string
}

const sourceOverrides = ref<SourceOverrideDraft[]>([])

const parseCommaSeparated = (text: string): string[] => {
  const parsed = (text || '')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
  return Array.from(new Set(parsed))
}

const hasSourceOptions = computed(() => (props.sources || []).length > 0)

const initSourceOverrides = (existingOverrides?: MetadataFieldSourceOverride[]) => {
  const sources = props.sources || []
  const existingMap = new Map<string, MetadataFieldSourceOverride>()
  ;(existingOverrides || []).forEach((o) => {
    existingMap.set(o.source_id, o)
  })

  sourceOverrides.value = sources.map((s) => {
    const existing = existingMap.get(s.id)
    const multi = Array.isArray(existing?.constant_values) ? existing.constant_values.map((v) => String(v)).filter(Boolean) : []
    const single = String(existing?.constant_value || '').trim() || multi[0] || ''
    return {
      _id: crypto.randomUUID(),
      source_id: s.id,
      source_name: s.name,
      source_type_key: s.type,
      constant_value: single,
      constant_values_text: multi.join(', '),
    }
  })
}

const getPresetExtractionHint = (name?: string | null): string | undefined => {
  const fieldName = (name || '').trim()
  if (!fieldName) return undefined
  return PRESET_FIELDS.find((p) => p.name === fieldName)?.llm_extraction_hint
}

// Computed values for variable substitution
const typeLabel = computed(() => ValueTypeOptions.find((o) => o.value === valueType.value)?.label || valueType.value)
const allowedValuesLabel = computed(() => {
  if (!restrictToAllowedValues.value) return 'any'
  return allowedValues.value.length ? allowedValues.value.map((v) => v.value).join(', ') : 'any'
})
const predefinedOptionsError = computed(() => showPredefinedOptionsError.value && restrictToAllowedValues.value && allowedValues.value.length === 0)
const defaultsLabel = computed(() => {
  if (isMultiple.value) {
    return defaultValues.value.length ? defaultValues.value.join(', ') : 'none'
  }
  return defaultValue.value.trim() || 'none'
})
const cardinalityLabel = computed(() => (isMultiple.value ? 'Multi-Value' : 'Single-Value'))
const displayNameLabel = computed(() => displayName.value.trim() || fieldName.value.trim() || 'Untitled')

const extractionVars = computed<Record<string, string>>(() => ({
  field_name: fieldName.value.trim() || 'field_name',
  display_name: displayNameLabel.value,
  type: typeLabel.value,
  values: allowedValuesLabel.value,
  defaults: defaultsLabel.value,
  cardinality: cardinalityLabel.value,
}))

// Render extraction hint with variable substitution
const renderedExtractionHint = computed(() => {
  const vars = extractionVars.value
  return extractionHint.value.replace(/\{(\w+)\}/g, (match, key) => vars[key] ?? match)
})

const formatExtractionVariableToken = (key: string) => `{${key}}`

const insertExtractionVariable = async (key: ExtractionVariableKey) => {
  if (extractionMode.value === 'disabled') return

  const token = `{${key}}`
  const pos = extractionHintInputRef.value?.getCursorIndex?.()
  const cursor = typeof pos === 'number' ? pos : extractionHint.value.length

  const text = extractionHint.value || ''
  const before = text.slice(0, cursor)
  const after = text.slice(cursor)

  const needsSpaceBefore = before.length > 0 && !/\s$/.test(before) && !/[([{]$/.test(before)
  const needsSpaceAfter = after.length > 0 && !/^\s/.test(after) && !/^[,.;:!?)}\]]/.test(after)
  const insertion = `${needsSpaceBefore ? ' ' : ''}${token}${needsSpaceAfter ? ' ' : ''}`

  extractionHint.value = before + insertion + after

  await nextTick()

  const nativeEl = extractionHintInputRef.value?.input?.nativeEl as HTMLTextAreaElement | HTMLInputElement | undefined
  const newPos = cursor + insertion.length

  if (nativeEl && typeof nativeEl.setSelectionRange === 'function') {
    nativeEl.focus?.()
    nativeEl.setSelectionRange(newPos, newPos)
  } else {
    extractionHintInputRef.value?.focus?.()
  }
}

// Reset to default template
const resetToDefaultTemplate = () => {
  extractionHint.value = DEFAULT_EXTRACTION_TEMPLATE
}

// Methods for checking/toggling default values
const isValueDefault = (value: string): boolean => {
  if (isMultiple.value) {
    return defaultValues.value.includes(value)
  }
  return defaultValue.value === value
}

const toggleDefault = (value: string) => {
  if (isMultiple.value) {
    // Multiple mode: toggle in array
    const idx = defaultValues.value.indexOf(value)
    if (idx >= 0) {
      defaultValues.value.splice(idx, 1)
    } else {
      defaultValues.value.push(value)
    }
  } else {
    // Single-Value mode: toggle or switch
    if (defaultValue.value === value) {
      defaultValue.value = ''
    } else {
      defaultValue.value = value
    }
  }
}

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
  const removedValue = allowedValues.value[idx].value
  allowedValues.value.splice(idx, 1)
  // Also remove from defaults if it was default
  if (isMultiple.value) {
    const defIdx = defaultValues.value.indexOf(removedValue)
    if (defIdx >= 0) {
      defaultValues.value.splice(defIdx, 1)
    }
  } else if (defaultValue.value === removedValue) {
    defaultValue.value = ''
  }
}

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
        isMultiple.value = !!props.field.is_multiple
        restrictToAllowedValues.value = !!props.field.allowed_values?.length
        defaultValue.value = props.field.default_value || ''
        defaultValues.value = props.field.default_values || []
        allowedValues.value = props.field.allowed_values || []
        extractionHint.value = props.field.llm_extraction_hint || getPresetExtractionHint(props.field.name) || DEFAULT_EXTRACTION_TEMPLATE
        // Determine extraction mode from saved data
        if (props.field.is_required) {
          extractionMode.value = 'mandatory'
        } else if (props.field.llm_extraction_hint) {
          extractionMode.value = 'optional'
        } else {
          extractionMode.value = 'disabled'
        }
        showPreview.value = false
        showPredefinedOptionsError.value = false

        initSourceOverrides(props.field.source_overrides)
      } else {
        // Reset for new field
        fieldName.value = ''
        displayName.value = ''
        description.value = ''
        valueType.value = 'string'
        isMultiple.value = false
        restrictToAllowedValues.value = false
        defaultValue.value = ''
        defaultValues.value = []
        allowedValues.value = []
        newAllowedValue.value = ''
        extractionHint.value = DEFAULT_EXTRACTION_TEMPLATE
        extractionMode.value = 'disabled'
        showPreview.value = false
        showPredefinedOptionsError.value = false
        initSourceOverrides()
      }
    }
  },
  { immediate: true }
)

// Keep override inputs sane when switching between single/multi value fields
watch(isMultiple, (multi) => {
  if (multi) {
    sourceOverrides.value.forEach((ov) => {
      if (!ov.constant_values_text.trim() && ov.constant_value.trim()) {
        ov.constant_values_text = ov.constant_value.trim()
      }
    })
  } else {
    sourceOverrides.value.forEach((ov) => {
      if (!ov.constant_value.trim()) {
        const parsed = parseCommaSeparated(ov.constant_values_text)
        if (parsed.length) ov.constant_value = parsed[0]
      }
    })
  }
})

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
  // Validate field name before saving
  if (fieldNameInputRef.value && !fieldNameInputRef.value.validate()) {
    return
  }

  // Validate predefined options
  showPredefinedOptionsError.value = true
  if (restrictToAllowedValues.value && allowedValues.value.length === 0) {
    return
  }

  // When saving, render the extraction hint with actual values (not variables)
  const finalExtractionHint = extractionMode.value !== 'disabled' ? renderedExtractionHint.value.trim() : undefined

  const overrides: MetadataFieldSourceOverride[] = []
  for (const ov of sourceOverrides.value) {
    const sid = ov.source_id.trim()
    const single = ov.constant_value.trim()
    const multi = parseCommaSeparated(ov.constant_values_text)

    const isEmpty = !sid && !single && multi.length === 0
    if (isEmpty) continue

    if (isMultiple.value) {
      const values = multi.length ? multi : single ? [single] : []
      if (sid && values.length) overrides.push({ source_id: sid, constant_values: values })
    } else {
      const value = single || multi[0] || ''
      if (sid && value) overrides.push({ source_id: sid, constant_value: value })
    }
  }

  const field: MetadataFieldDefinition = {
    id: props.field?.id || crypto.randomUUID(),
    name: fieldName.value.trim(),
    display_name: displayName.value.trim() || fieldName.value.trim(),
    description: description.value.trim(),
    value_type: valueType.value,
    is_multiple: isMultiple.value,
    is_required: isRequired.value,
    allowed_values: restrictToAllowedValues.value && allowedValues.value.length > 0 ? allowedValues.value : undefined,
    default_value: !isMultiple.value && defaultValue.value.trim() ? defaultValue.value.trim() : undefined,
    default_values: isMultiple.value && defaultValues.value.length > 0 ? defaultValues.value : undefined,
    llm_extraction_hint: finalExtractionHint || undefined,
    source_overrides: overrides.length ? overrides : undefined,
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
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
}

.value-option-chip:hover {
  border-color: var(--q-primary);
  background: rgba(var(--q-primary-rgb), 0.03);
}

.value-option-chip--default {
  border-color: var(--q-primary);
  background: rgba(var(--q-primary-rgb), 0.08);
  box-shadow: 0 0 0 1px rgba(var(--q-primary-rgb), 0.2);
}

.value-option-check {
  color: var(--q-control-border);
  transition: color 0.15s ease;
}

.value-option-chip--default .value-option-check {
  color: var(--q-primary);
}

.value-option-text {
  font-weight: 500;
  color: #444;
}

.value-option-chip--default .value-option-text {
  color: var(--q-primary);
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

/* Smart Extraction Section */
.extraction-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.extraction-content--disabled {
  opacity: 0.5;
}

.extraction-subtoolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.extraction-variables-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.extraction-var-chip {
  color: #5c6670;
}

.extraction-var-chip:hover {
  color: var(--q-primary);
  background: rgba(var(--q-primary-rgb), 0.04);
}

.extraction-var-token {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 11px;
  line-height: normal !important;
}

.extraction-toolbar {
  display: flex;
  align-items: center;
  gap: 4px;
}

.extraction-preview {
  background: #f8f9fa;
  border: 1px dashed var(--q-control-border);
  border-radius: 4px;
  padding: 8px 10px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 11px;
  line-height: 1.4;
  color: #555;
  white-space: pre-wrap;
}

.overrides-source-cell {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 36px;
  padding: 0 12px;
  border: 1px solid var(--q-control-border);
  border-radius: 4px;
}

.overrides-source-logo {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.overrides-source-name {
  font-size: 13px;
  font-weight: 500;
  color: #2d2438;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
