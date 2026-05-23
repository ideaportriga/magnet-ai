<template>
  <div class="metadata-panel">
    <div class="panel-header">
      <div class="panel-header-content">
        <span class="panel-title">Document Info</span>
      </div>
      <q-btn flat dense round icon="close" size="sm" class="panel-close-btn" @click="$emit('close')" />
    </div>

    <div v-if="hasAnyContent" class="panel-toolbar">
      <km-input v-model="search" placeholder="Filter..." icon-before="search" clearable dense />
    </div>

    <div class="panel-body">
      <div v-if="!hasAnyContent" class="panel-empty">
        <div class="empty-icon-wrapper">
          <q-icon name="label_off" size="32px" />
        </div>
        <div class="empty-text">No information available</div>
        <div class="empty-subtext">This document has no AI summary or metadata</div>
      </div>

      <div v-else-if="!hasAnyMatch" class="panel-empty">
        <div class="empty-icon-wrapper">
          <q-icon name="search_off" size="32px" />
        </div>
        <div class="empty-text">No matches</div>
        <div class="empty-subtext">Try a different search term</div>
      </div>

      <div v-else class="metadata-groups">
        <!-- AI Summary -->
        <div v-if="showSummary" class="metadata-group">
          <div class="group-header group-header--summary">
            <div class="row items-center q-gutter-x-sm">
              <q-icon name="auto_awesome" size="16px" />
              <span class="group-title">AI Summary</span>
            </div>
          </div>
          <div class="group-content">
            <p class="summary-text">{{ summary }}</p>
          </div>
        </div>

        <!-- File Metadata -->
        <div v-if="filteredFileMetadata.length > 0" class="metadata-group">
          <div class="group-header group-header--file">
            <div class="row items-center q-gutter-x-sm">
              <q-icon name="insert_drive_file" size="16px" />
              <span class="group-title">File Metadata</span>
            </div>
          </div>
          <div class="group-content">
            <div v-for="item in filteredFileMetadata" :key="`file:${item.key}`" class="metadata-item">
              <div class="item-key-wrapper">
                <div class="item-key" :class="{ 'item-key--defined': isDefined(item.key) }">{{ item.label }}</div>
                <q-icon v-if="isDefined(item.key)" name="check_circle" color="primary" size="14px">
                  <q-tooltip>Defined in Metadata Schema</q-tooltip>
                </q-icon>
              </div>
              <div class="item-value">
                <q-badge
                  v-if="item.kind === 'boolean'"
                  :color="item.value === 'Yes' ? 'teal-5' : 'grey-5'"
                  text-color="white"
                  class="boolean-badge"
                >
                  {{ item.value }}
                </q-badge>
                <span v-else class="value-text">{{ item.value }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Source Metadata -->
        <div v-if="filteredSourceMetadata.length > 0" class="metadata-group">
          <div class="group-header group-header--source">
            <div class="row items-center q-gutter-x-sm">
              <q-icon name="cloud_sync" size="16px" />
              <span class="group-title">Source Metadata</span>
            </div>
          </div>
          <div class="group-content">
            <div v-for="item in filteredSourceMetadata" :key="`source:${item.key}`" class="metadata-item">
              <div class="item-key-wrapper">
                <q-icon v-if="isDefined(item.key)" name="fact_check" size="14px" color="primary" class="q-mr-xs">
                  <q-tooltip>Defined in Metadata Schema</q-tooltip>
                </q-icon>
                <div class="item-key" :class="{ 'item-key--defined': isDefined(item.key) }">{{ item.label }}</div>
              </div>
              <div class="item-value">
                <q-badge
                  v-if="item.kind === 'boolean'"
                  :color="item.value === 'Yes' ? 'teal-5' : 'grey-5'"
                  text-color="white"
                  class="boolean-badge"
                >
                  {{ item.value }}
                </q-badge>
                <div v-else-if="item.kind === 'list'" class="value-list">
                  <q-chip v-for="(val, idx) in item.value" :key="idx" dense color="grey-2" text-color="grey-9" class="value-chip">
                    {{ val }}
                  </q-chip>
                </div>
                <span v-else class="value-text">{{ item.value }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- AI Extracted Metadata -->
        <div v-if="filteredLlmMetadata.length > 0" class="metadata-group">
          <div class="group-header group-header--ai">
            <div class="row items-center q-gutter-x-sm">
              <q-icon name="psychology" size="16px" />
              <span class="group-title">Extracted Metadata</span>
            </div>
          </div>
          <div class="group-content">
            <div v-for="item in filteredLlmMetadata" :key="`llm:${item.key}`" class="metadata-item">
              <div class="item-key-wrapper">
                <div class="item-key" :class="{ 'item-key--defined': isDefined(item.key) }">{{ item.label }}</div>
                <q-icon v-if="isDefined(item.key)" name="check_circle" size="14px" color="primary">
                  <q-tooltip>Defined in Metadata Schema</q-tooltip>
                </q-icon>
              </div>
              <div class="item-value">
                <q-badge
                  v-if="item.kind === 'boolean'"
                  :color="item.value === 'Yes' ? 'teal-5' : 'grey-5'"
                  text-color="white"
                  class="boolean-badge"
                >
                  {{ item.value }}
                </q-badge>
                <span v-else class="value-text">{{ item.value }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { fetchData } from '@shared'
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useStore } from 'vuex'

type MetadataOrigin = 'file' | 'source' | 'llm'
type MetadataValueKind = 'string' | 'number' | 'boolean' | 'date' | 'json' | 'list'

interface MetadataItem {
  origin: MetadataOrigin
  key: string
  label: string
  kind: MetadataValueKind
  value: any
}

const props = defineProps<{
  summary?: string | null
  fileMetadata: MetadataItem[]
  sourceMetadata: MetadataItem[]
  llmMetadata: MetadataItem[]
}>()

defineEmits<{
  (e: 'close'): void
}>()

const route = useRoute()
const store = useStore()

const graphId = computed(() => route.params.id as string)
const definedFieldNames = ref<Set<string>>(new Set())
const search = ref('')

const summary = computed(() => (props.summary ?? '').trim())
const hasSummary = computed(() => summary.value.length > 0)

const hasAnyContent = computed(() => hasSummary.value || props.fileMetadata.length + props.sourceMetadata.length + props.llmMetadata.length > 0)

const normalizedQuery = computed(() => search.value.trim().toLowerCase())

const stringifyValue = (val: unknown): string => {
  if (val === null || val === undefined) return ''
  if (Array.isArray(val)) return val.map((v) => stringifyValue(v)).join(' ')
  if (typeof val === 'object') {
    try {
      return JSON.stringify(val)
    } catch {
      return String(val)
    }
  }
  return String(val)
}

const itemMatches = (item: MetadataItem, q: string): boolean => {
  if (!q) return true
  return item.label.toLowerCase().includes(q) || item.key.toLowerCase().includes(q) || stringifyValue(item.value).toLowerCase().includes(q)
}

const filterItems = (items: MetadataItem[]) => {
  const q = normalizedQuery.value
  if (!q) return items
  return items.filter((item) => itemMatches(item, q))
}

const filteredFileMetadata = computed(() => filterItems(props.fileMetadata))
const filteredSourceMetadata = computed(() => filterItems(props.sourceMetadata))
const filteredLlmMetadata = computed(() => filterItems(props.llmMetadata))

const showSummary = computed(() => {
  if (!hasSummary.value) return false
  const q = normalizedQuery.value
  if (!q) return true
  return 'ai summary'.includes(q) || summary.value.toLowerCase().includes(q)
})

const hasAnyMatch = computed(
  () => showSummary.value || filteredFileMetadata.value.length > 0 || filteredSourceMetadata.value.length > 0 || filteredLlmMetadata.value.length > 0
)

const fetchGraphSettings = async () => {
  if (!graphId.value) return
  try {
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
    const response = await fetchData({
      endpoint,
      service: `knowledge_graphs/${graphId.value}`,
      method: 'GET',
      credentials: 'include',
    })
    if (response.ok) {
      const data = await response.json()
      const fields = data.settings?.metadata?.field_definitions || []
      definedFieldNames.value = new Set(fields.map((f: any) => f.name))
    }
  } catch (e) {
    console.error('Error fetching graph settings:', e)
  }
}

const isDefined = (key: string) => definedFieldNames.value.has(key)

onMounted(() => {
  fetchGraphSettings()
})
</script>

<style scoped>
.metadata-panel {
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

.panel-count {
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
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  background: #f8fafc;
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
}

.metadata-groups {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.metadata-group {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
  transition:
    border-color 0.15s ease,
    box-shadow 0.15s ease;
}

.metadata-group:hover {
  border-color: #cbd5e1;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.06);
}

.group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  font-size: 13px;
  font-weight: 600;
  border-bottom: 1px solid #f1f5f9;
}

.group-header--file {
  background: #ffffff;
  color: #334155;
}

.group-header--source {
  background: #ffffff;
  color: #334155;
}

.group-header--ai {
  background: #ffffff;
  color: #334155;
}

.group-header--summary {
  background: #ffffff;
  color: #334155;
}

.group-title {
  font-weight: 600;
}

.group-content {
  padding: 8px 12px;
}

.metadata-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 10px 8px;
  border-radius: 6px;
  transition: background 0.15s ease;
}

.metadata-item:not(:last-child) {
  border-bottom: 1px solid #f8fafc;
}

.metadata-item:hover {
  background: #f8fafc;
}

.item-key-wrapper {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 120px;
  max-width: 120px;
  min-height: 20px;
}

.item-key {
  flex: 1;
  min-width: 0;
  font-size: 12px;
  font-weight: 500;
  color: #64748b;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-key--defined {
  font-weight: 600;
  color: var(--q-primary);
}

.item-value {
  flex: 1;
  min-width: 0;
  min-height: 20px;
}

.value-text {
  font-size: 13px;
  color: #1e293b;
  word-break: break-word;
  line-height: 1.5;
}

.value-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.value-chip {
  margin: 0;
  height: 20px;
  font-size: 11px;
}

.boolean-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 8px;
}

.summary-text {
  margin: 0;
  font-size: 13px;
  line-height: 1.7;
  color: #1e293b;
  white-space: pre-wrap;
}

/* Responsive */
@media (max-width: 1024px) {
  .metadata-panel {
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
