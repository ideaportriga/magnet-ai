<template lang="pug">
auth-login-page(
  v-if='auth.client',
  :auth-client='auth.client',
  :providers='providers',
  :signup-enabled='signupEnabled',
  :oidc-base-url='auth.baseUrl',
  :popup-width='auth.authConfig.popup?.width',
  :popup-height='auth.authConfig.popup?.height',
  @success='onSuccess',
  @navigate='onNavigate'
)
</template>

<script setup>
import { computed, defineAsyncComponent } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/pinia'

const AuthLoginPage = defineAsyncComponent(() => import('@ui/components/auth/AuthLoginPage.vue'))

const auth = useAuth()
const router = useRouter()

const providers = computed(() => auth.authConfig.providers || [])
const signupEnabled = computed(() => auth.authConfig.signupEnabled || false)

async function onSuccess() {
  await auth.getAuthData()
  router.push('/')
}

function onNavigate(page) {
  router.push(`/${page}`)
}
</script>
