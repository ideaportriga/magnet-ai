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
          <kg-field-row label="Field Name">
            <km-input ref="fieldNameInputRef" v-model="fieldName" height="36px" />
          </kg-field-row>
          <kg-field-row label="Display Name">
            <km-input v-model="displayName" height="36px" />
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

      <!-- Field & Value Mappings -->
      <kg-dialog-section
        title="Field & Value Mappings"
        description="Configure which metadata fields and values map to this field definition, and set the resolution priority per source"
        icon="layers"
      >
        <div v-if="!hasSourceOptions" class="text-caption text-grey-6 italic">No sources available in this knowledge graph.</div>

        <div v-else class="value-resolution">
          <!-- Expandable source sections -->
          <div class="source-sections">
            <div
              v-for="source in sourceValueResolutions"
              :key="source._id"
              class="source-section"
              :class="{ 'source-section--expanded': activeResolutionSourceId === source.source_id }"
            >
              <!-- Source header (click to expand) -->
              <div class="source-section__header" @click="toggleSourceSection(source.source_id)">
                <div class="source-section__left">
                  <q-icon
                    :name="activeResolutionSourceId === source.source_id ? 'keyboard_arrow_down' : 'keyboard_arrow_right'"
                    size="20px"
                    color="grey-7"
                    class="source-section__chevron"
                  />
                  <span class="source-section__type">{{ getSourceTypeName(source.source_type_key) }}</span>
                  <span class="source-section__name">{{ source.source_name }}</span>
                </div>
                <div class="source-section__right">
                  <span v-if="source.chain.length > 0" class="source-section__badge">
                    {{ source.chain.length }} step{{ source.chain.length > 1 ? 's' : '' }}
                  </span>
                  <span v-else class="source-section__badge source-section__badge--empty">Not configured</span>
                </div>
              </div>

              <!-- Source content (expandable) -->
              <div v-if="activeResolutionSourceId === source.source_id" class="source-section__content">
                <div class="source-section__toolbar">
                  <span class="source-section__hint">First non-empty value wins, drag to reorder</span>
                  <!-- Origin buttons -->
                  <div class="origin-buttons">
                    <button
                      type="button"
                      class="origin-btn origin-btn--file"
                      :class="{ 'origin-btn--disabled': !canAddKind('file') }"
                      :disabled="!canAddKind('file')"
                      @click="addChainStep('file')"
                    >
                      <q-icon name="description" size="12px" />
                      <span>File</span>
                    </button>
                    <button
                      type="button"
                      class="origin-btn origin-btn--source"
                      :class="{ 'origin-btn--disabled': !canAddKind('source') }"
                      :disabled="!canAddKind('source')"
                      @click="addChainStep('source')"
                    >
                      <q-icon name="cloud_download" size="12px" />
                      <span>Source</span>
                    </button>
                    <button
                      type="button"
                      class="origin-btn origin-btn--llm"
                      :class="{ 'origin-btn--disabled': !canAddKind('llm') }"
                      :disabled="!canAddKind('llm')"
                      @click="addChainStep('llm')"
                    >
                      <q-icon name="smart_toy" size="12px" />
                      <span>LLM</span>
                    </button>
                    <button
                      type="button"
                      class="origin-btn origin-btn--constant"
                      :class="{ 'origin-btn--disabled': !canAddKind('constant') }"
                      :disabled="!canAddKind('constant')"
                      @click="addChainStep('constant')"
                    >
                      <q-icon name="pin" size="12px" />
                      <span>Constant</span>
                    </button>
                  </div>
                </div>

                <!-- Chain -->
                <VueDraggable
                  v-model="activeResolutionNonConstantChain"
                  handle=".value-chain__handle"
                  class="value-chain"
                  :disabled="activeResolutionNonConstantChain.length <= 1"
                  @end="sanitizeActiveSourceChain"
                >
                  <div
                    v-for="(step, stepIndex) in activeResolutionNonConstantChain"
                    :key="step._id"
                    class="value-chain__item"
                    :class="`value-chain__item--${step.kind}`"
                  >
                    <div class="value-chain__handle" :class="{ 'value-chain__handle--disabled': activeResolutionNonConstantChain.length <= 1 }">
                      <q-icon name="drag_indicator" size="16px" color="grey-5" />
                    </div>

                    <div class="value-chain__body">
                      <div class="value-chain__number">{{ stepIndex + 1 }}</div>
                      <div class="value-chain__kind">
                        <q-icon :name="valueSourceKindIcon(step.kind)" size="18px" :color="valueSourceKindColor(step.kind)" />
                        <span class="value-chain__kind-label">{{ valueSourceKindLabel(step.kind) }}</span>
                      </div>

                      <div class="value-chain__config">
                        <template v-if="step.kind === 'llm'">
                          <kg-dropdown-field
                            v-model="step.field_name"
                            :options="smartExtractionFieldOptions(step.field_name)"
                            placeholder="Select extraction field"
                            option-value="value"
                            option-label="label"
                            :option-meta="(o) => o.meta"
                            searchable
                            clearable
                            dense
                            :show-error="showValueResolutionErrors && !step.field_name"
                          />
                          <div v-if="showValueResolutionErrors && !step.field_name" class="value-chain__error">Required</div>
                        </template>

                        <template v-else>
                          <kg-dropdown-field
                            v-model="step.field_name"
                            :options="fieldOptionsForStep(step.kind, activeResolutionSource.source_id, step.field_name)"
                            placeholder="Select field"
                            option-value="value"
                            option-label="label"
                            :option-meta="(o) => o.meta"
                            searchable
                            clearable
                            dense
                            :show-error="showValueResolutionErrors && !step.field_name"
                          />
                          <div v-if="showValueResolutionErrors && !step.field_name" class="value-chain__error">Required</div>
                        </template>
                      </div>
                    </div>

                    <div class="value-chain__close">
                      <q-btn icon="close" size="sm" round flat @click="removeChainStep(step._id)" />
                    </div>
                  </div>
                </VueDraggable>

                <!-- Constant (fixed, terminal) -->
                <div v-if="activeResolutionConstantStep" class="value-chain__item value-chain__item--constant">
                  <div class="value-chain__handle value-chain__handle--disabled">
                    <q-icon name="drag_indicator" size="16px" color="grey-5" />
                  </div>

                  <div class="value-chain__body">
                    <div class="value-chain__number">{{ activeResolutionNonConstantChain.length + 1 }}</div>
                    <div class="value-chain__kind">
                      <q-icon
                        :name="valueSourceKindIcon(activeResolutionConstantStep.kind)"
                        size="14px"
                        :color="valueSourceKindColor(activeResolutionConstantStep.kind)"
                      />
                      <span class="value-chain__kind-label">{{ valueSourceKindLabel(activeResolutionConstantStep.kind) }}</span>
                    </div>

                    <div class="value-chain__config">
                      <km-input
                        v-model="activeResolutionConstantStep.constant_value"
                        placeholder="Enter value (or comma-separated values)"
                        :class="{
                          'value-chain__input--error':
                            showValueResolutionErrors &&
                            !activeResolutionConstantStep.constant_value.trim() &&
                            parseCommaSeparated(activeResolutionConstantStep.constant_values_text).length === 0,
                        }"
                      />
                      <div
                        v-if="
                          showValueResolutionErrors &&
                            !activeResolutionConstantStep.constant_value.trim() &&
                            parseCommaSeparated(activeResolutionConstantStep.constant_values_text).length === 0
                        "
                        class="value-chain__error"
                      >
                        Required
                      </div>
                    </div>
                  </div>

                  <div class="value-chain__close">
                    <q-btn icon="close" size="sm" round flat @click="removeChainStep(activeResolutionConstantStep._id)" />
                  </div>
                </div>

                <div v-if="source.chain.length === 0" class="value-chain__empty">
                  <q-icon name="add_circle_outline" size="18px" color="grey-5" />
                  <span>Add steps to define how this field is populated</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </kg-dialog-section>
    </div>
  </kg-dialog-base>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { VueDraggable } from 'vue-draggable-plus'
