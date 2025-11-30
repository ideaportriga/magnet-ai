import { computed } from 'vue'

export function useParentRoute(route) {
  return computed(() => {
    if (!route?.path) return 'default'
    const pathSegments = route.path.split('/').filter(Boolean)
    return pathSegments.length > 0 ? pathSegments[0] : 'default'
  })
}
