<script setup lang="ts">
/**
 * Command — searchable command palette / menu. Built on Reka UI's Listbox
 * primitive plus a small filter context shared with CommandItem/Group/Empty.
 */
import type { ListboxRootEmits, ListboxRootProps } from 'reka-ui'
import { ListboxRoot, useFilter, useForwardPropsEmits } from 'reka-ui'
import { reactive, ref, watch } from 'vue'
import { provideCommandContext } from './context'

const props = withDefaults(defineProps<ListboxRootProps>(), {
  modelValue: '',
})
const emits = defineEmits<ListboxRootEmits>()

const forwarded = useForwardPropsEmits(props, emits)

const allItems = ref<Map<string, string>>(new Map())
const allGroups = ref<Map<string, Set<string>>>(new Map())

const { contains } = useFilter({ sensitivity: 'base' })
const filterState = reactive({
  search: '',
  filtered: {
    count: 0,
    items: new Map() as Map<string, number>,
    groups: new Set() as Set<string>,
  },
})

function filterItems() {
  if (!filterState.search) {
    filterState.filtered.count = allItems.value.size
    return
  }
  filterState.filtered.groups = new Set()
  let itemCount = 0
  for (const [id, value] of allItems.value) {
    const score = contains(value, filterState.search)
    filterState.filtered.items.set(id, score ? 1 : 0)
    if (score) itemCount++
  }
  for (const [groupId, group] of allGroups.value) {
    for (const itemId of group) {
      if ((filterState.filtered.items.get(itemId) ?? 0) > 0) {
        filterState.filtered.groups.add(groupId)
        break
      }
    }
  }
  filterState.filtered.count = itemCount
}

watch(() => filterState.search, () => {
  filterItems()
})

provideCommandContext({ allItems, allGroups, filterState })
</script>

<template>
  <ListboxRoot
    v-bind="forwarded"
    class="ds-command"
    data-test="ds-command"
  >
    <slot />
  </ListboxRoot>
</template>

<style>
.ds-command {
  display: flex;
  flex-direction: column;
  inline-size: 100%;
  block-size: 100%;
  overflow: hidden;
  background: var(--ds-color-background);
  color: var(--ds-color-black);
  border-radius: var(--ds-radius-md);
}
</style>
