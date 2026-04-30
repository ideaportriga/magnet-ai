<template>
  <transition name="meta-slide">
    <div v-if="open" class="metadata-panel">
      <div class="panel-header">
        <div class="panel-header-content">
          <span class="panel-title">{{ m.dataExplorer_documentInfo() }}</span>
          <span v-if="totalCount > 0" class="panel-count">{{ m.dataExplorer_fields({ count: totalCount }) }}</span>
        </div>
        <km-btn flat dense round icon="close" size="sm" class="panel-close-btn" @click="$emit('close')" />
      </div>

      <div class="panel-body">
        <div v-if="!hasAnyContent" class="panel-empty">
          <div class="empty-icon-wrapper">
            <km-glyph name="label_off" size="32px" />
          </div>
          <div class="empty-text">{{ m.dataExplorer_noInformation() }}</div>
          <div class="empty-subtext">{{ m.dataExplorer_noInformationDesc() }}</div>
        </div>

        <div v-else class="metadata-groups">
          <!-- AI Summary -->
          <div v-if="hasSummary || totalCount > 0" class="metadata-group">
            <div class="group-header group-header--summary">
              <div class="cluster gap-x-sm">
                <km-glyph name="magic" size="16px" />
                <span class="group-title">{{ m.dataExplorer_aiSummary() }}</span>
              </div>
            </div>
            <div class="group-content">
              <p v-if="hasSummary" class="summary-text">{{ summary }}</p>
              <div v-else class="text-grey-5 text-italic py-sm">{{ m.dataExplorer_noSummary() }}</div>
            </div>
          </div>

          <!-- File Metadata -->
          <div v-if="fileMetadata.length > 0" class="metadata-group">
            <div class="group-header group-header--file">
              <div class="cluster gap-x-sm">
                <km-glyph name="file" size="16px" />
                <span class="group-title">{{ m.dataExplorer_fileProperties() }}</span>
              </div>
            </div>
            <div class="group-content">
              <div v-for="item in fileMetadata" :key="`file:${item.key}`" class="metadata-item">
                <div class="item-key-wrapper">
                  <div class="item-key" :class="{ 'item-key--defined': isDefined(item.key) }">{{ item.label }}</div>
                  <km-glyph v-if="isDefined(item.key)" name="check" tone="brand" size="14px">
                    <km-tooltip>{{ m.dataExplorer_definedInSchema() }}</km-tooltip>
                  </km-glyph>
                </div>
                <div class="item-value">
                  <km-badge
                    v-if="item.kind === 'boolean'"
                    :tone="item.value === 'Yes' ? 'success' : 'neutral'"
                    class="boolean-badge"
                  >
                    {{ item.value }}
                  </km-badge>
                  <span v-else class="value-text">{{ item.value }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Source Metadata -->
          <div v-if="sourceMetadata.length > 0" class="metadata-group">
            <div class="group-header group-header--source">
              <div class="cluster gap-x-sm">
                <km-glyph name="cloud_sync" size="16px" />
                <span class="group-title">{{ m.dataExplorer_sourceInformation() }}</span>
              </div>
            </div>
            <div class="group-content">
              <div v-for="item in sourceMetadata" :key="`source:${item.key}`" class="metadata-item">
                <div class="item-key-wrapper">
                  <km-glyph v-if="isDefined(item.key)" name="clipboard-check" size="14px" tone="brand" class="mr-xs">
                    <km-tooltip>{{ m.dataExplorer_definedInSchema() }}</km-tooltip>
                  </km-glyph>
                  <div class="item-key" :class="{ 'item-key--defined': isDefined(item.key) }">{{ item.label }}</div>
                </div>
                <div class="item-value">
                  <km-badge
                    v-if="item.kind === 'boolean'"
                    :tone="item.value === 'Yes' ? 'success' : 'neutral'"
                    class="boolean-badge"
                  >
                    {{ item.value }}
                  </km-badge>
                  <div v-else-if="item.kind === 'list'" class="value-list">
                    <km-chip
                      v-for="(val, idx) in item.value"
                      :key="idx"
                      dense
                      tone="neutral"
                      class="value-chip"
                    >
                      {{ val }}
                    </km-chip>
                  </div>
                  <span v-else class="value-text">{{ item.value }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- AI Extracted Metadata -->
          <div v-if="llmMetadata.length > 0" class="metadata-group">
            <div class="group-header group-header--ai">
              <div class="cluster gap-x-sm">
                <km-glyph name="brain" size="16px" />
                <span class="group-title">{{ m.dataExplorer_aiExtracted() }}</span>
              </div>
            </div>
            <div class="group-content">
              <div v-for="item in llmMetadata" :key="`llm:${item.key}`" class="metadata-item">
                <div class="item-key-wrapper">
                  <div class="item-key" :class="{ 'item-key--defined': isDefined(item.key) }">{{ item.label }}</div>
                  <km-glyph v-if="isDefined(item.key)" name="check" size="14px" tone="brand">
                    <km-tooltip>{{ m.dataExplorer_definedInSchema() }}</km-tooltip>
                  </km-glyph>
                </div>
                <div class="item-value">
                  <km-badge
                    v-if="item.kind === 'boolean'"
                    :tone="item.value === 'Yes' ? 'success' : 'neutral'"
                    class="boolean-badge"
                  >
                    {{ item.value }}
                  </km-badge>
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
  inline-size: 380px;
  min-inline-size: 380px;
  background: var(--ds-color-white);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: var(--ds-radius-xl);
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
  background: var(--ds-color-white);
  border-block-end: 1px solid var(--ds-color-border);
  color: var(--ds-color-black);
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
  font-size: var(--ds-font-size-caption);
  color: var(--ds-color-label);
  font-weight: 500;
}

.panel-close-btn {
  color: var(--ds-color-icon);
}

.panel-close-btn:hover {
  color: var(--ds-color-secondary-text);
  background: var(--ds-color-border);
}

.panel-body {
  flex: 1;
  overflow-block: auto;
  padding: 16px;
  background: var(--ds-color-background);
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
  inline-size: 64px;
  block-size: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--ds-color-white);
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-full);
  margin-block-end: 16px;
  color: var(--ds-color-icon);
}

