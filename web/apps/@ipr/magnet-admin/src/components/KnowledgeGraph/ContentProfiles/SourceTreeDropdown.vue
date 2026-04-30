<template>
  <ds-popover placement="bottom" align="start" :side-offset="4">
    <template #trigger>
      <kg-inline-field interactive>
        <span class="source-dropdown-label">{{ displayLabel }}</span>
        <km-glyph name="chevron-down" size="16px" />
      </kg-inline-field>
    </template>

    <div class="source-dropdown-content">
      <!-- Level 1: Any Source -->
      <div
        v-if="allowAllSources"
        class="source-item source-item--root"
        :class="{ 'source-item--selected': isAllSourcesSelected, 'source-item--clickable': true }"
        @click="toggleAllSources"
      >
        <div class="source-item-checkbox" :class="{ 'source-item-checkbox--active': isAllSourcesSelected }">
          <km-glyph v-if="isAllSourcesSelected" name="check" size="10px" class="source-item-checkbox-icon" />
        </div>
        <span class="source-item-label">{{ m.knowledgeGraph_anySource() }}</span>
      </div>

      <!-- Level 2: Source type groups -->
      <template v-for="group in visibleSourceGroups" :key="group.type">
        <!-- Manual Upload: flat entry -->
        <template v-if="group.type === 'upload'">
          <div
            class="source-item source-item--type"
            :class="{
              'source-item--selected': isGroupSelected(group.type),
              'source-item--disabled': isAllSourcesSelected,
              'source-item--clickable': !isAllSourcesSelected,
            }"
            @click="!isAllSourcesSelected && toggleGroup(group.type)"
          >
            <div
              class="source-item-checkbox"
              :class="{ 'source-item-checkbox--active': isGroupSelected(group.type) || isAllSourcesSelected }"
            >
              <km-glyph
                v-if="isGroupSelected(group.type) || isAllSourcesSelected"
                name="check"
                size="10px"
                class="source-item-checkbox-icon"
              />
            </div>
            <span class="source-item-label">{{ group.label }}</span>
          </div>
        </template>

        <!-- Other types: group with children -->
        <template v-else>
          <div
            class="source-item source-item--type"
            :class="{
              'source-item--selected': isGroupSelected(group.type),
              'source-item--disabled': isAllSourcesSelected,
              'source-item--clickable': !isAllSourcesSelected,
            }"
            @click="!isAllSourcesSelected && toggleGroup(group.type)"
          >
            <div
              class="source-item-checkbox"
              :class="{ 'source-item-checkbox--active': isGroupSelected(group.type) || isAllSourcesSelected }"
            >
              <km-glyph
                v-if="isGroupSelected(group.type) || isAllSourcesSelected"
                name="check"
                size="10px"
                class="source-item-checkbox-icon"
              />
            </div>
            <span class="source-item-label">{{ m.knowledgeGraph_anyNamedSource({ name: group.label }) }}</span>
          </div>

          <!-- Level 3: Individual sources -->
          <template v-if="allowIndividualSources">
            <div
              v-for="source in group.sources"
              :key="source.id"
              class="source-item source-item--source"
              :class="{
                'source-item--selected': isSourceSelected(source.id),
                'source-item--disabled': isAllSourcesSelected || isGroupSelected(group.type),
                'source-item--clickable': !isAllSourcesSelected && !isGroupSelected(group.type),
              }"
              @click="!isAllSourcesSelected && !isGroupSelected(group.type) && toggleSource(source.id)"
            >
              <div
                class="source-item-checkbox"
                :class="{ 'source-item-checkbox--active': isSourceSelected(source.id) || isGroupSelected(group.type) || isAllSourcesSelected }"
              >
                <km-glyph
                  v-if="isSourceSelected(source.id) || isGroupSelected(group.type) || isAllSourcesSelected"
                  name="check"
                  size="10px"
                  class="source-item-checkbox-icon"
                />
              </div>
              <span class="source-item-label">{{ source.name }}</span>
            </div>
          </template>
        </template>
      </template>
    </div>
  </ds-popover>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { m } from '@/paraglide/messages'
import { DsPopover } from '@ds/primitives'
import KgInlineField from '../common/KgInlineField.vue'
import type { SourceRow } from '../Sources/models'
import { sourceRegistry, type SourceTypeKey } from '../Sources/SourceTypes/registry'

interface SourceGroup {
  type: string
  label: string
  sources: SourceRow[]
}

const props = withDefaults(
  defineProps<{
  modelValue: string[]
  sources: SourceRow[]
  allowedGroupTypes?: string[]
  allowAllSources?: boolean
  allowIndividualSources?: boolean
}>(),
  {
    allowAllSources: true,
    allowIndividualSources: true,
  }
)

const emit = defineEmits<{
  'update:modelValue': [value: string[]]
}>()

const ALL_SOURCES_KEY = '__ALL__'
const groupKey = (type: string) => `__GROUP__${type}`

const selectedSet = computed(() => new Set(props.modelValue))

const isAllSourcesSelected = computed(() => selectedSet.value.has(ALL_SOURCES_KEY))

