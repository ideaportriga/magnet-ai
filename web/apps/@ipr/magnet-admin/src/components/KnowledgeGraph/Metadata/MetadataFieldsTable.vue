<template>
  <div class="metadata-board" :class="{ 'metadata-board--dragging': isDragging }">
    <!-- Global Toolbar -->
    <div class="board-toolbar">
      <km-input v-model="search" placeholder="Search all fields..." icon-before="search" clearable style="width: 280px" />
    </div>

    <q-linear-progress v-if="loading" indeterminate color="primary" class="q-mb-sm" />

    <!-- 4-Lane Board -->
    <div v-else class="board-lanes">
      <!-- Lane 1: Discovered -->
      <div class="board-lane">
        <div class="lane-header">
          <div class="lane-header__title">
            <q-icon name="explore" size="18px" color="teal-7" />
            <span>Discovered</span>
            <span class="lane-header__count">{{ discoveredRows.length }}</span>
          </div>
          <div class="lane-header__subtitle">Auto-detected from documents</div>
        </div>
        <div class="lane-content">
          <div v-if="discoveredRows.length === 0" class="lane-empty">
            <q-icon name="check_circle" size="32px" color="grey-4" />
            <span>{{ search ? 'No matches' : 'No new fields' }}</span>
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
                  <q-btn flat dense size="sm" color="grey-7" icon="o_edit" @click.stop="editDefinedField(row)">
                    <q-tooltip>Edit Schema</q-tooltip>
                  </q-btn>
                </template>
                <template v-else>
                  <q-btn flat dense size="sm" color="teal-7" icon="o_add_circle" @click.stop="emit('promote-field', row)">
                    <q-tooltip>Add to schema</q-tooltip>
                  </q-btn>
                  <q-btn flat dense size="sm" color="negative" icon="o_block" @click.stop="emit('discard-field', row.name)">
                    <q-tooltip>Ignore this field</q-tooltip>
                  </q-btn>
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Lane 2: Smart Extraction -->
      <div class="board-lane board-lane--ai">
        <div class="lane-header">
          <div class="lane-header__title">
            <q-icon name="auto_awesome" size="18px" color="purple-7" />
            <span>Smart Extraction</span>
            <span class="lane-header__count">{{ extractedRows.length }}</span>
          </div>
          <div class="lane-header__subtitle">Configure which fields AI should extract</div>
          <div class="lane-header__actions">
            <q-btn round flat dense class="lane-icon-btn lane-icon-btn--ai" icon="o_add_circle" @click.stop="emit('add-extraction-field')">
              <q-tooltip>Add Field</q-tooltip>
            </q-btn>
            <q-btn round flat dense class="lane-icon-btn lane-icon-btn--ai" icon="settings" @click.stop="emit('open-extraction-settings')">
              <q-tooltip>Settings</q-tooltip>
            </q-btn>
            <q-btn
              v-if="canRunExtraction"
              round
              flat
              dense
              class="lane-icon-btn lane-icon-btn--run"
              icon="play_arrow"
              :loading="runningExtraction"
              :disable="runningExtraction"
              @click.stop="emit('run-extraction')"
            >
              <q-tooltip>Run Extraction</q-tooltip>
            </q-btn>
          </div>
        </div>
        <div class="lane-content">
          <div v-if="extractedRows.length === 0" class="lane-empty">
            <q-icon name="smart_toy" size="32px" color="grey-4" />
            <span>{{ search ? 'No matches' : 'No extraction fields yet' }}</span>
            <span v-if="!search" class="lane-empty__hint">Add fields to define what AI should extract</span>
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
                <q-btn flat dense size="sm" color="grey-7" icon="o_edit" @click.stop="emit('edit-extraction-field', row)">
                  <q-tooltip>Edit</q-tooltip>
                </q-btn>
                <q-btn flat dense size="sm" color="negative" icon="o_delete" @click.stop="emit('delete-extraction-field', row)">
                  <q-tooltip>Delete</q-tooltip>
                </q-btn>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Lane 3: Schema -->
      <div class="board-lane board-lane--schema">
        <div class="lane-header">
          <div class="lane-header__title">
            <q-icon name="tune" size="18px" color="blue-7" />
            <span>Schema</span>
            <span class="lane-header__count">{{ schemaRows.length }}</span>
          </div>
          <div class="lane-header__subtitle">Defined metadata fields</div>
          <div class="lane-header__actions">
            <q-btn round flat dense class="lane-icon-btn lane-icon-btn--schema" icon="o_add_circle" @click.stop="emit('add-field')">
              <q-tooltip>Add Field</q-tooltip>
            </q-btn>
          </div>
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
            <q-icon name="category" size="32px" color="grey-4" />
            <span>{{ isDragOverSchema ? 'Drop to create field' : search ? 'No matches' : 'No schema fields' }}</span>
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
                    <q-icon name="check_circle" size="14px" />
                  </div>
                </template>
                <template v-else>
                  <div class="source-status source-status--unresolved">
                    <q-icon name="error_outline" size="14px" />
                    <span>{{ getSourceResolutionStatus(row).configured.length }}/{{ sources.length }} sources</span>
                  </div>
                </template>
                <q-tooltip class="source-tooltip" :offset="[0, 6]">
                  <div class="source-tooltip__content">
                    <div class="source-tooltip__header">
                      <span>Source resolution</span>
                      <span class="source-tooltip__meta">{{ getSourceResolutionStatus(row).configured.length }}/{{ sources.length }}</span>
                    </div>
                    <div v-if="getSourceResolutionStatus(row).hasWildcard" class="source-tooltip__wildcard">Applies to all sources (wildcard *)</div>
                    <div v-else class="source-tooltip__list">
                      <div
                        v-for="src in sources"
                        :key="src.id"
                        class="source-tooltip__row"
                        :class="{ 'source-tooltip__row--missing': getSourceResolutionStatus(row).missing.some((m) => m.id === src.id) }"
                      >
                        <span class="source-tooltip__name">{{ src.name }}</span>
                        <q-icon
                          :name="getSourceResolutionStatus(row).configured.some((c) => c.id === src.id) ? 'check' : 'remove'"
                          size="12px"
                          class="source-tooltip__status"
                        />
                      </div>
                    </div>
                  </div>
                </q-tooltip>
              </div>
            </div>
            <div v-if="getSchemaFieldType(row)" class="field-card__type">{{ getSchemaFieldType(row) }}</div>
            <div class="field-card__samples">
              <div class="field-card__actions field-card__actions--samples">
                <q-btn flat dense size="sm" color="grey-7" icon="o_edit" @click.stop="emit('edit-field', row)">
                  <q-tooltip>Edit</q-tooltip>
                </q-btn>
                <q-btn flat dense size="sm" color="negative" icon="o_delete" @click.stop="emit('delete-field', row)">
                  <q-tooltip>Delete</q-tooltip>
                </q-btn>
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
            <q-icon :name="discardedExpanded ? 'expand_less' : 'expand_more'" size="18px" color="grey-5" class="collapse-icon" />
            <q-icon v-if="discardedExpanded" name="block" size="18px" color="grey-6" />
            <span>Discarded</span>
            <span v-if="discardedExpanded" class="lane-header__count">{{ discardedRows.length }}</span>
          </div>
          <div v-if="discardedExpanded" class="lane-header__subtitle">Hidden from review</div>
          <div v-else class="lane-header__subtitle lane-header__subtitle--collapsed">Click to expand</div>
        </div>
        <transition name="lane-expand">
          <div v-if="discardedExpanded" class="lane-content">
            <div v-if="discardedRows.length === 0" class="lane-empty">
              <q-icon name="check" size="32px" color="grey-4" />
              <span>{{ search ? 'No matches' : 'Nothing discarded' }}</span>
            </div>
            <div v-for="row in discardedRows" :key="row.id" class="field-card field-card--discarded">
              <div class="field-card__header">
                <span class="field-card__name">{{ row.name }}</span>
                <div class="field-card__actions">
                  <q-btn flat dense size="sm" color="primary" label="Restore" @click.stop="emit('restore-field', row.name)" />
                  <q-btn flat dense size="sm" color="grey-7" label="Define" @click.stop="emit('promote-field', row)" />
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
  return sourceTypeVisuals[type] || { icon: 'description' }
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

