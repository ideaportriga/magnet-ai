<template>
  <div class="full-width mb-sm">
    <km-select height="auto" min-height="36px" :placeholder="m.entity_testSet()" :options="setItems" :model-value="selectedTestSet" option-value="system_name" option-label="name" emit-value map-options has-dropdown-search @update:model-value="$emit(&quot;update:selectedTestSet&quot;, $event)" />
  </div>
  <template v-if="selectedTestSet">
    <div class="cluster mb-sm">
      <km-input :placeholder="m.common_search()" icon-before="search" :model-value="globalFilter" clearable @input="globalFilter = $event" />
    </div>
    <div class="full-width">
      <km-data-table :table="table" row-key="user_input" :active-row-id="activeRowInput" @row-click="$emit(&quot;selectRecord&quot;, $event)" />
    </div>
  </template>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { m } from '@/paraglide/messages'
import { useEntityQueries } from '@/queries/entities'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
import { textColumn } from '@/utils/columnHelpers'

const props = defineProps<{
  selectedTestSet: string
  activeRowInput?: string
}>()

defineEmits<{
  'update:selectedTestSet': [value: string]
  selectRecord: [row: Record<string, unknown>]
}>()

const queries = useEntityQueries()
const { data: evaluationSetsListData } = queries.evaluation_sets.useList()

const setItems = computed(() => evaluationSetsListData.value?.items ?? [])
const testSetObject = computed(() =>
  setItems.value.find(({ system_name }: any) => system_name === props.selectedTestSet),
)
const testSetItems = computed(() => (testSetObject.value as any)?.items || [])

const columns = [
  textColumn<any>('user_input', 'User Input'),
  textColumn<any>('expected_result', 'Expected Result'),
]

const { table, globalFilter } = useLocalDataTable(testSetItems, columns, {
  defaultPageSize: 10,
})
</script>
