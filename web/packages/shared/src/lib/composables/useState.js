import { computed } from 'vue'
import { useSharedAuthStore } from '../stores/authStore'

/**
 * Reactive getter/setter for shared app state.
 * Previously backed by Vuex; now uses Pinia sharedAuthStore.
 */
export default function useState(propertyName) {
  const store = useSharedAuthStore()

  const flag = computed({
    get() {
      return store[propertyName]
    },
    set(value) {
      store[propertyName] = value
    },
  })

  return flag
}
