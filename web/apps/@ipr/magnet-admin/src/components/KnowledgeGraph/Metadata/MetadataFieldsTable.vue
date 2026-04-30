<template>
  <div class="metadata-board" :class="{ 'metadata-board--dragging': isDragging }">
    <km-linear-progress v-if="loading" indeterminate class="mb-sm" />

    <!-- 4-Lane Board -->
    <div v-else class="board-lanes">
      <!-- Lane 1: Discovered -->
      <div class="board-lane">
        <div class="lane-header">
          <div class="lane-header__title">
            <km-glyph name="explore" size="18px" tone="accent" />
            <span>{{ m.knowledgeGraph_discovered() }}</span>
            <span class="lane-header__count">{{ discoveredRows.length }}</span>
          </div>
          <div class="lane-header__subtitle">{{ m.knowledgeGraph_autoDetected() }}</div>
        </div>
        <div class="lane-content">
          <div v-if="discoveredRows.length === 0" class="lane-empty">
            <km-glyph name="check" size="32px" tone="muted" />
            <span>{{ search ? m.knowledgeGraph_noMatchesInSearch() : m.knowledgeGraph_noNewFields() }}</span>
          </div>
          <div
            v-for="row in discoveredRows"
            :key="row.id"
            class="field-card"
            :class="{ 'field-card--defined': row.is_defined, 'field-card--dragging': draggedField?.id === row.id }"
            :draggable="!row.is_defined"
            @dragstart="onDragStart($event, row)"
            @dragend="onDragEnd"
          >
            <div class="field-card__header">
              <div class="field-card__name-row">
                <span class="field-card__name">{{ row.name }}</span>
              </div>
              <template v-if="row.source">
                <span class="source-badge source-badge--top-right">
                  <span class="source-badge__name">{{ row.source.name }}</span>
                </span>
              </template>
            </div>
            <div class="field-card__type-row">
              <div class="field-card__type">{{ getTypeLabel(row.value_type) }}</div>
              <span v-if="row.origin" class="field-card__type-delimiter">•</span>
              <span v-if="row.origin" class="origin-chip origin-chip--type-style" :class="`origin-chip--${row.origin}`">
                {{ getOriginLabel(row.origin) }}
              </span>
            </div>
            <div class="field-card__samples">
              <template v-if="row.sample_values?.length">
                <span v-for="sample in row.sample_values.slice(0, 2)" :key="sample" class="sample-chip">
                  {{ truncateValue(sample, 14) }}
                </span>
                <span v-if="row.sample_values.length > 2" class="sample-more">+{{ row.sample_values.length - 2 }}</span>
              </template>
              <div class="field-card__actions field-card__actions--samples">
                <template v-if="row.is_defined">
                  <km-btn flat dense size="sm" tone="weak" icon="edit" :tooltip="m.knowledgeGraph_editSchema()" @click.stop="editDefinedField(row)" />
                </template>
                <template v-else>
                  <km-btn flat dense size="sm" tone="accent" icon="add-circle" :tooltip="m.knowledgeGraph_addToSchema()" @click.stop="emit('promote-field', row)" />
                  <km-btn flat dense size="sm" tone="danger" icon="o_block" :tooltip="m.knowledgeGraph_ignoreField()" @click.stop="emit('discard-field', row.name)" />
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Lane 2: Smart Extraction -->
      <div class="board-lane board-lane--ai">
        <div class="lane-header">
          <div class="lane-header__top">
            <div class="lane-header__title">
              <km-glyph name="magic" size="18px" tone="context" />
              <span>{{ m.knowledgeGraph_smartExtraction() }}</span>
              <span class="lane-header__count">{{ extractedRows.length }}</span>
            </div>
            <div class="lane-header__actions">
              <km-btn round flat dense class="lane-icon-btn lane-icon-btn--ai" icon="add-circle" :tooltip="m.knowledgeGraph_addField()" @click.stop="emit('add-extraction-field')" />
              <km-btn round flat dense class="lane-icon-btn lane-icon-btn--ai" icon="settings" :tooltip="m.common_settings()" @click.stop="emit('open-extraction-settings')" />
              <km-btn
                v-if="canRunExtraction"
                round
                flat
                dense
                class="lane-icon-btn lane-icon-btn--run"
                icon="play"
                :loading="runningExtraction"
                :disable="runningExtraction"
                :tooltip="m.knowledgeGraph_runExtractionTooltip()" @click.stop="emit('run-extraction')"
              />
            </div>
          </div>
          <div class="lane-header__subtitle">{{ m.knowledgeGraph_smartExtractionDesc() }}</div>
        </div>
        <div class="lane-content">
          <div v-if="extractedRows.length === 0" class="lane-empty">
            <km-glyph name="robot" size="32px" tone="muted" />
            <span>{{ search ? m.knowledgeGraph_noMatchesInSearch() : m.knowledgeGraph_noExtractionFields() }}</span>
            <span v-if="!search" class="lane-empty__hint">{{ m.knowledgeGraph_addFieldsHint() }}</span>
          </div>
          <div
            v-for="row in extractedRows"
            :key="row.id"
            class="field-card field-card--ai"
            :class="{ 'field-card--dragging': draggedExtractionField?.id === row.id }"
            draggable="true"
            @dragstart="onExtractionDragStart($event, row)"
            @dragend="onDragEnd"
          >
            <div class="field-card__header">
              <div class="field-card__name-row">
                <span class="field-card__name">{{ row.name }}</span>
              </div>
            </div>
            <div class="field-card__type">{{ getTypeLabel(row.value_type) }}</div>
            <div class="field-card__samples">
              <template v-if="row.sample_values?.length">
                <span v-for="sample in row.sample_values.slice(0, 2)" :key="sample" class="sample-chip">
                  {{ truncateValue(sample, 14) }}
                </span>
                <span v-if="row.sample_values.length > 2" class="sample-more">+{{ row.sample_values.length - 2 }}</span>
              </template>
              <div class="field-card__actions field-card__actions--samples">
                <km-btn flat dense size="sm" tone="weak" icon="edit" :tooltip="m.common_edit()" @click.stop="emit('edit-extraction-field', row)" />
                <km-btn flat dense size="sm" tone="danger" icon="delete" :tooltip="m.common_delete()" @click.stop="emit('delete-extraction-field', row)" />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Lane 3: Schema -->
      <div class="board-lane board-lane--schema">
        <div class="lane-header">
          <div class="lane-header__top">
            <div class="lane-header__title">
              <km-glyph name="tune" size="18px" tone="info" />
              <span>{{ m.knowledgeGraph_schemaLane() }}</span>
              <span class="lane-header__count">{{ schemaRows.length }}</span>
            </div>
            <div class="lane-header__actions">
              <km-btn round flat dense class="lane-icon-btn lane-icon-btn--schema" icon="add-circle" :tooltip="m.knowledgeGraph_addField()" @click.stop="emit('add-field')" />
            </div>
          </div>
          <div class="lane-header__subtitle">{{ m.knowledgeGraph_schemaLaneDesc() }}</div>
        </div>
        <div
          class="lane-content"
          :class="{ 'lane-content--drag-over': isDragOverSchema }"
          @dragenter="onSchemaDragEnter"
          @dragover.prevent="onSchemaDragOver"
          @dragleave="onSchemaDragLeave"
          @drop="onSchemaDrop($event)"
        >
          <div v-if="schemaRows.length === 0" class="lane-empty lane-empty--drop-target">
            <km-glyph name="category" size="32px" tone="muted" />
            <span>{{ isDragOverSchema ? m.knowledgeGraph_dropToCreateField() : search ? m.knowledgeGraph_noMatchesInSearch() : m.knowledgeGraph_noSchemaFieldsShort() }}</span>
          </div>
          <div
            v-for="row in schemaRows"
            :key="row.id"
            class="field-card field-card--schema"
            :class="{ 'field-card--drop-target': dragOverSchemaFieldId === row.id }"
            @click="emit('edit-field', row)"
            @dragenter="onSchemaFieldDragEnter($event, row)"
            @dragover.prevent.stop="onSchemaFieldDragOver($event)"
            @dragleave="onSchemaFieldDragLeave($event, row)"
            @drop.stop="onSchemaFieldDrop($event, row)"
          >
            <div class="field-card__header">
              <span class="field-card__name">{{ row.display_name || row.name }}</span>
              <!-- Source Resolution Status -->
              <div v-if="sources.length > 0" class="field-card__sources field-card__sources--top-right">
                <template v-if="getSourceResolutionStatus(row).configured.length === sources.length">
                  <div class="source-status source-status--resolved">
                    <km-glyph name="check" size="14px" />
                  </div>
                </template>
                <template v-else>
                  <div class="source-status source-status--unresolved">
                    <km-glyph name="error" size="14px" />
                    <span>{{ getSourceResolutionStatus(row).configured.length }}/{{ sources.length }} sources</span>
                  </div>
                </template>
                <km-tooltip class="source-tooltip" :offset="[0, 6]">
                  <div class="source-tooltip__content">
                    <div class="source-tooltip__header">
                      <span>{{ m.knowledgeGraph_sourceResolution() }}</span>
                      <span class="source-tooltip__meta">{{ getSourceResolutionStatus(row).configured.length }}/{{ sources.length }}</span>
                    </div>
                    <div v-if="getSourceResolutionStatus(row).hasWildcard" class="source-tooltip__wildcard">{{ m.knowledgeGraph_appliesToAllSources() }}</div>
                    <div v-else class="source-tooltip__list">
                      <div
                        v-for="src in sources"
                        :key="src.id"
                        class="source-tooltip__row"
                        :class="{ 'source-tooltip__row--missing': getSourceResolutionStatus(row).missing.some((m) => m.id === src.id) }"
                      >
                        <span class="source-tooltip__name">{{ src.name }}</span>
                        <km-glyph
                          :name="getSourceResolutionStatus(row).configured.some((c) => c.id === src.id) ? 'check' : 'remove'"
                          size="12px"
                          class="source-tooltip__status"
                        />
                      </div>
                    </div>
                  </div>
                </km-tooltip>
              </div>
            </div>
            <div v-if="getSchemaFieldType(row)" class="field-card__type">{{ getSchemaFieldType(row) }}</div>
            <div class="field-card__samples">
              <div class="field-card__actions field-card__actions--samples">
                <km-btn flat dense size="sm" tone="weak" icon="edit" :tooltip="m.common_edit()" @click.stop="emit('edit-field', row)" />
                <km-btn flat dense size="sm" tone="danger" icon="delete" :tooltip="m.common_delete()" @click.stop="emit('delete-field', row)" />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Lane 4: Discarded (Collapsible) -->
      <div
        class="board-lane board-lane--discarded"
        :class="{ 'board-lane--collapsed': !discardedExpanded, 'board-lane--drag-over': isDragOverDiscard }"
        @dragenter="onDiscardDragEnter"
        @dragover.prevent="onDiscardDragOver"
        @dragleave="onDiscardDragLeave"
        @drop="onDiscardDrop"
      >
        <div class="lane-header lane-header--clickable" @click="discardedExpanded = !discardedExpanded">
          <div class="lane-header__title">
            <km-glyph :name="discardedExpanded ? 'chevron-up' : 'chevron-down'" size="18px" tone="muted" class="collapse-icon" />
            <km-glyph v-if="discardedExpanded" name="block" size="18px" tone="muted" />
            <span>{{ m.knowledgeGraph_discarded() }}</span>
            <span v-if="discardedExpanded" class="lane-header__count">{{ discardedRows.length }}</span>
          </div>
          <div v-if="discardedExpanded" class="lane-header__subtitle">{{ m.knowledgeGraph_hiddenFromReview() }}</div>
          <div v-else class="lane-header__subtitle lane-header__subtitle--collapsed">{{ m.knowledgeGraph_clickToExpand() }}</div>
        </div>
        <transition name="lane-expand">
          <div v-if="discardedExpanded" class="lane-content">
            <div v-if="discardedRows.length === 0" class="lane-empty">
              <km-glyph name="check" size="32px" tone="muted" />
              <span>{{ search ? m.knowledgeGraph_noMatchesInSearch() : m.knowledgeGraph_nothingDiscarded() }}</span>
            </div>
            <div v-for="row in discardedRows" :key="row.id" class="field-card field-card--discarded">
              <div class="field-card__header">
                <span class="field-card__name">{{ row.name }}</span>
                <div class="field-card__actions">
                  <km-btn flat dense size="sm" tone="brand" :label="m.knowledgeGraph_restore()" @click.stop="emit('restore-field', row.name)" />
                  <km-btn flat dense size="sm" tone="weak" :label="m.knowledgeGraph_define()" @click.stop="emit('promote-field', row)" />
                </div>
              </div>
              <div class="field-card__type">{{ getTypeLabel(row.value_type) }}</div>
              <div class="field-card__meta">
                <span v-if="row.origin" class="origin-chip origin-chip--muted">
                  {{ row.origin === 'llm' ? 'AI' : getOriginLabel(row.origin) }}
                </span>
              </div>
            </div>
          </div>
        </transition>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import confluenceImage from '@/assets/brands/atlassian-confluence.png'
