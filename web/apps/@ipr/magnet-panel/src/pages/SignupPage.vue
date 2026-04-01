<template lang="pug">
auth-signup-page(
  v-if='auth.client',
  :auth-client='auth.client',
  @success='onSuccess',
  @navigate='onNavigate'
)
</template>

<script setup>
import { defineAsyncComponent } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/pinia'

const AuthSignupPage = defineAsyncComponent(() => import('@ui/components/auth/AuthSignupPage.vue'))

const auth = useAuth()
const router = useRouter()

function onSuccess() {
  router.push('/login')
}

function onNavigate(page) {
  router.push(`/${page}`)
}
</script>