const search = ref('')
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
  return 'Mixed'
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

// Reset search when data changes significantly
watch([() => props.definedFields?.length, () => props.discoveredFields?.length], () => {
  // keep search
})
</script>

<style scoped>
.metadata-board {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.board-toolbar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 0;
}

/* Board lanes container */
.board-lanes {
  display: grid;
  grid-template-columns: repeat(3, 1fr) auto;
  gap: 16px;
  min-height: 400px;
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
  background: #fafafa;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
  min-height: 300px;
  max-height: 500px;
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
  background: #f3f4f6;
  border-color: #d1d5db;
  transition:
    width 0.25s ease,
    min-width 0.25s ease;
  width: 280px;
  min-width: 280px;
}

.board-lane--discarded.board-lane--collapsed {
  width: 56px;
  min-width: 56px;
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
  margin-top: 10px;
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
  background: #f9fafb;
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
  transition: all 0.25s ease;
  overflow: hidden;
}

.lane-expand-enter-from,
.lane-expand-leave-to {
  opacity: 0;
  max-height: 0;
}

.lane-expand-enter-to,
.lane-expand-leave-from {
  opacity: 1;
  max-height: 600px;
}

/* Lane header */
.lane-header {
  padding: 12px 14px;
  background: white;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  position: relative;
}

