<template>
  <div class="entities-panel">
    <div class="panel-header">
      <div class="panel-header-content">
        <span class="panel-title">Extracted Entities</span>
      </div>
      <q-btn flat dense round icon="close" size="sm" class="panel-close-btn" @click="$emit('close')" />
    </div>

    <div v-if="!loading && totalCount > 0" class="panel-toolbar">
      <km-input v-model="search" placeholder="Filter..." icon-before="search" clearable dense />
      <kg-dropdown-field
        v-model="selectedType"
        :options="typeOptions"
        option-value="value"
        option-label="label"
        option-meta="count"
        placeholder="All"
        dense
      />
    </div>

    <div class="panel-body">
      <div v-if="loading" class="panel-loading">
        <q-spinner size="28px" color="primary" />
        <div class="loading-text">Loading entities...</div>
      </div>

      <div v-else-if="totalCount === 0" class="panel-empty">
        <div class="empty-icon-wrapper">
          <q-icon name="hub" size="32px" />
        </div>
        <div class="empty-text">No extracted entities</div>
        <div class="empty-subtext">Run entity extraction to discover entities in this document</div>
      </div>

      <div v-else-if="filteredRecords.length === 0" class="panel-empty">
        <div class="empty-icon-wrapper">
          <q-icon name="search_off" size="32px" />
        </div>
        <div class="empty-text">No matches</div>
        <div class="empty-subtext">No entities match the current filter</div>
      </div>

      <div v-else class="entity-cards">
        <div v-for="record in paginatedRecords" :key="record.id" class="entity-card">
          <div v-if="showCardHeader" class="entity-card-header">
            <span class="entity-card-title">{{ record.entity }}</span>
            <span v-if="chunkMentionCount(record) > 0" class="chunk-mentions">
              <q-icon name="layers" size="12px" />
              {{ chunkMentionCount(record) }}
            </span>
          </div>

          <div v-if="cardPairs(record).length > 0" class="entity-card-attrs">
            <div v-for="pair in cardPairs(record)" :key="pair.key" class="attr-row" :class="{ 'attr-row--identifier': pair.isIdentifier }">
              <span class="attr-key">
                <q-icon v-if="pair.isIdentifier" name="vpn_key" size="11px" class="identifier-icon">
                  <q-tooltip>Identifier field</q-tooltip>
                </q-icon>
                {{ pair.key }}
              </span>
              <span class="attr-value" :title="pair.value">{{ pair.value }}</span>
            </div>
          </div>

          <div v-if="!showCardHeader && chunkMentionCount(record) > 0" class="entity-card-footer">
            <span class="chunk-mentions">
              <q-icon name="layers" size="12px" />
              {{ chunkMentionCount(record) }} {{ chunkMentionCount(record) === 1 ? 'chunk' : 'chunks' }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="!loading && filteredRecords.length > pageSize" class="panel-footer">
      <q-pagination
        v-model="currentPage"
        :max="totalPages"
        :max-pages="5"
        dense
        flat
        boundary-numbers
        direction-links
        color="grey-7"
        active-color="primary"
      />
      <div class="pagination-info">{{ pageStart }}–{{ pageEnd }} of {{ filteredRecords.length }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { KgDropdownField } from '../common'
import { EntityRecord } from './models'

const props = defineProps<{
  entities: EntityRecord[]
  loading?: boolean
}>()

defineEmits<{
  (e: 'close'): void
}>()

const ALL_TYPES = '__all__'
const pageSize = 8
const currentPage = ref(1)
const selectedType = ref<string>(ALL_TYPES)
const search = ref('')

const totalCount = computed(() => props.entities.length)

const typeCounts = computed<Map<string, number>>(() => {
  const counts = new Map<string, number>()
  for (const record of props.entities) {
    const key = record.entity || '(uncategorized)'
    counts.set(key, (counts.get(key) || 0) + 1)
  }
  return counts
})

const typeOptions = computed(() => {
  const opts: Array<{ label: string; value: string; count: string }> = [{ label: 'All', value: ALL_TYPES, count: String(totalCount.value) }]
  const sortedTypes = [...typeCounts.value.entries()].sort((a, b) => a[0].localeCompare(b[0]))
  for (const [name, count] of sortedTypes) {
    opts.push({ label: name, value: name, count: String(count) })
  }
  return opts
})

const showCardHeader = computed(() => selectedType.value === ALL_TYPES)

const normalizedQuery = computed(() => search.value.trim().toLowerCase())

const recordMatchesQuery = (record: EntityRecord, q: string): boolean => {
  if (!q) return true
  if ((record.entity || '').toLowerCase().includes(q)) return true
  if ((record.record_identifier || '').toLowerCase().includes(q)) return true
  const cols = record.column_values || {}
  for (const [k, v] of Object.entries(cols)) {
    if (k.toLowerCase().includes(q)) return true
    if (formatValue(v).toLowerCase().includes(q)) return true
  }
  return false
}

const filteredRecords = computed<EntityRecord[]>(() => {
  const all = [...props.entities]
  const byType = selectedType.value === ALL_TYPES ? all : all.filter((r) => (r.entity || '(uncategorized)') === selectedType.value)
  const q = normalizedQuery.value
  const filtered = q ? byType.filter((r) => recordMatchesQuery(r, q)) : byType
  filtered.sort((a, b) => {
    const t = (a.entity || '').localeCompare(b.entity || '')
    if (t !== 0) return t
    return (a.record_identifier || '').localeCompare(b.record_identifier || '')
  })
  return filtered
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredRecords.value.length / pageSize)))

const paginatedRecords = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return filteredRecords.value.slice(start, start + pageSize)
})

