import { DateTime } from 'luxon'
// import tableColumns from '@/config/tableColumns.js'
import { formatDate, hasProps, sortAlphabetically } from '@shared'
import { isEmpty, isObject, cloneDeep } from 'lodash'
import store from '@/store/index'

const setGlobalLoading = function (globalLoading) {
  store.commit('set', { globalLoading })
}

const setGlobalErrorMessage = function (text, technicalError) {
  const errorMessage = { text, technicalError }
  store.commit('set', { errorMessage, globalLoading: false, lockUI: false })
}

export const globalProperties = {
  dt: {
    value: DateTime,
  },
  formatDate: {
    value: formatDate,
  },
  env: {
    value: import.meta.env.MODE,
  },
  isSiebel: {
    value: 'SiebelApp' in window,
  },
  hasProps: {
    value: hasProps,
  },
  isEmpty: {
    value: isEmpty,
  },
  isObject: {
    value: isObject,
  },
  cloneDeep: {
    value: cloneDeep,
  },
  sortAlphabetically: {
    value: sortAlphabetically,
  },
  setGlobalLoading: {
    value: setGlobalLoading,
  },
  setGlobalErrorMessage: {
    value: setGlobalErrorMessage,
  },
}