.lane-header__title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.lane-header__count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 18px;
  padding: 0 6px;
  background: #e5e7eb;
  border-radius: 9px;
  font-size: 11px;
  font-weight: 600;
  color: #6b7280;
}

.lane-header__subtitle {
  font-size: 11px;
  color: #9ca3af;
  margin-top: 2px;
}

.lane-header__action {
  position: absolute;
  top: 10px;
  right: 10px;
}

.lane-header__actions {
  position: absolute;
  top: 6px;
  right: 6px;
  display: flex;
  gap: 2px;
}

/* Lane content (scrollable) */
.lane-content {
  flex: 1;
  overflow-y: auto;
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
  color: #9ca3af;
  font-size: 12px;
  text-align: center;
  padding: 24px;
}

.lane-empty__hint {
  font-size: 11px;
  color: #b5b5b5;
  max-width: 180px;
  line-height: 1.4;
  margin-top: 4px;
}

/* Field card */
.field-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 10px 12px;
  cursor: default;
  transition:
    box-shadow 0.15s ease,
    border-color 0.15s ease;
}

.field-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border-color: #d1d5db;
}

.field-card--defined {
  opacity: 0.6;
  background: #f9fafb;
}

.field-card--schema {
  cursor: pointer;
}

.field-card--schema:hover {
  border-color: var(--q-primary);
}

.field-card--discarded {
  opacity: 0.7;
  background: #f9fafb;
}

.field-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 6px;
  position: relative;
}

.field-card__name-row {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  flex: 1;
}

