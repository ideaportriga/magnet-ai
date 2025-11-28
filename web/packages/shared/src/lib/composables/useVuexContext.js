import { computed } from 'vue'
import { useStore } from 'vuex'

function useVuexContext(entity) {
  //namespce is passed through bind function
  // eslint-disable-next-line @typescript-eslint/no-this-alias
  const namespace = this
  const store = useStore()
  // getting module getters and actions
  const getters = store.getters[namespace][entity]
  const actions = Object.keys(store._actions)
    .filter((actionKey) => actionKey.startsWith(`${namespace}/`))
    .map((actionKey) => actionKey.replace(`${namespace}/`, ''))
  // Helper function for dispatching/commiting actions with the provided entity
  const dispatch = (name, payload) => store.dispatch(`${namespace}/${name}`, { payload, entity })
  const commit = (name, payload) => store.commit(`${namespace}/${name}`, { payload, entity })

  // Helper function for accessing and setting local state properties
  const uselocalState = (propName) => {
    const flag = computed({
      get() {
        return store.getters?.[namespace]?.[entity]?.[propName]
      },
      set(value) {
        commit('set', { [propName]: value })
      },
    })
    return flag
  }
  return {
    // Getters
    ...Object.fromEntries(Object.keys(getters).map((key) => [[key], uselocalState(key)])),
    // Dispatch functions
    ...Object.fromEntries(actions.map((key) => [[key], (payload) => dispatch(key, payload)])),
  }
}

export default useVuexContext
