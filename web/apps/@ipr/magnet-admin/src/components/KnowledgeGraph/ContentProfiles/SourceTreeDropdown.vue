<template>
  <kg-inline-field interactive @click.stop>
    <span class="source-dropdown-label">{{ displayLabel }}</span>
    <q-icon name="arrow_drop_down" size="16px" />
    <q-menu
      ref="menuRef"
      anchor="bottom left"
      self="top left"
      class="source-dropdown-menu"
      :offset="[0, 4]"
    >
      <div class="source-dropdown-content">
        <!-- Level 1: Any Source -->
        <div
          v-if="allowAllSources"
          class="source-item source-item--root"
          :class="{ 'source-item--selected': isAllSourcesSelected, 'source-item--clickable': true }"
          @click="toggleAllSources"
        >
          <div class="source-item-checkbox" :class="{ 'source-item-checkbox--active': isAllSourcesSelected }">
            <q-icon v-if="isAllSourcesSelected" name="check" size="10px" class="source-item-checkbox-icon" />
          </div>
          <span class="source-item-label">Any Source</span>
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
                <q-icon
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
                <q-icon
                  v-if="isGroupSelected(group.type) || isAllSourcesSelected"
                  name="check"
                  size="10px"
                  class="source-item-checkbox-icon"
                />
              </div>
              <span class="source-item-label">Any {{ group.label }} source</span>
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
                  <q-icon
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
    </q-menu>
  </kg-inline-field>
</template>

<script setup lang="ts">
import { computed } from 'vue'
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
      label: type === 'upload' ? 'Manual Uploads' : sourceRegistry[type].label,
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
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.source-dropdown-content {
  min-width: 280px;
  max-height: 380px;
  overflow-y: auto;
  padding: 8px 6px;
}

.source-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 7px 10px;
  border-radius: var(--radius-md);
  transition: background 0.12s ease;
}

.source-item--clickable {
  cursor: pointer;
}

.source-item--clickable:hover {
  background: var(--q-primary-bg);
}

.source-item--disabled {
  cursor: default;
  opacity: 0.5;
}

.source-item--root {
  margin-bottom: 4px;
}

.source-item--root .source-item-label {
  font-size: var(--km-font-size-label);
  font-weight: 600;
  color: var(--q-black);
}

.source-item--type {
  padding-left: 22px;
}

.source-item--type .source-item-label {
  font-size: var(--km-font-size-caption);
  font-weight: 500;
  color: var(--q-secondary-text);
}

.source-item--source {
  padding-left: 44px;
}

.source-item--source .source-item-label {
  font-size: var(--km-font-size-caption);
  font-weight: 400;
  color: var(--q-label);
}

.source-item-checkbox {
  width: 14px;
  height: 14px;
  border-radius: var(--radius-xs);
  border: 1.5px solid var(--q-border-2);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: var(--q-white);
  transition:
    border-color 0.15s ease,
    background 0.15s ease;
}

.source-item--clickable:hover .source-item-checkbox {
  border-color: var(--q-secondary);
}

.source-item-checkbox--active {
  border-color: var(--q-primary);
  background: var(--q-primary);
}

.source-item-checkbox-icon {
  color: var(--q-white);
}

.source-item--disabled .source-item-checkbox {
  border-color: var(--q-border);
}

.source-item--disabled .source-item-checkbox--active {
  background: var(--q-secondary-bg);
  border-color: var(--q-secondary-bg);
}

.source-item-label {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>

<style>
.source-dropdown-menu {
  border-radius: var(--radius-xl);
  box-shadow:
    0 4px 20px var(--q-primary-transparent),
    0 8px 40px rgba(45, 36, 56, 0.12);
  border: 1px solid var(--q-border);
  background: var(--q-white);
}
</style>