.field-card__name {
  font-size: 13px;
  font-weight: 600;
  color: #1f2937;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.field-card__type-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}

.field-card__type-delimiter {
  font-size: 10px;
  color: #9ca3af;
  margin: 0 2px;
}

.field-card__type {
  font-size: 10px;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.field-card__meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
  flex-wrap: wrap;
}

.field-card__source {
  font-size: 11px;
  color: #6b7280;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 140px;
}

.field-card__samples {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
  margin-top: 4px;
  padding-top: 6px;
  border-top: 1px solid #f3f4f6;
  position: relative;
  min-height: 24px;
}

.field-card__constraints {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}

.field-card__actions {
  display: flex;
  align-items: center;
  gap: 4px;
  justify-content: flex-end;
  flex-shrink: 0;
}

.field-card__actions--samples {
  margin-left: auto;
}

/* Sample chips */
.sample-chip {
  display: inline-block;
  padding: 2px 6px;
  background: #f3f4f6;
  border-radius: 4px;
  font-size: 10px;
  color: #4b5563;
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sample-more {
  font-size: 10px;
  color: #9ca3af;
}

/* Constraint chips */
.constraint-chip {
  display: inline-block;
  padding: 2px 6px;
  background: #dbeafe;
  border-radius: 4px;
  font-size: 10px;
  color: #1e40af;
}

/* Origin chips */
.origin-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
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
  background: #e5e7eb;
  color: #6b7280;
}

.origin-chip--type-style {
  font-size: 10px;
  color: #9ca3af;
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
  border-radius: 4px;
  flex-shrink: 0;
  max-width: 140px;
  border: 1px solid #d1d5db;
}

.source-badge--top-right {
  position: absolute;
  top: 0;
  right: 0;
}

.source-badge__name {
  font-size: 11px;
  font-weight: 500;
  color: #374151;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Action buttons for discovered/extracted fields */
.action-btn {
  padding: 2px 10px;
  min-height: 24px;
  border-radius: 4px;
}

.action-btn:deep(.q-btn__content) {
  text-transform: none;
}

/* Drag and drop styles */
.field-card--dragging {
  opacity: 0.35;
  transform: scale(0.97);
  box-shadow: none;
  border-color: #cbd5e1 !important;
  background: #f8fafc;
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
  border-radius: 6px;
}

/* Schema field drop target - instant feedback */
.field-card--drop-target {
  border-color: #3b82f6 !important;
  box-shadow:
    0 0 0 3px rgba(59, 130, 246, 0.25),
    0 4px 12px rgba(59, 130, 246, 0.15);
  background: #eff6ff;
}

/* Discard lane drop zone - instant feedback */
.board-lane--discarded.board-lane--drag-over {
  background: rgba(239, 68, 68, 0.06);
  border-color: #ef4444;
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
  border-radius: 8px;
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
  width: 36px !important;
  height: 36px !important;
  min-width: 36px !important;
  min-height: 36px !important;
}

.lane-icon-btn :deep(.q-icon) {
  font-size: 24px !important;
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
  color: #10b981 !important;
}

.lane-icon-btn--run:hover {
  background: rgba(16, 185, 129, 0.1) !important;
  color: #059669 !important;
}

/* Schema lane button - Blue theme */
.lane-icon-btn--schema {
  color: #3b82f6 !important;
}

.lane-icon-btn--schema:hover {
  background: rgba(59, 130, 246, 0.1) !important;
  color: #2563eb !important;
}

/* Source resolution status indicator */
.field-card__sources {
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px solid #f0f1f3;
}

.field-card__sources--top-right {
  position: absolute;
  top: 0;
  right: 0;
  margin-top: 0;
  padding-top: 0;
  border-top: none;
}

.source-status {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 12px;
  cursor: help;
}

.source-status--resolved {
  color: #059669;
}

.source-status--unresolved {
  color: #dc2626;
}
</style>

<!-- Unscoped styles for tooltip (teleported to body) -->
<style>
.source-tooltip.q-tooltip {
  background: #ffffff !important;
  padding: 0 !important;
  border-radius: 8px !important;
  border: 1px solid #e5e7eb !important;
  box-shadow:
    0 4px 16px rgba(0, 0, 0, 0.1),
    0 1px 4px rgba(0, 0, 0, 0.06) !important;
  color: #374151 !important;
  max-width: 240px !important;
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
  color: #6b7280;
  border-bottom: 1px solid #e5e7eb;
  margin-bottom: 4px;
}

.source-tooltip .source-tooltip__meta {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.2px;
  color: #374151;
}

.source-tooltip .source-tooltip__wildcard {
  padding: 6px 12px;
  font-size: 11px;
  color: #047857;
}

.source-tooltip .source-tooltip__list {
  display: flex;
  flex-direction: column;
  max-height: 220px;
  overflow: auto;
}

.source-tooltip .source-tooltip__row {
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: center;
  column-gap: 12px;
  padding: 6px 12px;
  font-size: 12px;
  color: #1f2937;
}

.source-tooltip .source-tooltip__row:hover {
  background: #f3f4f6;
}

.source-tooltip .source-tooltip__row--missing {
  color: #9ca3af;
}

.source-tooltip .source-tooltip__name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.source-tooltip .source-tooltip__status {
  color: #10b981;
}

.source-tooltip .source-tooltip__row--missing .source-tooltip__status {
  color: #d1d5db;
}
</style>
