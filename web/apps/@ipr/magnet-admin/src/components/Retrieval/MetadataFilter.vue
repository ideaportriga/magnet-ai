<script setup lang="ts">
/**
 * Metadata filter list — admin-only. Migrated from `@ui-comp/Retrieval/`
 * to `magnet-admin/components/Retrieval/` in Phase 4c, rewritten on `@ds`.
 *
 * Public surface preserved (`v-model="filters"`, `:sources`, `:collections`,
 * `:label`, `:label-class`, `:icon-size`). Auto-registered globally as
 * `<retrieval-metadata-filter>` via admin's `getComponentList`.
 */

import { computed, useTemplateRef } from 'vue'
import _ from 'lodash'
import type { Filter } from '@shared/types'
import { DsDropdownMenu } from '@ds/primitives'
import KmBtn from '@ds/components/domain/KmBtn.vue'
import RetrievalMetadataFilterEditor from './MetadataFilterEditor.vue'
import RetrievalMetadataFilterChipList from './MetadataFilterChipList.vue'

interface MetadataConfig {
  name: string
  enabled: boolean
}
interface Source {
  system_name?: string
  metadata_config?: MetadataConfig[]
}

const filters = defineModel<Filter[]>({ default: () => [] })
const props = defineProps<{
  sources?: string[]
  collections?: Source[]
  label?: string
  labelClass?: string
  iconSize?: string
}>()

const newFilterPopup = useTemplateRef<{ show: (f: Filter) => void } | null>('newFilterPopup')
const editFilterPopup = useTemplateRef<{ show: (f: Filter) => void } | null>('editFilterPopup')

const availableMetadataFields = computed(() => {
  const items = props.collections ?? []
  const filteredSources = !props.sources
    ? items
    : items.filter((source) => (props.sources ?? []).includes(source.system_name ?? ''))
  const fields = filteredSources.flatMap((source) =>
    (source.metadata_config ?? [])
      .filter((config) => config.enabled)
      .map((config) => config.name)
      .filter((field) => !filters.value.find((filter) => filter.field === field)),
  )
  return [...new Set(fields)].sort()
})

const menuItems = computed(() =>
  availableMetadataFields.value.map((field) => ({
    label: field,
    onSelect: () => showNewFilterPopup(field),
  })),
)

function showNewFilterPopup(field: string) {
  newFilterPopup.value?.show({ field, operator: 'equal', conditions: [] } as unknown as Filter)
}

function showEditFilterPopup(filter: Filter) {
  editFilterPopup.value?.show(filter)
}

function addFilter(newFilter: Filter) {
  filters.value = [...filters.value, newFilter]
}

function updateFilter(updatedFilter: Filter, filter: Filter) {
  Object.assign(filter, _.cloneDeep(updatedFilter))
  filters.value = [...filters.value]
}

function removeFilter(filter: Filter) {
  filters.value = filters.value.filter((f) => f !== filter)
}
</script>

<template>
  <div class="metadata-filter stack" data-gap="2xs">
    <div class="metadata-filter__header cluster gap-sm" data-align="baseline">
      <span :class="labelClass ?? 'metadata-filter__label'">
        {{ label ?? 'Metadata filters' }}
      </span>
      <DsDropdownMenu :items="menuItems">
        <template #trigger>
          <KmBtn flat icon="add" :icon-size="iconSize ?? '14px'" />
        </template>
      </DsDropdownMenu>
    </div>

    <div>
      <RetrievalMetadataFilterEditor
        ref="newFilterPopup"
        title="Add filter"
        save-button-label="Add"
        @save="addFilter"
      />
      <RetrievalMetadataFilterEditor
        ref="editFilterPopup"
        title="Edit filter"
        save-button-label="Save"
        @save="updateFilter"
      />
    </div>

    <RetrievalMetadataFilterChipList
      v-model="filters"
      @click="showEditFilterPopup"
      @remove="removeFilter"
    />
  </div>
</template>

<style scoped>
.metadata-filter__label {
  font-size: var(--ds-font-size-body);
  font-weight: var(--ds-font-weight-semibold);
}
</style>
