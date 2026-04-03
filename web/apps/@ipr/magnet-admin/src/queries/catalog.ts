import { useQuery } from '@tanstack/vue-query'
import { getApiClient } from '@/api'
import Fuse from 'fuse.js'

export interface CatalogItem {
  id: string
  name: string
  system_name: string
  description: string | null
  entity_type: string
  entity_label: string
  updated_at: string | null
  display_name?: string | null
  type?: string | null
  category?: string | null
  parent_system_name?: string | null
}

export function useCatalog() {
  const client = getApiClient()
  return useQuery<CatalogItem[]>({
    queryKey: ['catalog'],
    queryFn: () => client.get<CatalogItem[]>('catalog'),
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
    refetchOnWindowFocus: false,
  })
}

let _fuse: Fuse<CatalogItem> | null = null
let _fuseItems: CatalogItem[] | null = null

function getFuse(items: CatalogItem[]): Fuse<CatalogItem> {
  if (_fuse && _fuseItems === items) return _fuse
  _fuse = new Fuse(items, {
    keys: [
      { name: 'name', weight: 3 },
      { name: 'system_name', weight: 2 },
      { name: 'description', weight: 1 },
    ],
    threshold: 0.35,
    ignoreLocation: true,
    minMatchCharLength: 2,
  })
  _fuseItems = items
  return _fuse
}

export function filterCatalog(items: CatalogItem[], query: string): CatalogItem[] {
  const q = query.trim()
  if (!q) return items.slice(0, 50)
  const fuse = getFuse(items)
  return fuse.search(q, { limit: 50 }).map((r) => r.item)
}
