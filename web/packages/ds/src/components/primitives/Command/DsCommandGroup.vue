<script setup lang="ts">
/**
 * CommandGroup — labelled group of CommandItem children. Auto-hides itself
 * when the active search filters out every child.
 */
import type { ListboxGroupProps } from 'reka-ui'
import { ListboxGroup, ListboxGroupLabel, useId } from 'reka-ui'
import { computed, onMounted, onUnmounted } from 'vue'
import { provideCommandGroupContext, useCommandContext } from './context'

const props = defineProps<ListboxGroupProps & { heading?: string }>()

const { allGroups, filterState } = useCommandContext()
const id = useId()

const isRender = computed(() =>
  !filterState.search ? true : filterState.filtered.groups.has(id),
)

provideCommandGroupContext({ id })
onMounted(() => {
  if (!allGroups.value.has(id)) allGroups.value.set(id, new Set())
})
onUnmounted(() => {
  allGroups.value.delete(id)
})
</script>

<template>
  <ListboxGroup
    v-bind="props"
    :id="id"
    class="ds-command__group"
    data-test="ds-command-group"
    :hidden="isRender ? undefined : true"
  >
    <ListboxGroupLabel
      v-if="heading"
      class="ds-command__group-heading"
    >
      {{ heading }}
    </ListboxGroupLabel>
    <slot />
  </ListboxGroup>
</template>

<style>
.ds-command__group {
  overflow: hidden;
  padding: var(--ds-space-2xs);
  color: var(--ds-color-black);
}
.ds-command__group-heading {
  display: block;
  padding-inline: var(--ds-space-xs);
  padding-block: var(--ds-space-2xs);
  font-size: var(--ds-font-size-xs);
  font-weight: var(--ds-font-weight-medium);
  color: var(--ds-color-text-grey);
}
</style>