import { m } from '@/paraglide/messages'
import fluidTopicsImage from '@/assets/brands/fluid-topics.png'
import sharepointImage from '@/assets/brands/sharepoint.svg'
import { computed, ref, watch } from 'vue'
import { type SourceRow } from '../Sources/models'
import {
  MetadataDiscoveredField,
  MetadataExtractedField,
  MetadataFieldDefinition,
  MetadataOrigin,
  MetadataOriginLabels,
  MetadataValueType,
  ValueTypeOptions,
} from './models'

// Source type visuals (image or icon)
const sourceTypeVisuals: Record<string, { image?: string; icon?: string }> = {
  upload: { icon: 'upload' },
  sharepoint: { image: sharepointImage },
  fluid_topics: { image: fluidTopicsImage },
  confluence: { image: confluenceImage },
}

const getSourceVisual = (type: string) => {
  return sourceTypeVisuals[type] || { icon: 'file-text' }
}

const props = defineProps<{
  definedFields: MetadataFieldDefinition[]
  discoveredFields: MetadataDiscoveredField[]
  extractedFields: MetadataExtractedField[]
  discardedFieldNames: string[]
  sources: SourceRow[]
  loading: boolean
  canRunExtraction?: boolean
  runningExtraction?: boolean
  search?: string
}>()