const pageStart = computed(() => (filteredRecords.value.length === 0 ? 0 : (currentPage.value - 1) * pageSize + 1))
const pageEnd = computed(() => Math.min(currentPage.value * pageSize, filteredRecords.value.length))

watch(selectedType, () => {
  currentPage.value = 1
})

watch(search, () => {
  currentPage.value = 1
})

watch(
  () => props.entities,
  () => {
    currentPage.value = 1
    if (selectedType.value !== ALL_TYPES && !typeCounts.value.has(selectedType.value)) {
      selectedType.value = ALL_TYPES
    }
  }
)

function formatValue(val: unknown): string {
  if (val === null || val === undefined) return ''
  if (typeof val === 'string') return val
  if (typeof val === 'number' || typeof val === 'boolean') return String(val)
  try {
    return JSON.stringify(val)
  } catch {
    return String(val)
  }
}

interface CardPair {
  key: string
  value: string
  isIdentifier: boolean
}

const cardPairs = (record: EntityRecord): CardPair[] => {
  const identifier = record.record_identifier || ''
  const cols = record.column_values || {}
  const rawPairs: CardPair[] = []
  let identifierMatched = false

  for (const [k, v] of Object.entries(cols)) {
    if (v === null || v === undefined || v === '') continue
    const formatted = formatValue(v)
    if (!formatted) continue
    const isIdentifier = !identifierMatched && identifier !== '' && String(v) === identifier
    if (isIdentifier) identifierMatched = true
    rawPairs.push({
      key: k,
      value: formatted,
      isIdentifier,
    })
  }

  if (!identifierMatched && identifier) {
    rawPairs.unshift({ key: 'identifier', value: identifier, isIdentifier: true })
  }

  rawPairs.sort((a, b) => Number(b.isIdentifier) - Number(a.isIdentifier))

  return rawPairs.slice(0, 5)
}

const chunkMentionCount = (record: EntityRecord): number => {
  return record.source_chunk_ids?.length || 0
}
</script>

<style scoped>
.entities-panel {
  width: 380px;
  min-width: 380px;
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: none;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: #ffffff;
  border-bottom: 1px solid #f1f5f9;
  color: #1e293b;
}

.panel-header-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.panel-title {
  font-size: 15px;
  font-weight: 600;
  letter-spacing: -0.01em;
}

.panel-subtitle {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
}

.panel-close-btn {
  color: #94a3b8;
}

.panel-close-btn:hover {
  color: #475569;
  background: #f1f5f9;
}

.panel-toolbar {
  padding: 12px 16px;
  background: #ffffff;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  background: #f8fafc;
}

.panel-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  gap: 12px;
}

.loading-text {
  font-size: 13px;
  color: #64748b;
}

.panel-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
}

.empty-icon-wrapper {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 50%;
  margin-bottom: 16px;
  color: #94a3b8;
}

.empty-text {
  font-size: 14px;
  font-weight: 600;
  color: #64748b;
  margin-bottom: 4px;
}

.empty-subtext {
  font-size: 12px;
  color: #94a3b8;
  max-width: 240px;
  line-height: 1.5;
}

.entity-cards {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.entity-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  transition:
    border-color 0.15s ease,
    box-shadow 0.15s ease;
}

.entity-card:hover {
  border-color: #cbd5e1;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.06);
}

.entity-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid #f1f5f9;
}

.entity-card-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--q-primary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.entity-card-attrs {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.attr-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
  font-size: 12px;
  line-height: 1.5;
  min-width: 0;
}

.attr-row--identifier .attr-value {
  font-weight: 600;
  color: #1e293b;
}

.attr-key {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  color: #94a3b8;
  font-weight: 500;
  flex-shrink: 0;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 11px;
}

.identifier-icon {
  color: var(--q-primary);
}

.attr-value {
  color: #334155;
  flex: 1;
  min-width: 0;
  white-space: nowrap;
  overflow-x: auto;
  overflow-y: hidden;
  scrollbar-width: none;
  -ms-overflow-style: none;
  user-select: text;
  -webkit-user-select: text;
  cursor: text;
  mask-image: linear-gradient(to right, #000 calc(100% - 16px), transparent);
  -webkit-mask-image: linear-gradient(to right, #000 calc(100% - 16px), transparent);
}

.attr-value::-webkit-scrollbar {
  display: none;
  width: 0;
  height: 0;
}

.entity-card-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-top: 4px;
  border-top: 1px dashed #f1f5f9;
}

.chunk-mentions {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 11px;
  color: #64748b;
  font-weight: 500;
}

.panel-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: #ffffff;
  border-top: 1px solid #f1f5f9;
  gap: 8px;
}

.panel-footer :deep(.q-pagination__content) {
  gap: 2px;
}

.panel-footer :deep(.q-btn) {
  min-width: 26px;
  min-height: 26px;
  font-size: 11px;
}

.pagination-info {
  font-size: 11px;
  color: #64748b;
  font-weight: 500;
  white-space: nowrap;
}

/* Responsive */
@media (max-width: 1024px) {
  .entities-panel {
    position: absolute;
    top: 16px;
    right: 16px;
    bottom: 16px;
    z-index: 10;
    width: 400px;
    max-width: calc(100% - 32px);
    min-width: 0;
    box-shadow:
      0 10px 25px -5px rgba(0, 0, 0, 0.1),
      0 8px 10px -6px rgba(0, 0, 0, 0.1);
  }
}
</style>
