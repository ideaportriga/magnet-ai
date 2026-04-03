<template lang="pug">
user-security-page(
  :user-info='userInfo',
  :sessions='sessions',
  @setup-mfa='handleSetupMfa',
  @disable-mfa='handleDisableMfa',
  @revoke-session='handleRevokeSession',
  @revoke-all-sessions='handleRevokeAllSessions'
)
</template>

<script>
import { computed, ref, onMounted } from 'vue'
import { m } from '@/paraglide/messages'
import { useAuth } from '@shared'
import UserSecurityPage from '@ui/components/user/UserSecurityPage.vue'
import { useSharedAuthStore } from '@shared/stores/authStore'

export default {
  components: { UserSecurityPage },
  setup() {
    const authStore = useSharedAuthStore()
    const auth = useAuth()
    const userInfo = computed(() => authStore.userInfo)
    const sessions = ref([])

    onMounted(async () => {
      if (auth.client.value) {
        sessions.value = await auth.client.value.getSessions()
      }
    })

    return { userInfo, sessions, auth }
  },
  methods: {
    handleSetupMfa() {

    },
    async handleDisableMfa() {
      if (!this.auth.client.value) return
      try {
        await this.auth.client.value.disableMfa()
        await this.auth.getAuthData()
      } catch (e) {

      }
    },
    async handleRevokeSession(id) {
      if (!this.auth.client.value) return
      await this.auth.client.value.revokeSession(id)
      this.sessions = await this.auth.client.value.getSessions()
    },
    async handleRevokeAllSessions() {
      if (!this.auth.client.value) return
      await this.auth.client.value.revokeAllSessions()
      this.sessions = await this.auth.client.value.getSessions()
    },
  },
}
</script>