const emit = defineEmits<{
  (e: 'add-field'): void
  (e: 'edit-field', field: MetadataFieldDefinition): void
  (e: 'delete-field', field: MetadataFieldDefinition): void
  (e: 'promote-field', row: MetadataDiscoveredField): void
  (e: 'discard-field', name: string): void
  (e: 'restore-field', name: string): void
  (e: 'run-extraction'): void
  (e: 'open-extraction-settings'): void
  (e: 'add-extraction-field'): void
  (e: 'edit-extraction-field', field: MetadataExtractedField): void
  (e: 'delete-extraction-field', field: MetadataExtractedField): void
  (e: 'quick-create-field', row: MetadataDiscoveredField): void
  (e: 'quick-replace-field', payload: { discovered: MetadataDiscoveredField; target: MetadataFieldDefinition }): void
  (e: 'quick-create-from-extraction', field: MetadataExtractedField): void
  (e: 'quick-replace-from-extraction', payload: { extracted: MetadataExtractedField; target: MetadataFieldDefinition }): void
}>()

const search = computed(() => props.search ?? '')
const discardedExpanded = ref(false)

// Drag-and-drop state
const draggedField = ref<MetadataDiscoveredField | null>(null)
const draggedExtractionField = ref<MetadataExtractedField | null>(null)
const isDragOverSchema = ref(false)
const isDragOverDiscard = ref(false)
const dragOverSchemaFieldId = ref<string | null>(null)
const isDragging = ref(false)
const schemaLaneDragDepth = ref(0)
const discardLaneDragDepth = ref(0)
const schemaFieldDragDepth = new Map<string, number>()

