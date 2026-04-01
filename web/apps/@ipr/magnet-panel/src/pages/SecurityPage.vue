<template lang="pug">
user-security-page(
  :user-info='auth.userInfo',
  :sessions='sessions',
  @setup-mfa='handleSetupMfa',
  @disable-mfa='handleDisableMfa',
  @revoke-session='handleRevokeSession',
  @revoke-all-sessions='handleRevokeAllSessions'
)
</template>

<script setup>
import { ref, onMounted, defineAsyncComponent } from 'vue'
import { useAuth } from '@/pinia'

const UserSecurityPage = defineAsyncComponent(() => import('@ui/components/user/UserSecurityPage.vue'))

const auth = useAuth()
const sessions = ref([])

onMounted(async () => {
  if (auth.client) {
    sessions.value = await auth.client.getSessions()
  }
})

async function handleSetupMfa() {
  console.log('Setup MFA')
}

async function handleDisableMfa() {
  if (!auth.client) return
  try {
    await auth.client.disableMfa()
    await auth.getAuthData()
  } catch (e) {
    console.error('Failed to disable MFA:', e)
  }
}

async function handleRevokeSession(id) {
  if (!auth.client) return
  await auth.client.revokeSession(id)
  sessions.value = await auth.client.getSessions()
}

async function handleRevokeAllSessions() {
  if (!auth.client) return
  await auth.client.revokeAllSessions()
  sessions.value = await auth.client.getSessions()
}
</script>