import { KgDialogBase, KgDialogSection, KgDropdownField, KgFieldRow } from '../common'
import { type SourceRow, getSourceTypeName } from '../Sources/models'
import {
  MetadataDiscoveredField,
  MetadataExtractedField,
  MetadataFieldDefinition,
  MetadataFieldSourceValueResolution,
  MetadataFieldValueSourceKind,
  MetadataFieldValueSourceStep,
} from './models'

const props = defineProps<{
  showDialog: boolean
  field?: MetadataFieldDefinition | null
  existingFieldNames?: string[]
  sources?: SourceRow[]
  discoveredFields?: MetadataDiscoveredField[]
  extractedFields?: MetadataExtractedField[]
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
const loading = ref(false)
const fieldNameInputRef = ref<any>(null)
const showValueResolutionErrors = ref(false)

type ValueResolutionStepDraft = {
  _id: string
  kind: MetadataFieldValueSourceKind
  field_name: string
  constant_value: string
  constant_values_text: string
}

type SourceValueResolutionDraft = {
  _id: string
  source_id: string
  source_name: string
  source_type_key: string
  chain: ValueResolutionStepDraft[]
}

const sourceValueResolutions = ref<SourceValueResolutionDraft[]>([])
const activeResolutionSourceId = ref<string>('')

const discoveredFields = computed(() => props.discoveredFields || [])

const parseCommaSeparated = (text: string): string[] => {
  const parsed = (text || '')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
  return Array.from(new Set(parsed))
}

const hasSourceOptions = computed(() => (props.sources || []).length > 0)

const sanitizeChain = (chain: ValueResolutionStepDraft[]): ValueResolutionStepDraft[] => {
  const out: ValueResolutionStepDraft[] = []
  const seen = new Set<MetadataFieldValueSourceKind>()
  for (const step of chain || []) {
    if (!step?.kind) continue
    if (seen.has(step.kind)) continue
    seen.add(step.kind)
    out.push(step)
  }
  const constIdx = out.findIndex((s) => s.kind === 'constant')
  if (constIdx >= 0 && constIdx !== out.length - 1) {
    const [c] = out.splice(constIdx, 1)
    out.push(c)
  }
  return out
}

const initSourceValueResolution = (existingResolution?: MetadataFieldSourceValueResolution[]) => {
  const sources = props.sources || []
  const existingMap = new Map<string, MetadataFieldSourceValueResolution>()
  ;(existingResolution || []).forEach((r) => {
    if (r?.source_id) existingMap.set(r.source_id, r)
  })

  sourceValueResolutions.value = sources.map((s) => {
    const existing = existingMap.get(s.id)

    const chain: ValueResolutionStepDraft[] = []

    if (existing?.chain?.length) {
      for (const st of existing.chain) {
        const kind = st?.kind
        if (!kind) continue
        if (kind === 'constant') {
          const multi = Array.isArray(st.constant_values) ? st.constant_values.map((v) => String(v)).filter(Boolean) : []
          const single = String(st.constant_value || '').trim() || multi[0] || ''
          chain.push({
            _id: crypto.randomUUID(),
            kind,
            field_name: '',
            constant_value: single,
            constant_values_text: multi.join(', '),
          })
        } else {
          chain.push({
            _id: crypto.randomUUID(),
            kind,
            field_name: String(st.field_name || '').trim(),
            constant_value: '',
            constant_values_text: '',
          })
        }
      }
    }

    return {
      _id: crypto.randomUUID(),
      source_id: s.id,
      source_name: s.name,
      source_type_key: s.type,
      chain: sanitizeChain(chain),
    }
  })

  // Default to all collapsed
  activeResolutionSourceId.value = ''
}

type SourceOption = { label: string; value: string }

const sourceOptions = computed<SourceOption[]>(() => {
  return (props.sources || []).map((s) => ({ label: s.name, value: s.id }))
})

const activeResolutionSource = computed<SourceValueResolutionDraft | null>(() => {
  const byId = sourceValueResolutions.value.find((s) => s.source_id === activeResolutionSourceId.value)
  return byId || sourceValueResolutions.value[0] || null
})

// Drag model: constant is fixed last (not draggable)
const activeResolutionNonConstantChain = computed<ValueResolutionStepDraft[]>({
  get: () => {
    const src = activeResolutionSource.value
    return src ? (src.chain || []).filter((s) => s.kind !== 'constant') : []
  },
  set: (v) => {
    const src = activeResolutionSource.value
    if (!src) return
    const constant = (src.chain || []).find((s) => s.kind === 'constant')
    src.chain = sanitizeChain([...(v || []), ...(constant ? [constant] : [])])
  },
})

const activeResolutionConstantStep = computed<ValueResolutionStepDraft | null>(() => {
  const src = activeResolutionSource.value
  if (!src) return null
  return (src.chain || []).find((s) => s.kind === 'constant') || null
})

// Keep active source selection stable if the selected source is removed.
watch(
  () => [props.showDialog, sourceValueResolutions.value.length] as const,
  () => {
    if (!props.showDialog) return
    if (!sourceValueResolutions.value.length) {
      activeResolutionSourceId.value = ''
      return
    }
    // Only reset if current selection is invalid (not found in sources), but allow empty
    if (activeResolutionSourceId.value) {
      const exists = sourceValueResolutions.value.some((s) => s.source_id === activeResolutionSourceId.value)
      if (!exists) {
        activeResolutionSourceId.value = ''
      }
    }
  }
)

watch(activeResolutionSourceId, () => {
  // Switching sources should not keep showing validation noise.
  showValueResolutionErrors.value = false
})

type FieldOption = { label: string; value: string; meta?: string }

const truncate = (value: string, max = 48) => {
  const s = String(value || '')
  return s.length > max ? s.slice(0, Math.max(max - 1, 1)) + '…' : s
}

const fieldOptionsForStep = (kind: MetadataFieldValueSourceKind, sourceId: string, selectedValue?: string): FieldOption[] => {
  if (kind === 'constant') return []

  const originForKind: Record<Exclude<MetadataFieldValueSourceKind, 'constant'>, string> = {
    file: 'file',
    llm: 'llm',
    source: 'source',
  }

  const desiredOrigin = originForKind[kind]
  let rows = discoveredFields.value.filter((r) => r.origin === desiredOrigin)

  if (sourceId) {
    rows = rows.filter((r) => r.source?.id === sourceId)
  }

  // De-dupe by field name, then sort
  const unique = new Map<string, MetadataDiscoveredField>()
  for (const r of rows) {
    if (!r?.name) continue
    if (!unique.has(r.name)) unique.set(r.name, r)
  }

  const opts: FieldOption[] = Array.from(unique.values())
    .sort((a, b) => String(a.name).localeCompare(String(b.name)))
    .map((r) => ({
      label: r.name,
      value: r.name,
      meta: r.sample_values?.length ? `e.g. ${truncate(r.sample_values[0])}` : undefined,
    }))

  const sel = String(selectedValue || '').trim()
  if (sel && !opts.some((o) => o.value === sel)) {
    opts.unshift({ label: sel, value: sel, meta: 'Not currently discovered' })
  }

  return opts
}

const smartExtractionFieldOptions = (selectedValue?: string): FieldOption[] => {
  const fields = props.extractedFields || []

  const opts: FieldOption[] = fields
    .slice()
    .sort((a, b) => String(a.name).localeCompare(String(b.name)))
    .map((f) => ({
      label: f.name,
      value: f.name,
      meta: f.sample_values?.length ? `e.g. ${truncate(f.sample_values[0])}` : undefined,
    }))

  const sel = String(selectedValue || '').trim()
  if (sel && !opts.some((o) => o.value === sel)) {
    opts.unshift({ label: sel, value: sel, meta: 'Field not found' })
  }

  return opts
}

const valueSourceKindLabel = (kind: MetadataFieldValueSourceKind) => {
  const labels: Record<MetadataFieldValueSourceKind, string> = {
    source: 'Source Metadata',
    file: 'File Metadata',
    llm: 'Smart Extraction',
    constant: 'Constant Value',
  }
  return labels[kind] || kind
}

const valueSourceKindIcon = (kind: MetadataFieldValueSourceKind) => {
  const icons: Record<MetadataFieldValueSourceKind, string> = {
    source: 'cloud_download',
    file: 'description',
    llm: 'smart_toy',
    constant: 'pin',
  }
  return icons[kind] || 'tune'
}

const valueSourceKindColor = (kind: MetadataFieldValueSourceKind) => {
  const colors: Record<MetadataFieldValueSourceKind, string> = {
    source: 'indigo-8',
    file: 'teal-8',
    llm: 'purple-8',
    constant: 'grey-8',
  }
  return colors[kind] || 'grey-8'
}

const canAddKind = (kind: MetadataFieldValueSourceKind) => {
  const src = activeResolutionSource.value
  if (!src) return false
  return !src.chain.some((s) => s.kind === kind)
}

const guessDefaultFieldName = (kind: Exclude<MetadataFieldValueSourceKind, 'constant'>, sourceId: string): string => {
  const desired = fieldName.value.trim()
  if (!desired) return ''
  const opts = kind === 'llm' ? smartExtractionFieldOptions(desired) : fieldOptionsForStep(kind, sourceId, desired)
  return opts.some((o) => o.value === desired) ? desired : ''
}

const sanitizeActiveSourceChain = () => {
  const src = activeResolutionSource.value
  if (!src) return
  src.chain = sanitizeChain(src.chain)
}

const addChainStep = (kind: MetadataFieldValueSourceKind) => {
  const src = activeResolutionSource.value
  if (!src) return
  if (!canAddKind(kind)) return

  const newStep: ValueResolutionStepDraft = {
    _id: crypto.randomUUID(),
    kind,
    field_name: '',
    constant_value: '',
    constant_values_text: '',
  }

  if (kind !== 'constant') {
    newStep.field_name = guessDefaultFieldName(kind, src.source_id)
  }

  const constIdx = src.chain.findIndex((s) => s.kind === 'constant')
  if (kind !== 'constant' && constIdx >= 0) {
    src.chain.splice(constIdx, 0, newStep)
  } else {
    src.chain.push(newStep)
  }

  src.chain = sanitizeChain(src.chain)
  showValueResolutionErrors.value = false
}

const removeChainStep = (stepId: string) => {
  const src = activeResolutionSource.value
  if (!src) return
  src.chain = sanitizeChain(src.chain.filter((s) => s._id !== stepId))
  showValueResolutionErrors.value = false
}

const resetActiveSourceChain = () => {
  const src = activeResolutionSource.value
  if (!src) return
  src.chain = []
  showValueResolutionErrors.value = false
}

const toggleSourceSection = (sourceId: string) => {
  if (activeResolutionSourceId.value === sourceId) {
    // Already expanded, collapse it
    activeResolutionSourceId.value = ''
    return
  }
  activeResolutionSourceId.value = sourceId
}

const applyActiveChainToAllSources = () => {
  const src = activeResolutionSource.value
  if (!src) return
  const base = sanitizeChain(src.chain)
  sourceValueResolutions.value = sourceValueResolutions.value.map((s) => ({
    ...s,
    chain: base.map((st) => ({
      ...st,
      _id: crypto.randomUUID(),
    })),
  }))
  showValueResolutionErrors.value = false
}

const isEditMode = computed(() => !!props.field?.id)

// Initialize form when dialog opens or field changes
watch(
  () => [props.showDialog, props.field] as const,
  () => {
    if (props.showDialog) {
      if (props.field) {
        fieldName.value = props.field.name
        displayName.value = props.field.display_name || ''
        description.value = props.field.description || ''
        showValueResolutionErrors.value = false

        initSourceValueResolution(props.field.source_value_resolution)
      } else {
        // Reset for new field
        fieldName.value = ''
        displayName.value = ''
        description.value = ''
        showValueResolutionErrors.value = false
        initSourceValueResolution()
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
  // Validate per-source value resolution chains (only if configured for a source)
  showValueResolutionErrors.value = true
  const invalid = sourceValueResolutions.value.some((src) => {
    if (!src.chain.length) return false
    return src.chain.some((step) => {
      if (step.kind === 'constant') {
        // For value resolution, we still need to handle constant steps
        // Use single value mode by default since we no longer have isMultiple here
        return !step.constant_value.trim() && parseCommaSeparated(step.constant_values_text).length === 0
      }
      // All other kinds (file, source, llm) require a field_name
      return !step.field_name.trim()
    })
  })
  if (invalid) return

  const valueResolution: MetadataFieldSourceValueResolution[] = []

  for (const src of sourceValueResolutions.value) {
    const sid = String(src.source_id || '').trim()
    if (!sid) continue

    const chain: MetadataFieldValueSourceStep[] = []
    for (const step of sanitizeChain(src.chain)) {
      if (step.kind === 'constant') {
        // Check if multiple values are provided
        const multiValues = parseCommaSeparated(step.constant_values_text)
        if (multiValues.length > 1) {
          chain.push({ kind: 'constant', constant_values: multiValues })
        } else {
          const v = step.constant_value.trim() || multiValues[0] || ''
          if (v) chain.push({ kind: 'constant', constant_value: v })
        }
      } else if (step.kind === 'llm') {
        // LLM value: use the selected smart extraction field
        const fname = step.field_name.trim()
        if (fname) chain.push({ kind: 'llm', field_name: fname })
      } else {
        const fname = step.field_name.trim()
        if (fname) chain.push({ kind: step.kind, field_name: fname })
      }
    }

    if (chain.length) {
      valueResolution.push({ source_id: sid, chain })
    }
  }

  const field: MetadataFieldDefinition = {
    id: props.field?.id || crypto.randomUUID(),
    name: fieldName.value.trim(),
    display_name: displayName.value.trim() || fieldName.value.trim(),
    description: description.value.trim(),
    source_value_resolution: valueResolution.length ? valueResolution : undefined,
  }
  emit('save', field)
}
</script>

<style scoped>
/* Value Resolution - Source Sections */
.value-resolution {
  display: flex;
  flex-direction: column;
}

.source-sections {
  display: flex;
  flex-direction: column;
  gap: 1px;
  border: 1px solid #e2e5e9;
  border-radius: 4px;
  overflow: hidden;
  background: #e2e5e9;
}

.source-section {
  background: #fff;
}

.source-section__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.source-section__header:hover {
  background: #f8f9fa;
}

.source-section--expanded .source-section__header {
  background: #f4f5f7;
  border-bottom: 1px solid #e2e5e9;
}

.source-section__left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.source-section__chevron {
  flex-shrink: 0;
  transition: transform 0.15s ease;
}

.source-section__type {
  font-size: 11px;
  font-weight: 600;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 2px 6px;
  background: #f0f0f0;
  border-radius: 3px;
  flex-shrink: 0;
}

.source-section__name {
  font-size: 13px;
  font-weight: 500;
  color: #2d3748;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.source-section__right {
  flex-shrink: 0;
}

.source-section__badge {
  font-size: 11px;
  font-weight: 500;
  padding: 4px 10px;
  border-radius: 10px;
  background: #e8f4ea;
  color: #2e7d42;
}

.source-section__badge--empty {
  background: #f5f5f5;
  color: #888;
}

.source-section__content {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: #fafbfc;
}

.source-section__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.source-section__hint {
  font-size: 11px;
  color: #888;
  flex-shrink: 0;
}

/* Value Chain Items */
.value-chain {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.value-chain__item {
  display: flex;
  align-items: stretch;
  gap: 0;
  border: 1px solid #e2e5e9;
  border-radius: 6px;
  background: #fff;
  overflow: hidden;
}

.value-chain__handle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  flex-shrink: 0;
  cursor: grab;
  user-select: none;
}

.value-chain__handle--disabled {
  cursor: default;
  opacity: 0.4;
}

.value-chain__body {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
  padding: 8px 0 8px 10px;
}

.value-chain__number {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  font-size: 10px;
  font-weight: 600;
  color: #666;
  background: #fff;
  border: 1px solid #d0d5dd;
  border-radius: 50%;
}

.value-chain__kind {
  display: inline-flex;
  align-items: center;
  justify-content: flex-start;
  gap: 6px;
  width: 144px;
  height: 32px;
  padding: 0 10px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
  flex-shrink: 0;
  background: #f6f7f8;
  color: #555;
}

.value-chain__kind-label {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.01em;
}

.value-chain__config {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 0;
}

.value-chain__llm-hint {
  display: flex;
  align-items: center;
  height: 32px;
  font-size: 12px;
  color: #888;
}

.value-chain__error {
  font-size: 10px;
  color: var(--q-error-text);
  padding-left: 2px;
}

.value-chain__close {
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 6px;
  flex-shrink: 0;
  background: none;
  border: none;
  color: #aaa;
  cursor: pointer;
}

.value-chain__close :deep(.q-focus-helper) {
  background: none !important;
}

.value-chain__close:hover {
  color: #c00;
}

.value-chain__empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px;
  border: 1px dashed #d8dce0;
  border-radius: 6px;
  background: #fff;
  font-size: 12px;
  color: #888;
}

/* Origin Buttons */
.origin-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.origin-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  border: 1px solid;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  background: #fff;
}

.origin-btn--file {
  border-color: #00897b;
  color: #00897b;
}

.origin-btn--file:hover:not(:disabled) {
  background: #e0f2f1;
}

.origin-btn--source {
  border-color: #3949ab;
  color: #3949ab;
}

.origin-btn--source:hover:not(:disabled) {
  background: #e8eaf6;
}

.origin-btn--llm {
  border-color: #8e24aa;
  color: #8e24aa;
}

.origin-btn--llm:hover:not(:disabled) {
  background: #f3e5f5;
}

.origin-btn--constant {
  border-color: #616161;
  color: #616161;
}

.origin-btn--constant:hover:not(:disabled) {
  background: #f5f5f5;
}

.origin-btn--disabled {
  border-style: dashed;
  opacity: 0.4;
  cursor: not-allowed;
}

.value-chain__input--error :deep(.q-field__control:before) {
  border-color: var(--q-negative) !important;
}
</style>
