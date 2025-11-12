const state = () => ({
  items: {},
  controls: {},
  methods: {},
  n19: {},
  allItems: {},
  paginationInfo: {},
  user: {},
})

const getters = {
  n19: (state) => state.n19,
  items: (state) => state.items,
  controls: (state) => state.controls,
  methods: (state) => state.methods,
  allItems: (state) => state.allItems,
  controlOptions: (state) => (entity, controlName) => {
    return state.controls[entity][controlName]?.options
  },
  paginationInfo: (state) => state.paginationInfo,
  user: (state) => state.user,
}

const mutations = {
  set(state, payload) {
    Object.entries(payload).forEach(([key, value]) => {
      state[key] = value
    })
  },

  // Set Nested
  setNested(state, { key, prop, val }) {
    state[key][prop] = val
  },

  removeNested(state, { key, index }) {
    delete state[key][index]
  },

  // Set Record field
  setRecord(state, { entity, key, record }) {
    state.items[entity][key] = record
  },

  // Set Record prop
  setRecordProp(state, { entity, key, prop, val }) {
    state.items[entity][key][prop] = val
    // state.controls[entity][prop]['value'] = val
  },
}

const actions = {}

export default {
  state: state(),
  getters: { ...getters },
  mutations,
  actions,
}
