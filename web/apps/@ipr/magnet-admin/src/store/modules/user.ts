import _ from 'lodash'
import { uid } from 'quasar'

const LOCAL_STORAGE_KEY = 'userInfo'

const state = () => ({
  userInfo: JSON.parse(localStorage.getItem(LOCAL_STORAGE_KEY) || '{}') || {},
})

const getters = {
  userInfo: (state) => {
    const storedUserInfo = localStorage.getItem(LOCAL_STORAGE_KEY)
    return storedUserInfo ? JSON.parse(storedUserInfo) : state.userInfo
  },
}

const mutations = {
  setUserInfo(state, userInfo) {
    console.log('setUserInfo', userInfo)
    state.userInfo = userInfo
    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(userInfo))
  },
  clearUserInfo(state) {
    state.userInfo = {}
    localStorage.removeItem(LOCAL_STORAGE_KEY)
  },
}

export default {
  state,
  getters,
  mutations,
}
