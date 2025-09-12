// store/modules/popup.js
export default {
  state: {
    showLeaveConfirm: false,
    message: '',
    nextRoute: null,
    isNavigationCancelled: false,
  },

  getters: {
    showLeaveConfirm: (state) => state.showLeaveConfirm,
    message: (state) => state.message,
    nextRoute: (state) => state.nextRoute,
    isNavigationCancelled: (state) => state.isNavigationCancelled,
  },
  mutations: {
    setIsNavigationCancelled(state, payload) {
      state.isNavigationCancelled = payload
    },
    showPopup(state, payload) {
      state.showLeaveConfirm = true
    },
    hidePopup(state) {
      state.showLeaveConfirm = false
      state.nextRoute = null
    },

    setNextRoute(state, route) {
      state.nextRoute = route
    },
    clearNextRoute(state) {
      state.nextRoute = null
    },
  },
}