const isGroupSelected = (type: string) => selectedSet.value.has(groupKey(type))

const isSourceSelected = (id: string) => selectedSet.value.has(id)

const sourceGroups = computed<SourceGroup[]>(() => {
  const groupMap = new Map<string, SourceRow[]>()
  for (const source of props.sources) {
    const type = source.type || 'unknown'
    if (!groupMap.has(type)) groupMap.set(type, [])
    groupMap.get(type)!.push(source)
  }

  const typeOrder: SourceTypeKey[] = ['sharepoint', 'fluid_topics', 'confluence', 'api_ingest', 'upload']

  return typeOrder
    .filter((type) => !sourceRegistry[type].comingSoon)
    .map((type) => ({
      type,
      label: type === 'upload' ? m.knowledgeGraph_manualUploads() : sourceRegistry[type].label,
      sources: groupMap.get(type) || [],
    }))
})

const visibleSourceGroups = computed(() => {
  if (!props.allowedGroupTypes?.length) {
    return sourceGroups.value
  }

  const allowedGroups = new Set(props.allowedGroupTypes)
  return sourceGroups.value.filter((group) => allowedGroups.has(group.type))
})

const displayLabel = computed(() => {
  if (isAllSourcesSelected.value) return 'any source'

  const parts: string[] = []

  for (const group of visibleSourceGroups.value) {
    if (isGroupSelected(group.type)) {
      if (group.type === 'upload') {
        parts.push(group.label.toLowerCase())
      } else {
        parts.push(`any ${group.label} source`)
      }
    } else if (props.allowIndividualSources) {
      for (const s of group.sources) {
        if (isSourceSelected(s.id)) parts.push(s.name)
      }
    }
  }

  if (parts.length === 0) return 'no source'
  if (parts.length === 1) return parts[0]
  return `${parts.length} sources`
})

const emitUpdate = (ids: string[]) => {
  emit('update:modelValue', ids)
}

const toggleAllSources = () => {
  const current = new Set(selectedSet.value)
  if (current.has(ALL_SOURCES_KEY)) {
    current.delete(ALL_SOURCES_KEY)
  } else {
    // Selecting "All Sources" clears everything else
    current.clear()
    current.add(ALL_SOURCES_KEY)
  }
  emitUpdate([...current])
}

const toggleGroup = (type: string) => {
  const key = groupKey(type)
  const current = new Set(selectedSet.value)

  if (current.has(key)) {
    current.delete(key)
  } else {
    current.add(key)
    // Remove individual sources of this group since group is now selected
    const group = sourceGroups.value.find((g) => g.type === type)
    if (group) {
      group.sources.forEach((s) => current.delete(s.id))
    }
  }
  emitUpdate([...current])
}

const toggleSource = (id: string) => {
  const current = new Set(selectedSet.value)
  if (current.has(id)) {
    current.delete(id)
  } else {
    current.add(id)
  }
  emitUpdate([...current])
}
</script>

<style scoped>
.source-dropdown-label {
  font-family: inherit;
  min-inline-size: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.source-dropdown-content {
  min-inline-size: 280px;
  max-block-size: 380px;
  overflow-block: auto;
}

.source-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 7px 10px;
  border-radius: var(--ds-radius-md);
  transition: background 0.12s ease;
}

.source-item--clickable {
  cursor: pointer;
}

.source-item--clickable:hover {
  background: var(--ds-color-primary-bg);
}

.source-item--disabled {
  cursor: default;
  opacity: 0.5;
}

.source-item--root {
  margin-block-end: 4px;
}

.source-item--root .source-item-label {
  font-size: var(--ds-font-size-label);
  font-weight: 600;
  color: var(--ds-color-black);
}

.source-item--type {
  padding-inline-start: 22px;
}

.source-item--type .source-item-label {
  font-size: var(--ds-font-size-caption);
  font-weight: 500;
  color: var(--ds-color-secondary-text);
}

.source-item--source {
  padding-inline-start: 44px;
}

.source-item--source .source-item-label {
  font-size: var(--ds-font-size-caption);
  font-weight: 400;
  color: var(--ds-color-label);
}

.source-item-checkbox {
  inline-size: 14px;
  block-size: 14px;
  border-radius: var(--ds-radius-xs);
  border: 1.5px solid var(--ds-color-border-2);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: var(--ds-color-white);
  transition:
    border-color 0.15s ease,
    background 0.15s ease;
}

.source-item--clickable:hover .source-item-checkbox {
  border-color: var(--ds-color-secondary);
}

.source-item-checkbox--active {
  border-color: var(--ds-color-primary);
  background: var(--ds-color-primary);
}

.source-item-checkbox-icon {
  color: var(--ds-color-static-white);
}

.source-item--disabled .source-item-checkbox {
  border-color: var(--ds-color-border);
}

.source-item--disabled .source-item-checkbox--active {
  background: var(--ds-color-secondary-bg);
  border-color: var(--ds-color-secondary-bg);
}

.source-item-label {
  flex: 1;
  min-inline-size: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