// Drag event handlers
const onDragStart = (event: DragEvent, row: MetadataDiscoveredField) => {
  if (row.is_defined) {
    event.preventDefault()
    return
  }
  // Reset transient drag state
  schemaLaneDragDepth.value = 0
  discardLaneDragDepth.value = 0
  schemaFieldDragDepth.clear()
  isDragOverSchema.value = false
  isDragOverDiscard.value = false
  dragOverSchemaFieldId.value = null

  draggedField.value = row
  isDragging.value = true

  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', row.id)

    // Create a custom drag image for smoother feel
    const dragEl = event.target as HTMLElement
    if (dragEl) {
      // Use a slight offset to position the ghost under cursor nicely
      event.dataTransfer.setDragImage(dragEl, dragEl.offsetWidth / 2, 20)
    }
  }
}

const onDragEnd = () => {
  draggedField.value = null
  draggedExtractionField.value = null
  isDragging.value = false
  isDragOverSchema.value = false
  isDragOverDiscard.value = false
  dragOverSchemaFieldId.value = null
  schemaLaneDragDepth.value = 0
  discardLaneDragDepth.value = 0
  schemaFieldDragDepth.clear()
}

// Extraction field drag handlers
const onExtractionDragStart = (event: DragEvent, row: MetadataExtractedField) => {
  // Reset transient drag state
  schemaLaneDragDepth.value = 0
  discardLaneDragDepth.value = 0
  schemaFieldDragDepth.clear()
  isDragOverSchema.value = false
  isDragOverDiscard.value = false
  dragOverSchemaFieldId.value = null

  draggedExtractionField.value = row
  isDragging.value = true

  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', row.id)

    // Create a custom drag image for smoother feel
    const dragEl = event.target as HTMLElement
    if (dragEl) {
      event.dataTransfer.setDragImage(dragEl, dragEl.offsetWidth / 2, 20)
    }
  }
}

// Helper to check if any field is being dragged
const isAnyFieldDragging = () => draggedField.value || draggedExtractionField.value

// Schema lane drop handlers
const onSchemaDragEnter = () => {
  if (!isAnyFieldDragging()) return
  schemaLaneDragDepth.value += 1
  if (!isDragOverSchema.value) {
    isDragOverSchema.value = true
  }
}

const onSchemaDragOver = (event: DragEvent) => {
  if (!isAnyFieldDragging()) return
  event.dataTransfer!.dropEffect = 'move'
}

const onSchemaDragLeave = () => {
  if (!isAnyFieldDragging()) return
  schemaLaneDragDepth.value = Math.max(0, schemaLaneDragDepth.value - 1)
  if (schemaLaneDragDepth.value === 0) {
    isDragOverSchema.value = false
    dragOverSchemaFieldId.value = null
  }
}

const onSchemaDrop = (event: DragEvent) => {
  // Only create new field if not dropped on an existing field
  if (!dragOverSchemaFieldId.value) {
    if (draggedField.value) {
      emit('quick-create-field', draggedField.value)
    } else if (draggedExtractionField.value) {
      emit('quick-create-from-extraction', draggedExtractionField.value)
    }
  }
  onDragEnd()
}

// Schema field drop handlers (for replacing existing field)
const onSchemaFieldDragEnter = (event: DragEvent, row: MetadataFieldDefinition) => {
  if (!isAnyFieldDragging()) return
  const id = row.id
  schemaFieldDragDepth.set(id, (schemaFieldDragDepth.get(id) || 0) + 1)
  if (dragOverSchemaFieldId.value !== id) {
    dragOverSchemaFieldId.value = id
  }
}

const onSchemaFieldDragOver = (event: DragEvent) => {
  if (!isAnyFieldDragging()) return
  event.dataTransfer!.dropEffect = 'move'
}

const onSchemaFieldDragLeave = (event: DragEvent, row: MetadataFieldDefinition) => {
  if (!isAnyFieldDragging()) return
  const id = row.id
  const next = (schemaFieldDragDepth.get(id) || 0) - 1
  if (next <= 0) {
    schemaFieldDragDepth.delete(id)
    if (dragOverSchemaFieldId.value === id) {
      dragOverSchemaFieldId.value = null
    }
  } else {
    schemaFieldDragDepth.set(id, next)
  }
}

