import { queryClient } from '@/plugins/vueQuery'
import { entityKeys } from './queryKeys'

type EntityName = keyof typeof entityKeys

/**
 * Get cached list items for an entity from the TanStack Query cache.
 * Safe to call outside Vue component setup (e.g. in config files, plain JS modules).
 * Returns the items array or an empty array if not yet cached.
 *
 * NOTE: Most usages have been migrated to getCachedCatalog() from useCatalogOptions.ts.
 * Remaining usages need fields not available in catalog (display_name, label, pricing, tools).
 * TODO: Remove when backend adds display_name/type/category to /catalog endpoint.
 */
export function getCachedItems(entity: EntityName): any[] {
  const keys = entityKeys[entity]
  // Try to find any cached list query for this entity
  const queries = queryClient.getQueriesData({ queryKey: keys.lists() })
  for (const [, data] of queries) {
    if (data && typeof data === 'object' && 'items' in (data as any)) {
      return (data as any).items ?? []
    }
  }
  return []
}
