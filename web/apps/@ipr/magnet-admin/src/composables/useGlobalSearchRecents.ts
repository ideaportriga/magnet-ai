/**
 * Tracks recently selected entries from the cmd+K global search popup so
 * the popup can show a "recent" list before the user starts typing.
 *
 * Persisted to localStorage. Each entry stores the minimum needed to look
 * the item back up against the catalog (entity_type + id) — full item data
 * comes from `useCatalog()` at render time so we never display a stale
 * name/description.
 */

import { ref, watch } from 'vue'

export interface GlobalSearchRecent {
  id: string
  entity_type: string
}

const STORAGE_KEY = 'magnet.globalSearch.recents'
const MAX_RECENTS = 20

function load(): GlobalSearchRecent[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    return parsed.filter(
      (r): r is GlobalSearchRecent =>
        r && typeof r.id === 'string' && typeof r.entity_type === 'string',
    )
  } catch {
    return []
  }
}

const recents = ref<GlobalSearchRecent[]>(load())

watch(
  recents,
  (next) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
    } catch {
      // localStorage full / disabled — silently drop
    }
  },
  { deep: true },
)

export function useGlobalSearchRecents() {
  function record(item: GlobalSearchRecent) {
    const filtered = recents.value.filter(
      (r) => !(r.id === item.id && r.entity_type === item.entity_type),
    )
    recents.value = [item, ...filtered].slice(0, MAX_RECENTS)
  }

  function clear() {
    recents.value = []
  }

  return { recents, record, clear }
}