.empty-text {
  font-size: var(--ds-font-size-body);
  font-weight: 600;
  color: var(--ds-color-label);
  margin-block-end: 4px;
}

.empty-subtext {
  font-size: var(--ds-font-size-caption);
  color: var(--ds-color-icon);
}

.metadata-groups {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.metadata-group {
  background: var(--ds-color-white);
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-xl);
  overflow: hidden;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

.group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  font-size: var(--ds-font-size-label);
  font-weight: 600;
  border-block-end: 1px solid var(--ds-color-border);
}

.group-header--file {
  background: var(--ds-color-white);
  color: var(--ds-color-black);
}

.group-header--source {
  background: var(--ds-color-white);
  color: var(--ds-color-black);
}

.group-header--ai {
  background: var(--ds-color-white);
  color: var(--ds-color-black);
}

.group-header--summary {
  background: var(--ds-color-white);
  color: var(--ds-color-black);
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
  border-radius: var(--ds-radius-md);
  transition: background 0.15s ease;
}

.metadata-item:not(:last-child) {
  border-block-end: 1px solid var(--ds-color-background);
}

.metadata-item:hover {
  background: var(--ds-color-background);
}

.item-key-wrapper {
  display: flex;
  align-items: center;
  gap: 6px;
  min-inline-size: 120px;
  max-inline-size: 120px;
  min-block-size: 20px;
}

.item-key {
  flex: 1;
  min-inline-size: 0;
  font-size: var(--ds-font-size-caption);
  font-weight: 500;
  color: var(--ds-color-label);
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-key--defined {
  font-weight: 600;
  color: var(--ds-color-primary);
}

.item-value {
  flex: 1;
  min-inline-size: 0;
  min-block-size: 20px;
}

.value-text {
  font-size: var(--ds-font-size-label);
  color: var(--ds-color-black);
  overflow-wrap: break-word;
  line-height: 1.5;
}

.value-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.value-chip {
  margin: 0;
  block-size: 20px;
  font-size: var(--ds-font-size-sm);
}

.boolean-badge {
  font-size: var(--ds-font-size-xs);
  font-weight: 600;
  padding: 2px 8px;
}

.summary-text {
  margin: 0;
  font-size: var(--ds-font-size-label);
  line-height: 1.7;
  color: var(--ds-color-black);
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
    inset-block: 16px;
    inset-inline-end: 16px;
    z-index: 10;
    inline-size: 400px;
    max-inline-size: calc(100% - 32px);
    min-inline-size: 0;
    box-shadow:
      0 10px 25px -5px rgba(0, 0, 0, 0.1),
      0 8px 10px -6px rgba(0, 0, 0, 0.1); /* intentional elevation shadow */
  }
}
</style>
