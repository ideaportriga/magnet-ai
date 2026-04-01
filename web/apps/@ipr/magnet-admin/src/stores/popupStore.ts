import { defineStore } from 'pinia'
import { ref } from 'vue'

export const usePopupStore = defineStore('popup', () => {
  const showLeaveConfirm = ref(false)
  const message = ref('')
  const nextRoute = ref<any>(null)
  const isNavigationCancelled = ref(false)

  function showPopup() {
    showLeaveConfirm.value = true
  }

  function hidePopup() {
    showLeaveConfirm.value = false
    nextRoute.value = null
  }

  function setNextRoute(route: any) {
    nextRoute.value = route
  }

  function clearNextRoute() {
    nextRoute.value = null
  }

  function setIsNavigationCancelled(value: boolean) {
    isNavigationCancelled.value = value
  }

  return {
    // state
    showLeaveConfirm,
    message,
    nextRoute,
    isNavigationCancelled,
    // actions
    showPopup,
    hidePopup,
    setNextRoute,
    clearNextRoute,
    setIsNavigationCancelled,
  }
})