const onSchemaFieldDrop = (event: DragEvent, row: MetadataFieldDefinition) => {
  if (draggedField.value) {
    emit('quick-replace-field', { discovered: draggedField.value, target: row })
  } else if (draggedExtractionField.value) {
    emit('quick-replace-from-extraction', { extracted: draggedExtractionField.value, target: row })
  }
  onDragEnd()
}

// Discard lane drop handlers
const onDiscardDragEnter = () => {
  if (!isAnyFieldDragging()) return
  discardLaneDragDepth.value += 1
  if (!isDragOverDiscard.value) {
    isDragOverDiscard.value = true
  }
}

const onDiscardDragOver = (event: DragEvent) => {
  if (!isAnyFieldDragging()) return
  event.dataTransfer!.dropEffect = 'move'
}

const onDiscardDragLeave = () => {
  if (!isAnyFieldDragging()) return
  discardLaneDragDepth.value = Math.max(0, discardLaneDragDepth.value - 1)
  if (discardLaneDragDepth.value === 0) {
    isDragOverDiscard.value = false
  }
}

const onDiscardDrop = () => {
  if (draggedField.value) {
    emit('discard-field', draggedField.value.name)
  } else if (draggedExtractionField.value) {
    emit('delete-extraction-field', draggedExtractionField.value)
  }
  onDragEnd()
}

// Maps for quick lookups
const defsByName = computed(() => new Map((props.definedFields || []).map((f) => [f.name, f] as const)))
const discardedSet = computed(() => new Set(props.discardedFieldNames || []))

type SearchableRow = MetadataDiscoveredField | MetadataFieldDefinition | MetadataExtractedField

// Helper: apply search filter
const matchesSearch = (row: SearchableRow) => {
  if (!search.value) return true
  const s = search.value.toLowerCase()
  const name = row.name.toLowerCase()
  const displayName = ('display_name' in row && row.display_name ? row.display_name : '').toLowerCase()
  const description = ('description' in row ? row.description || '' : '').toLowerCase()
  const samples = 'sample_values' in row ? row.sample_values || [] : []
  return name.includes(s) || displayName.includes(s) || description.includes(s) || samples.some((v) => v.toLowerCase().includes(s))
}

// Lane 1: Discovered (origin !== 'llm', not discarded)
const discoveredRows = computed(() => {
  let rows = (props.discoveredFields || []).filter((r) => r.origin !== 'llm' && !discardedSet.value.has(r.name))
  rows = rows.filter((r) => !r.is_defined)
  return rows.filter(matchesSearch)
})

// Lane 2: Smart Extraction (configured extraction fields)
const extractedRows = computed(() => {
  let rows = props.extractedFields || []
  return rows.filter(matchesSearch)
})

// Lane 3: Schema (defined fields)
const schemaRows = computed(() => {
  let rows = props.definedFields || []
  return rows.filter(matchesSearch)
})

// Lane 4: Discarded (any discovered field in discarded list)
const discardedRows = computed(() => {
  const rows = (props.discoveredFields || []).filter((r) => discardedSet.value.has(r.name))
  return rows.filter(matchesSearch)
})

// Helper functions
const getTypeLabel = (type: MetadataValueType) => ValueTypeOptions.find((t) => t.value === type)?.label || type
const getOriginLabel = (origin: MetadataOrigin) => MetadataOriginLabels[origin]

/**
 * Compute the resolved type for a schema field based on all fields referenced in its resolution chains.
 * Returns the type label if all referenced fields have the same type, or "Mixed" if types differ.
 */
const getSchemaFieldType = (field: MetadataFieldDefinition): string | null => {
  const resolutions = field.source_value_resolution || []
  if (resolutions.length === 0) return null

  const types = new Set<MetadataValueType>()

  for (const resolution of resolutions) {
    for (const step of resolution.chain || []) {
      if (step.kind === 'constant') continue // Constants don't have a type

      const fieldName = step.field_name
      if (!fieldName) continue

      if (step.kind === 'llm') {
        // Look in extracted fields
        const extracted = props.extractedFields?.find((f) => f.name === fieldName)
        if (extracted?.value_type) {
          types.add(extracted.value_type)
        }
      } else {
        // Look in discovered fields (file or source origin)
        const discovered = props.discoveredFields?.find(
          (f) => f.name === fieldName && (step.kind === 'file' ? f.origin === 'file' : f.origin === 'source')
        )
        if (discovered?.value_type) {
          types.add(discovered.value_type)
        }
      }
    }
  }

  if (types.size === 0) return null
  if (types.size === 1) return getTypeLabel([...types][0])
  return m.knowledgeGraph_mixed()
}

const truncateValue = (value: string, maxLength = 30) => {
  return value.length > maxLength ? value.substring(0, maxLength) + '…' : value
}

/**
 * Compute source resolution status for a schema field.
 * Returns info about which sources have resolution configured vs which don't.
 */
interface SourceResolutionStatus {
  configured: { id: string; name: string; type: string }[]
  missing: { id: string; name: string; type: string }[]
  hasWildcard: boolean
  total: number
}

