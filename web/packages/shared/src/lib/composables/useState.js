import { computed } from 'vue'
import store from '@/store/index'

//useState
export default function useState(propertyName) {
  const flag = computed({
    get() {
      return store.getters[propertyName]
    },
    set(value) {
      store.commit('set', { [propertyName]: value })
    },
  })

  return flag
}
