<script setup lang="ts">
/**
 * CommandItem — a selectable row inside a CommandList. Auto-hides on
 * non-matching searches; clearing on select restores the full list.
 */
import type { ListboxItemEmits, ListboxItemProps } from 'reka-ui'
import { useCurrentElement } from '@vueuse/core'
import { ListboxItem, useForwardPropsEmits, useId } from 'reka-ui'
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useCommandContext, useCommandGroupContext } from './context'

const props = defineProps<ListboxItemProps>()
const emits = defineEmits<ListboxItemEmits>()

const forwarded = useForwardPropsEmits(props, emits)

const id = useId()
const { filterState, allItems, allGroups } = useCommandContext()
const groupContext = useCommandGroupContext(null)

const isRender = computed(() => {
  if (!filterState.search) return true
  const filteredCurrentItem = filterState.filtered.items.get(id)
  if (filteredCurrentItem === undefined) return true
  return filteredCurrentItem > 0
})

const itemRef = ref()
const currentElement = useCurrentElement(itemRef)
onMounted(() => {
  if (!(currentElement.value instanceof HTMLElement)) return
  allItems.value.set(
    id,
    currentElement.value.textContent ?? (props.value?.toString() ?? ''),
  )

  const groupId = groupContext?.id
  if (groupId) {
    if (!allGroups.value.has(groupId)) {
      allGroups.value.set(groupId, new Set([id]))
    } else {
      allGroups.value.get(groupId)?.add(id)
    }
  }
})
onUnmounted(() => {
  allItems.value.delete(id)
})
</script>

<template>
  <ListboxItem
    v-if="isRender"
    v-bind="forwarded"
    :id="id"
    ref="itemRef"
    class="ds-command__item"
    data-test="ds-command-item"
    @select="
      () => {
        filterState.search = ''
      }
    "
  >
    <slot />
  </ListboxItem>
</template>

<style>
.ds-command__item {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--ds-space-xs);
  padding-inline: var(--ds-space-xs);
  padding-block: var(--ds-space-2xs);
  font-size: var(--ds-font-size-label);
  color: var(--ds-color-black);
  border-radius: var(--ds-radius-sm);
  outline: none;
  user-select: none;
  cursor: default;
}
.ds-command__item[data-highlighted] {
  background: var(--ds-color-accent-bg);
  color: var(--ds-color-accent);
}
.ds-command__item[data-disabled] {
  pointer-events: none;
  opacity: 0.5;
}
.ds-command__item > svg {
  flex: none;
  inline-size: 16px;
  block-size: 16px;
  pointer-events: none;
  color: var(--ds-color-text-grey);
}
</style>