const getSourceResolutionStatus = (field: MetadataFieldDefinition): SourceResolutionStatus => {
  const sources = props.sources || []
  const resolutions = field.source_value_resolution || []

  // Check for wildcard (*) resolution
  const hasWildcard = resolutions.some((r) => r.source_id === '*' && r.chain?.length > 0)

  // Get set of source IDs that have explicit resolution
  const configuredSourceIds = new Set(resolutions.filter((r) => r.source_id !== '*' && r.chain?.length > 0).map((r) => r.source_id))

  const configured: { id: string; name: string; type: string }[] = []
  const missing: { id: string; name: string; type: string }[] = []

  for (const src of sources) {
    const srcInfo = { id: src.id, name: src.name, type: src.type }
    if (configuredSourceIds.has(src.id) || hasWildcard) {
      configured.push(srcInfo)
    } else {
      missing.push(srcInfo)
    }
  }

  return {
    configured,
    missing,
    hasWildcard,
    total: sources.length,
  }
}

const editDefinedField = (row: MetadataDiscoveredField) => {
  const def = defsByName.value.get(row.name)
  if (def) emit('edit-field', def)
}

</script>

<style scoped>
.metadata-board {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Board lanes container */
.board-lanes {
  display: grid;
  grid-template-columns: repeat(3, 1fr) auto;
  gap: 16px;
  min-block-size: 400px;
}

@media (max-width: 1400px) {
  .board-lanes {
    grid-template-columns: repeat(2, 1fr) auto;
  }
}

@media (max-width: 900px) {
  .board-lanes {
    grid-template-columns: 1fr;
  }
}

/* Lane styling */
.board-lane {
  display: flex;
  flex-direction: column;
  background: var(--ds-color-background);
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-lg);
  overflow: hidden;
  min-block-size: 300px;
  max-block-size: 500px;
}

.board-lane--ai {
  background: #faf5ff;
  border-color: #e9d5ff;
}

.board-lane--schema {
  background: #eff6ff;
  border-color: #bfdbfe;
}

.board-lane--discarded {
  background: var(--ds-color-light);
  border-color: var(--ds-color-border-2);
  transition:
    width 0.25s ease,
    min-width 0.25s ease;
  inline-size: 280px;
  min-inline-size: 280px;
}

.board-lane--discarded.board-lane--collapsed {
  inline-size: 56px;
  min-inline-size: 56px;
}

.board-lane--collapsed .lane-header {
  /* Keep icons stable: don't rotate the whole header, only rotate the label */
  padding: 10px 6px;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
}

.board-lane--collapsed .lane-header__title {
  flex-direction: column;
  gap: 10px;
  align-items: center;
}

.board-lane--collapsed .lane-header__title > span:not(.lane-header__count) {
  /* "Discarded" label only */
  order: 3;
  margin-block-start: 10px;
  writing-mode: vertical-rl;
  text-orientation: mixed;
  transform: rotate(180deg);
}

.board-lane--collapsed .lane-header__subtitle {
  display: none;
}

.board-lane--collapsed .collapse-icon {
  transform: rotate(90deg);
}

.lane-header--clickable {
  cursor: pointer;
  transition: background 0.15s ease;
}

.lane-header--clickable:hover {
  background: var(--ds-color-light);
}

.lane-header__subtitle--collapsed {
  font-style: italic;
}

.collapse-icon {
  transition: transform 0.2s ease;
}

/* Transition for lane content expand/collapse */
.lane-expand-enter-active,
.lane-expand-leave-active {
  transition:
    opacity var(--ds-duration-slow) var(--ds-ease-out),
    max-height var(--ds-duration-slow) var(--ds-ease-out);
  overflow: hidden;
}

.lane-expand-enter-from,
.lane-expand-leave-to {
  opacity: 0;
  max-block-size: 0;
}

.lane-expand-enter-to,
.lane-expand-leave-from {
  opacity: 1;
  max-block-size: 600px;
}

/* Lane header */
.lane-header {
  padding: 12px 14px;
  background: var(--ds-color-white);
  border-block-end: 1px solid rgba(0, 0, 0, 0.06);
  position: relative;
}

.lane-header__title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--ds-font-size-body);
  font-weight: 600;
  color: var(--ds-color-black);
  min-inline-size: 0;
  overflow: hidden;
}

.lane-header__title > span:not(.lane-header__count) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.lane-header__count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-inline-size: 20px;
  block-size: 18px;
  padding: 0 6px;
  background: var(--ds-color-border);
  border-radius: var(--ds-radius-lg);
  font-size: var(--ds-font-size-sm);
  font-weight: 600;
  color: var(--ds-color-label);
  flex-shrink: 0;
}

.lane-header__subtitle {
  font-size: var(--ds-font-size-sm);
  color: var(--ds-color-label);
  margin-block-start: 2px;
}

.lane-header__top {
  display: flex;
  align-items: center;
  gap: 8px;
}

.lane-header__action {
  position: absolute;
  inset-block-start: 10px;
  inset-inline-end: 10px;
}

.lane-header__actions {
  display: flex;
  gap: 2px;
  flex-shrink: 0;
  margin-inline-start: auto;
}

/* Lane content (scrollable) */
.lane-content {
  flex: 1;
  overflow-block: auto;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.lane-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  flex: 1;
  color: var(--ds-color-label);
  font-size: var(--ds-font-size-caption);
  text-align: center;
  padding: 24px;
}

