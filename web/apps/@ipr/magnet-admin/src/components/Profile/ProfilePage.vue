<template>
  <layouts-details-layout no-header>
    <template #content>
      <km-tabs v-model="tab">
        <km-tab name="profile" :label="m.user_profile()" />
        <km-tab name="access" :label="m.common_access()" />
        <km-tab name="security" :label="m.user_security()" />
      </km-tabs>
      <div class="stack full-height full-width overflow-auto mb-md mt-lg" data-gap="lg" style="min-block-size: 0">
        <div class="cluster full-height full-width" data-gap="lg">
          <div class="flex-1 full-height full-width">
            <div class="stack items-center full-height full-width overflow-auto" data-gap="lg">
              <div class="flex-none full-width">
                <template v-if="tab === &quot;profile&quot;">
                  <km-section :title="m.section_account()" :sub-title="m.subtitle_yourAccount()">
                    <div class="cluster gap-lg">
                      <div class="flex-1">
                        <div class="km-input-label">{{ m.common_name() }}</div>
                        <km-input :model-value="editName" :placeholder="m.profile_yourName()" @input="editName = $event" />
                      </div>
                      <div class="flex-1">
                        <div class="km-input-label">{{ m.auth_email() }}</div>
                        <km-input :model-value="displayEmail" readonly />
                      </div>
                    </div>
                    <div class="mt-md">
                      <div class="km-input-label">{{ m.user_lastLogin() }}</div>
                      <div class="km-description mt-xs">{{ userInfo?.last_login_at ? new Date(userInfo.last_login_at).toLocaleString() : m.user_na() }}</div>
                    </div>
                  </km-section>
                  <km-separator class="my-lg" />
                  <km-section :title="m.section_linkedAccounts()" :sub-title="m.subtitle_linkedIdentityProviders()">
                    <template v-if="oauthAccounts.length">
                      <div class="stack" data-gap="sm" style="max-inline-size: 400px">
                        <div v-for="account in oauthAccounts" :key="account.provider" class="cluster p-sm pl-md ba-border border-radius-8" data-wrap="no">
                          <km-glyph class="mr-sm" name="check" size="16px" tone="success" />
                          <div class="km-title mr-md">{{ providerLabel(account.provider) }}</div>
                          <div v-if="account.email" class="km-description text-grey">{{ account.email }}</div>
                        </div>
                      </div>
                    </template>
                    <div v-else class="km-description text-grey">{{ m.user_noLinkedAccounts() }}</div>
                  </km-section>
                </template>
                <template v-if="tab === &quot;access&quot;">
                  <km-section :title="m.section_roles()" :sub-title="m.subtitle_yourRoles()">
                    <div class="stack" data-gap="sm" style="max-inline-size: 400px">
                      <div v-for="role in roles" :key="role" class="cluster p-sm pl-md ba-border border-radius-8" data-wrap="no">
                        <km-glyph class="mr-sm" name="shield-check" size="16px" tone="brand" />
                        <div class="km-title">{{ role }}</div>
                      </div>
                      <div v-if="!roles.length" class="km-description text-grey">No roles assigned</div>
                    </div>
                  </km-section>
                  <km-separator class="my-lg" />
                  <km-section :title="m.section_groups()" :sub-title="m.subtitle_groups()">
                    <div class="km-description text-grey">No groups assigned</div>
                    <div class="km-description text-grey mt-sm">Group management is available for administrators.</div>
                  </km-section>
                </template>
                <template v-if="tab === &quot;security&quot;">
                  <km-section :title="m.section_twoFactorAuth()" :sub-title="m.subtitle_addSecurityLayer()">
                    <div class="cluster" data-gap="sm">
                      <div class="km-description">{{ m.common_status() }}:</div>
                      <km-chip :tone="userInfo?.is_two_factor_enabled ? &quot;success&quot; : &quot;neutral&quot;" size="sm">{{ userInfo?.is_two_factor_enabled ? m.common_enabled() : m.common_disabled() }}</km-chip>
                    </div>
                  </km-section>
                  <km-separator class="my-lg" />
                  <km-section :title="m.section_activeSessions()" :sub-title="m.subtitle_activeDevices()">
                    <div v-if="sessions.length &gt; 1" class="cluster mb-sm" data-justify="end">
                      <km-btn flat :label="m.user_revokeAllOthers()" size="sm" @click="revokeAllSessions" />
                    </div>
                    <div class="stack" data-gap="sm">
                      <div v-for="session in sessions" :key="session.id" class="cluster p-md ba-border border-radius-8" data-justify="between">
                        <div class="stack">
                          <div class="km-title">{{ session.device_info || m.user_unknownDevice() }}</div>
                          <div class="km-description text-grey">{{ m.user_since({ date: new Date(session.created_at).toLocaleString() }) }}</div>
                        </div>
                        <km-btn flat :label="m.user_revoke()" size="sm" @click="revokeSession(session.id)" />
                      </div>
                      <div v-if="!sessions.length" class="km-description text-grey">{{ m.user_noActiveSessions() }}</div>
                    </div>
                  </km-section>
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </layouts-details-layout>
</template>

<script>
import { computed, ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuth } from '@shared'
import { useSharedAuthStore } from '@shared/stores/authStore'
import { m } from '@/paraglide/messages'

export default {
  setup() {
    const authStore = useSharedAuthStore()
    const route = useRoute()
    const auth = useAuth()
    const userInfo = computed(() => authStore.userInfo)
    const validTabs = ['profile', 'access', 'security']
    const tab = ref(validTabs.includes(route.params?.tab) ? route.params.tab : 'profile')
    const editName = ref(userInfo.value?.name || '')
    const sessions = ref([])

    const displayEmail = computed(() =>
      userInfo.value?.email || userInfo.value?.preferred_username || ''
    )

    const oauthAccounts = computed(() =>
      userInfo.value?.oauth_accounts || []
    )

    const roles = computed(() =>
      userInfo.value?.roles || []
    )

    onMounted(async () => {
      if (auth.client.value) {
        try {
          sessions.value = await auth.client.value.getSessions()
        } catch (e) {
          // ignore
        }
      }
    })

    return { m, userInfo, tab, editName, displayEmail, oauthAccounts, roles, sessions, auth }
  },
  methods: {
    providerLabel(provider) {
      const labels = { microsoft: 'Microsoft', google: 'Google', github: 'GitHub', oracle: 'Oracle' }
      return labels[provider] || provider
    },
    async revokeSession(id) {
      if (!this.auth.client.value) return
      await this.auth.client.value.revokeSession(id)
      this.sessions = await this.auth.client.value.getSessions()
    },
    async revokeAllSessions() {
      if (!this.auth.client.value) return
      await this.auth.client.value.revokeAllSessions()
      this.sessions = await this.auth.client.value.getSessions()
    },
  },
}
</script>
