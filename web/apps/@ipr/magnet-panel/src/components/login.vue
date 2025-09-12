<template lang="pug">
.flex.flex-center.full-height
  .column.items-center.auth-container
    .row
      km-icon(:name='"magnet"', width='23', height='25')
      .km-heading-7.logo-text.q-ml-sm Magnet AI
    km-btn.q-mt-md(bg='primary', color='border', :label='loginButtonText', @click='login', :disable='loginInProgress')
</template>

<script setup>
import { useAuth } from '@/pinia'
import { computed, ref, defineEmits, onUnmounted } from 'vue'

const emit = defineEmits(['auth-completed'])

const auth = useAuth()

/* Window */
const loginWindow = ref()
const loginInProgress = ref(false)
const oAuthPopupWidth = computed(() => auth.authConfig.popup.width)
const oAuthPopupHeight = computed(() => auth.authConfig.popup.height)

const loginButtonText = computed(() => {
  return loginInProgress.value ? `Logging in with ${auth.authConfig.provider} ...` : `Log in with ${auth.authConfig.provider}`
})

const tokenReceived = ref(false)
let loginWindowClosedCheckInterval

async function receiveMessageFromPopup(event) {
  window.removeEventListener('message', receiveMessageFromPopup)

  tokenReceived.value = true

  const authorized = await auth.completeAuth(event.data)
  loginInProgress.value = false
  if (authorized) {
    emit('auth-completed')
  }
}
onUnmounted(() => {
  window.removeEventListener('message', receiveMessageFromPopup)
  clearInterval(loginWindowClosedCheckInterval)
})

function login() {
  if (!auth.baseUrl) {
    throw new Error('API base url not defined')
  }
  if (loginInProgress.value) {
    return
  }

  loginInProgress.value = true
  loginWindow.value = window.open(
    `${auth.baseUrl}/auth/login`,
    'popupLoginWithOAuthProvider',
    `width=${oAuthPopupWidth.value},height=${oAuthPopupHeight.value}`
  )

  window.addEventListener('message', receiveMessageFromPopup)

  loginWindowClosedCheckInterval = setInterval(() => {
    if (tokenReceived.value) {
      clearInterval(loginWindowClosedCheckInterval)
      return
    }

    if (loginWindow.value.closed) {
      loginInProgress.value = false
      clearInterval(loginWindowClosedCheckInterval)
      window.removeEventListener('message', receiveMessageFromPopup)
    }
  }, 500)

  //TODO ADD CHECK FOR WINDOW
}
</script>