.lane-empty__hint {
  font-size: var(--ds-font-size-sm);
  color: var(--ds-color-label);
  max-inline-size: 180px;
  line-height: 1.4;
  margin-block-start: 4px;
}

/* Field card */
.field-card {
  background: var(--ds-color-white);
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-md);
  padding: 10px 12px;
  cursor: default;
  transition:
    box-shadow 0.15s ease,
    border-color 0.15s ease;
}

.field-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border-color: var(--ds-color-border-2);
}

.field-card--defined {
  opacity: 0.6;
  background: var(--ds-color-light);
}

.field-card--schema {
  cursor: pointer;
}

.field-card--schema:hover {
  border-color: var(--ds-color-primary);
}

.field-card--discarded {
  opacity: 0.7;
  background: var(--ds-color-light);
}

.field-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-block-end: 6px;
  position: relative;
}

.field-card__name-row {
  display: flex;
  align-items: center;
  gap: 6px;
  min-inline-size: 0;
  flex: 1;
}

.field-card__name {
  font-size: var(--ds-font-size-label);
  font-weight: 600;
  color: var(--ds-color-black);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.field-card__type-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-block-end: 6px;
}

.field-card__type-delimiter {
  font-size: var(--ds-font-size-xs);
  color: var(--ds-color-label);
  margin: 0 2px;
}

.field-card__type {
  font-size: var(--ds-font-size-xs);
  color: var(--ds-color-label);
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.field-card__meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-block-end: 6px;
  flex-wrap: wrap;
}

.field-card__source {
  font-size: var(--ds-font-size-sm);
  color: var(--ds-color-secondary-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-inline-size: 140px;
}

.field-card__samples {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
  margin-block-start: 4px;
  padding-block-start: 6px;
  border-block-start: 1px solid var(--ds-color-light);
  position: relative;
  min-block-size: 24px;
}

.field-card__constraints {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-block-end: 8px;
}

.field-card__actions {
  display: flex;
  align-items: center;
  gap: 4px;
  justify-content: flex-end;
  flex-shrink: 0;
}

.field-card__actions--samples {
  margin-inline-start: auto;
}

/* Sample chips */
.sample-chip {
  display: inline-block;
  padding: 2px 6px;
  background: var(--ds-color-light);
  border-radius: var(--ds-radius-sm);
  font-size: var(--ds-font-size-xs);
  color: var(--ds-color-secondary-text);
  max-inline-size: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sample-more {
  font-size: var(--ds-font-size-xs);
  color: var(--ds-color-label);
}

/* Constraint chips */
.constraint-chip {
  display: inline-block;
  padding: 2px 6px;
  background: var(--ds-color-info-soft);
  border-radius: var(--ds-radius-sm);
  font-size: var(--ds-font-size-xs);
  color: var(--ds-color-info-on-soft);
}

/* Origin chips */
.origin-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 6px;
  border-radius: var(--ds-radius-sm);
  font-size: var(--ds-font-size-xs);
  font-weight: 500;
}

.origin-chip--llm {
  background: #f3e8ff;
  color: #7c3aed;
}

.origin-chip--file {
  background: #ccfbf1;
  color: #0d9488;
}

.origin-chip--source {
  background: #e0e7ff;
  color: #4338ca;
}

.origin-chip--muted {
  background: var(--ds-color-border);
  color: var(--ds-color-secondary-text);
}

.origin-chip--type-style {
  font-size: var(--ds-font-size-xs);
  color: var(--ds-color-label);
  text-transform: uppercase;
  letter-spacing: 0.3px;
  background: transparent !important;
  padding: 0;
  border-radius: 0;
  font-weight: normal;
}

/* Source badge for discovered fields */
.source-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: var(--ds-radius-sm);
  flex-shrink: 0;
  max-inline-size: 140px;
  border: 1px solid var(--ds-color-border-2);
}

.source-badge--top-right {
  position: absolute;
  inset-block-start: 0;
  inset-inline-end: 0;
}

