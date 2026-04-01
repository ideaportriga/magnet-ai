import { DateTime } from 'luxon'
// import tableColumns from '@/config/tableColumns.js'
import { formatDate, hasProps, sortAlphabetically } from '@shared'
import { isEmpty, isObject, cloneDeep } from 'lodash'
import { useSharedAuthStore } from '../stores/authStore'

const setGlobalLoading = function (globalLoading) {
  try {
    const store = useSharedAuthStore()
    store.globalLoading = globalLoading
  } catch {
    // Store not initialized yet
  }
}

const setGlobalErrorMessage = function (text, technicalError) {
  try {
    const store = useSharedAuthStore()
    store.errorMessage = { text, technicalError }
    store.globalLoading = false
  } catch {
    // Store not initialized yet
  }
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
