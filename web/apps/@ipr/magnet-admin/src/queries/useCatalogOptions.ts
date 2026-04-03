import { computed } from 'vue'
import { useCatalog, type CatalogItem } from './catalog'
import { queryClient } from '@/plugins/vueQuery'

/**
 * Composable for getting dropdown options from the catalog cache.
 *
 * Replaces the pattern of `queries.someEntity.useList()` + computed mapping
 * for simple dropdowns that only need name + system_name.
 */
export function useCatalogOptions(
  entityType: string,
  filter?: (item: CatalogItem) => boolean,
) {
  const { data: catalog, isLoading } = useCatalog()

  const options = computed(() => {
    const items = catalog.value?.filter((c) => c.entity_type === entityType) ?? []
    return filter ? items.filter(filter) : items
  })

  return { options, isLoading }
}

/**
 * Synchronous catalog access for config files and non-reactive contexts.
 *
 * Replaces getCachedItems() — reads from the catalog cache instead of
 * individual entity list caches.
 *
 * Returns an empty array if catalog is not yet cached.
 */
export function getCachedCatalog(entityType?: string): CatalogItem[] {
  const data = queryClient.getQueryData<CatalogItem[]>(['catalog'])
  if (!data) return []
  if (!entityType) return data
  return data.filter((c) => c.entity_type === entityType)
}
