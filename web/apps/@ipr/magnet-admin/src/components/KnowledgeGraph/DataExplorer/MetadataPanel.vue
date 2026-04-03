<template>
  <transition name="meta-slide">
    <div v-if="open" class="metadata-panel">
      <div class="panel-header">
        <div class="panel-header-content">
          <span class="panel-title">Document Info</span>
          <span v-if="totalCount > 0" class="panel-count">{{ totalCount }} fields</span>
        </div>
        <q-btn flat dense round icon="close" size="sm" class="panel-close-btn" @click="$emit('close')" />
      </div>

      <div class="panel-body">
        <div v-if="!hasAnyContent" class="panel-empty">
          <div class="empty-icon-wrapper">
            <q-icon name="label_off" size="32px" />
          </div>
          <div class="empty-text">No information available</div>
          <div class="empty-subtext">This document has no AI summary or metadata</div>
        </div>

        <div v-else class="metadata-groups">
          <!-- AI Summary -->
          <div v-if="hasSummary || totalCount > 0" class="metadata-group">
            <div class="group-header group-header--summary">
              <div class="row items-center q-gutter-x-sm">
                <q-icon name="auto_awesome" size="16px" />
                <span class="group-title">AI Summary</span>
              </div>
            </div>
            <div class="group-content">
              <p v-if="hasSummary" class="summary-text">{{ summary }}</p>
              <div v-else class="text-grey-5 text-italic q-py-sm">No summary available</div>
            </div>
          </div>

          <!-- File Metadata -->
          <div v-if="fileMetadata.length > 0" class="metadata-group">
            <div class="group-header group-header--file">
              <div class="row items-center q-gutter-x-sm">
                <q-icon name="insert_drive_file" size="16px" />
                <span class="group-title">File Properties</span>
              </div>
            </div>
            <div class="group-content">
              <div v-for="item in fileMetadata" :key="`file:${item.key}`" class="metadata-item">
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
          <div v-if="sourceMetadata.length > 0" class="metadata-group">
            <div class="group-header group-header--source">
              <div class="row items-center q-gutter-x-sm">
                <q-icon name="cloud_sync" size="16px" />
                <span class="group-title">Source Information</span>
              </div>
            </div>
            <div class="group-content">
              <div v-for="item in sourceMetadata" :key="`source:${item.key}`" class="metadata-item">
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
                    <q-chip
                      v-for="(val, idx) in item.value"
                      :key="idx"
                      dense
                      color="grey-2"
                      text-color="grey-9"
                      class="value-chip"
                    >
                      {{ val }}
                    </q-chip>
                  </div>
                  <span v-else class="value-text">{{ item.value }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- AI Extracted Metadata -->
          <div v-if="llmMetadata.length > 0" class="metadata-group">
            <div class="group-header group-header--ai">
              <div class="row items-center q-gutter-x-sm">
                <q-icon name="psychology" size="16px" />
                <span class="group-title">AI Extracted</span>
              </div>
            </div>
            <div class="group-content">
              <div v-for="item in llmMetadata" :key="`llm:${item.key}`" class="metadata-item">
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
  </transition>
</template>

<script setup lang="ts">
import { fetchData } from '@shared'
import { m } from '@/paraglide/messages'
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/stores/appStore'

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
  open: boolean
  summary?: string | null
  fileMetadata: MetadataItem[]
  sourceMetadata: MetadataItem[]
  llmMetadata: MetadataItem[]
}>()

defineEmits<{
  (e: 'close'): void
}>()

const route = useRoute()
const appStore = useAppStore()

const graphId = computed(() => route.params.id as string)
const definedFieldNames = ref<Set<string>>(new Set())

const summary = computed(() => (props.summary ?? '').trim())
const hasSummary = computed(() => summary.value.length > 0)

const hasAnyContent = computed(() => hasSummary.value || props.fileMetadata.length + props.sourceMetadata.length + props.llmMetadata.length > 0)

const totalCount = computed(() => props.fileMetadata.length + props.sourceMetadata.length + props.llmMetadata.length)

const fetchGraphSettings = async () => {
  if (!graphId.value) return
  try {
    const endpoint = appStore.config.api.aiBridge.urlAdmin
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
  background: var(--q-white);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: var(--radius-xl);
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
  background: var(--q-white);
  border-bottom: 1px solid var(--q-border);
  color: var(--q-black);
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
  font-size: var(--km-font-size-caption);
  color: var(--q-label);
  font-weight: 500;
}

.panel-close-btn {
  color: var(--q-icon);
}

.panel-close-btn:hover {
  color: var(--q-secondary-text);
  background: var(--q-border);
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: var(--q-background);
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
  background: var(--q-white);
  border: 1px solid var(--q-border);
  border-radius: var(--radius-full);
  margin-bottom: 16px;
  color: var(--q-icon);
}

.empty-text {
  font-size: var(--km-font-size-body);
  font-weight: 600;
  color: var(--q-label);
  margin-bottom: 4px;
}

.empty-subtext {
  font-size: var(--km-font-size-caption);
  color: var(--q-icon);
}

.metadata-groups {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.metadata-group {
  background: var(--q-white);
  border: 1px solid var(--q-border);
  border-radius: var(--radius-xl);
  overflow: hidden;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

.group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  font-size: var(--km-font-size-label);
  font-weight: 600;
  border-bottom: 1px solid var(--q-border);
}

.group-header--file {
  background: var(--q-white);
  color: var(--q-black);
}

.group-header--source {
  background: var(--q-white);
  color: var(--q-black);
}

.group-header--ai {
  background: var(--q-white);
  color: var(--q-black);
}

.group-header--summary {
  background: var(--q-white);
  color: var(--q-black);
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
  border-radius: var(--radius-md);
  transition: background 0.15s ease;
}

.metadata-item:not(:last-child) {
  border-bottom: 1px solid var(--q-background);
}

.metadata-item:hover {
  background: var(--q-background);
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
  font-size: var(--km-font-size-caption);
  font-weight: 500;
  color: var(--q-label);
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
  font-size: var(--km-font-size-label);
  color: var(--q-black);
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
  font-size: var(--km-font-size-sm);
}

.boolean-badge {
  font-size: var(--km-font-size-xs);
  font-weight: 600;
  padding: 2px 8px;
}

.summary-text {
  margin: 0;
  font-size: var(--km-font-size-label);
  line-height: 1.7;
  color: var(--q-black);
  white-space: pre-wrap;
}

/* Slide transition */
.meta-slide-enter-active,
.meta-slide-leave-active {
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
}

.meta-slide-enter-from,
.meta-slide-leave-to {
  opacity: 0;
  transform: translateX(12px);
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
      0 8px 10px -6px rgba(0, 0, 0, 0.1); /* intentional elevation shadow */
  }
}
</style>