.source-badge__name {
  font-size: var(--ds-font-size-sm);
  font-weight: 500;
  color: var(--ds-color-black);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Action buttons for discovered/extracted fields */
.action-btn {
  padding: 2px 10px;
  min-block-size: 24px;
  border-radius: var(--ds-radius-sm);
}

/* Drag and drop styles */
.field-card--dragging {
  opacity: 0.35;
  transform: scale(0.97);
  box-shadow: none;
  border-color: var(--ds-color-border-2) !important;
  background: var(--ds-color-light);
}

.field-card[draggable='true'] {
  cursor: grab;
}

.field-card[draggable='true']:hover {
  transform: translateY(-1px);
}

.field-card[draggable='true']:active {
  cursor: grabbing;
}

/* Schema lane drop zone - instant on enter, smooth on leave */
.board-lane--schema .lane-content {
  border: 2px solid transparent;
}

.lane-content--drag-over {
  background: rgba(59, 130, 246, 0.06);
  border: 2px dashed #3b82f6;
  border-radius: var(--ds-radius-md);
}

/* Schema field drop target - instant feedback */
.field-card--drop-target {
  border-color: var(--ds-color-primary) !important;
  box-shadow:
    0 0 0 3px rgba(59, 130, 246, 0.25),
    0 4px 12px rgba(59, 130, 246, 0.15);
  background: var(--ds-color-primary-bg);
}

/* Discard lane drop zone - instant feedback */
.board-lane--discarded.board-lane--drag-over {
  background: var(--ds-color-error-bg);
  border-color: var(--ds-color-error);
  box-shadow:
    inset 0 0 0 2px rgba(239, 68, 68, 0.15),
    0 0 20px rgba(239, 68, 68, 0.1);
}

.board-lane--discarded.board-lane--drag-over .lane-header {
  background: rgba(239, 68, 68, 0.04);
}

/* Empty lane drop hint */
.lane-empty--drop-target {
  pointer-events: none;
}

/* Drag active state - instant visual hints */
.metadata-board--dragging .field-card:not(.field-card--dragging) {
  opacity: 0.75;
}

.metadata-board--dragging .board-lane--schema,
.metadata-board--dragging .board-lane--discarded {
  position: relative;
}

.metadata-board--dragging .board-lane--schema::after,
.metadata-board--dragging .board-lane--discarded:not(.board-lane--collapsed)::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: var(--ds-radius-lg);
  pointer-events: none;
}

.metadata-board--dragging .board-lane--schema::after {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.02) 0%, rgba(59, 130, 246, 0.06) 100%);
  border: 1px dashed rgba(59, 130, 246, 0.25);
}

.metadata-board--dragging .board-lane--discarded:not(.board-lane--collapsed)::after {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.02) 0%, rgba(239, 68, 68, 0.04) 100%);
  border: 1px dashed rgba(239, 68, 68, 0.2);
}

/* Lane header icon buttons - clean minimal style */
.lane-icon-btn {
  inline-size: 36px !important;
  block-size: 36px !important;
  min-inline-size: 36px !important;
  min-block-size: 36px !important;
}

/* AI lane buttons - Purple theme */
.lane-icon-btn--ai {
  color: #9333ea !important;
}

.lane-icon-btn--ai:hover {
  background: rgba(147, 51, 234, 0.1) !important;
  color: #7c3aed !important;
}

/* Run button - Green accent */
.lane-icon-btn--run {
  color: var(--ds-color-success) !important;
}

.lane-icon-btn--run:hover {
  background: rgba(16, 185, 129, 0.1) !important;
  color: var(--ds-color-success) !important;
}

/* Schema lane button - Blue theme */
.lane-icon-btn--schema {
  color: var(--ds-color-primary) !important;
}

.lane-icon-btn--schema:hover {
  background: var(--ds-color-primary-bg) !important;
  color: var(--ds-color-primary) !important;
}

/* Source resolution status indicator */
.field-card__sources {
  margin-block-start: 6px;
  padding-block-start: 6px;
  border-block-start: 1px solid var(--ds-color-light);
}

.field-card__sources--top-right {
  position: absolute;
  inset-block-start: 0;
  inset-inline-end: 0;
  margin-block-start: 0;
  padding-block-start: 0;
  border-block-start: none;
}

.source-status {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: var(--ds-font-size-caption);
  cursor: help;
}

.source-status--resolved {
  color: var(--ds-color-success);
}

.source-status--unresolved {
  color: var(--ds-color-error);
}
</style>

<!-- Unscoped styles for tooltip (teleported to body) -->
<style>
.source-tooltip {
  background: var(--ds-color-white) !important;
  padding: 0 !important;
  border-radius: var(--ds-radius-lg) !important;
  border: 1px solid var(--ds-color-border) !important;
  box-shadow:
    0 4px 16px rgba(0, 0, 0, 0.1),
    0 1px 4px rgba(0, 0, 0, 0.06) !important;
  color: var(--ds-color-black) !important;
  max-inline-size: 240px !important;
}

.source-tooltip .source-tooltip__content {
  padding: 8px 0;
}

.source-tooltip .source-tooltip__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 0 12px 6px;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  color: var(--ds-color-secondary-text);
  border-block-end: 1px solid var(--ds-color-border);
  margin-block-end: 4px;
}

.source-tooltip .source-tooltip__meta {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.2px;
  color: var(--ds-color-black);
}

.source-tooltip .source-tooltip__wildcard {
  padding: 6px 12px;
  font-size: 11px;
  color: var(--ds-color-success-text);
}

.source-tooltip .source-tooltip__list {
  display: flex;
  flex-direction: column;
  max-block-size: 220px;
  overflow: auto;
}

.source-tooltip .source-tooltip__row {
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: center;
  column-gap: 12px;
  padding: 6px 12px;
  font-size: 12px;
  color: var(--ds-color-black);
}

.source-tooltip .source-tooltip__row:hover {
  background: var(--ds-color-light);
}

.source-tooltip .source-tooltip__row--missing {
  color: var(--ds-color-label);
}

.source-tooltip .source-tooltip__name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.source-tooltip .source-tooltip__status {
  color: var(--ds-color-success);
}

.source-tooltip .source-tooltip__row--missing .source-tooltip__status {
  color: var(--ds-color-border-2);
}
</style>
