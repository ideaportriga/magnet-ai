/**
 * Internal Command context — used by Command.vue, CommandGroup.vue,
 * CommandItem.vue, and CommandEmpty.vue to share filter / membership state.
 *
 * NOT exported from primitives/index.ts on purpose; this is component-internal.
 */
import type { Ref } from 'vue'
import { createContext } from 'reka-ui'

export const [useCommandContext, provideCommandContext] = createContext<{
  allItems: Ref<Map<string, string>>
  allGroups: Ref<Map<string, Set<string>>>
  filterState: {
    search: string
    filtered: { count: number; items: Map<string, number>; groups: Set<string> }
  }
}>('DsCommand')

export const [useCommandGroupContext, provideCommandGroupContext] = createContext<{
  id?: string
}>('DsCommandGroup')
