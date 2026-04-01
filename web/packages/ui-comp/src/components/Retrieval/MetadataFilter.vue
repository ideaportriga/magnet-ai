<template>
  <div class="column">
    <div class="row items-baseline q-mb-xs">
      <div :class="labelClass ?? 'km-heading-4 q-mr-sm'">{{ label ?? 'Metadata filters' }}</div>
      <q-btn icon="fas fa-plus" padding="xs" :size="iconSize ?? 'xs'" flat>
        <q-menu>
          <q-list>
            <q-item v-for="field in availableMetadataFields" :key="field" v-close-popup clickable @click="showNewFilterPopup(field)">
              <q-item-section>
                <q-item-label>{{ field }}</q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </q-menu>
      </q-btn>
    </div>

    <div class="row">
      <retrieval-metadata-filter-editor ref="newFilterPopup" title="Add filter" save-button-label="Add" @save="addFilter" />
      <retrieval-metadata-filter-editor ref="editFilterPopup" title="Edit filter" save-button-label="Save" @save="updateFilter" />
    </div>

    <retrieval-metadata-filter-chip-list v-model="filters" @click="showEditFilterPopup" @remove="removeFilter" />
  </div>
</template>

<script setup lang="ts">
import { computed, useTemplateRef, inject, ref } from 'vue'
import type { Filter } from '@shared/types'
import _ from 'lodash'

// Parent provides 'collectionsList' ref via provide/inject
const allKnowledgeSources = inject<any>('collectionsList', ref([]))

// Models & Props
const filters = defineModel<Filter[]>({ default: [] })
const { sources } = defineProps<{
  sources?: string[]
  label?: string
  labelClass?: string
  iconSize?: string
}>()

const newFilterPopup = useTemplateRef('newFilterPopup')
const editFilterPopup = useTemplateRef('editFilterPopup')

const availableMetadataFields = computed(() => {
  const items = allKnowledgeSources?.value || []
  const filteredSources = !sources
    ? items
    : items.filter((source: any) => (sources || []).includes(source?.system_name))
  const fields: string[] = filteredSources.flatMap((source: any) =>
    (source?.metadata_config || [])
      .filter((config: any) => config.enabled)
      .map((config: any) => config.name)
      .filter((field: string) => !filters.value.find((filter) => filter.field === field))
  )
  return [...new Set(fields)].sort()
})

const showNewFilterPopup = (field: string) => {
  ;(newFilterPopup as any).value?.show({
    field: field,
    operator: 'equal',
    conditions: [],
  })
}

const showEditFilterPopup = (filter: Filter) => {
  ;(editFilterPopup as any).value?.show(filter)
}

const addFilter = (newFilter: Filter) => {
  filters.value = [...filters.value, newFilter]
}

const updateFilter = (updatedFilter: Filter, filter: Filter) => {
  Object.assign(filter, _.cloneDeep(updatedFilter))
  filters.value = [...filters.value]
}

const removeFilter = (filter: Filter) => {
  filters.value = filters.value.filter((f) => f !== filter)
}
</script>
