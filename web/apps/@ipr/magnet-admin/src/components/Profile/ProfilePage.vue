<template lang="pug">
layouts-details-layout(noHeader)
  template(#content)
    km-tabs(v-model='tab')
      q-tab(name='profile', :label='m.user_profile()')
      q-tab(name='access', label='Access')
      q-tab(name='security', :label='m.user_security()')
    .column.no-wrap.q-gap-16.full-height.full-width.overflow-auto.q-mb-md.q-mt-lg(style='min-height: 0')
      .row.q-gap-16.full-height.full-width
        .col.full-height.full-width
          .column.items-center.full-height.full-width.q-gap-16.overflow-auto
            .col-auto.full-width
              template(v-if='tab === "profile"')
                km-section(:title='m.section_account()', :subTitle='m.subtitle_yourAccount()')
                  .row.q-gap-16
                    .col
                      .km-input-label {{ m.common_name() }}
                      km-input(:modelValue='editName', @input='editName = $event', placeholder='Your name')
                    .col
                      .km-input-label {{ m.auth_email() }}
                      km-input(:modelValue='displayEmail', readonly)
                  .q-mt-md
                    .km-input-label {{ m.user_lastLogin() }}
                    .km-description.q-mt-xs {{ userInfo?.last_login_at ? new Date(userInfo.last_login_at).toLocaleString() : m.user_na() }}

                q-separator.q-my-lg

                km-section(:title='m.section_linkedAccounts()', :subTitle='m.subtitle_linkedIdentityProviders()')
                  template(v-if='oauthAccounts.length')
                    .column.q-gap-sm(style='max-width: 400px')
                      .row.items-center.no-wrap.q-pa-sm.q-pl-md.ba-border.border-radius-8(v-for='account in oauthAccounts', :key='account.provider')
                        q-icon.q-mr-sm(name='fas fa-check-circle', size='16px', color='positive')
                        .km-title.q-mr-md {{ providerLabel(account.provider) }}
                        .km-description.text-grey(v-if='account.email') {{ account.email }}
                  .km-description.text-grey(v-else) {{ m.user_noLinkedAccounts() }}

              template(v-if='tab === "access"')
                km-section(:title='m.section_roles()', :subTitle='m.subtitle_yourRoles()')
                  .column.q-gap-sm(style='max-width: 400px')
                    .row.items-center.no-wrap.q-pa-sm.q-pl-md.ba-border.border-radius-8(v-for='role in roles', :key='role')
                      q-icon.q-mr-sm(name='fas fa-shield-alt', size='16px', color='primary')
                      .km-title {{ role }}
                    .km-description.text-grey(v-if='!roles.length') No roles assigned

                q-separator.q-my-lg

                km-section(:title='m.section_groups()', :subTitle='m.subtitle_groups()')
                  .km-description.text-grey No groups assigned
                  .km-description.text-grey.q-mt-sm Group management is available for administrators.

              template(v-if='tab === "security"')
                km-section(:title='m.section_twoFactorAuth()', :subTitle='m.subtitle_addSecurityLayer()')
                  .row.items-center.q-gap-sm
                    .km-description {{ m.common_status() }}:
                    q-chip(
                      :color='userInfo?.is_two_factor_enabled ? "positive" : "grey-4"',
                      :text-color='userInfo?.is_two_factor_enabled ? "white" : "dark"',
                      size='sm'
                    ) {{ userInfo?.is_two_factor_enabled ? m.common_enabled() : m.common_disabled() }}

                q-separator.q-my-lg

                km-section(:title='m.section_activeSessions()', :subTitle='m.subtitle_activeDevices()')
                  .row.items-center.justify-end.q-mb-sm(v-if='sessions.length > 1')
                    km-btn(flat, :label='m.user_revokeAllOthers()', size='sm', @click='revokeAllSessions')
                  .column.q-gap-sm
                    .row.items-center.justify-between.q-pa-md.ba-border.border-radius-8(v-for='session in sessions', :key='session.id')
                      .column
                        .km-title {{ session.device_info || m.user_unknownDevice() }}
                        .km-description.text-grey {{ m.user_since({ date: new Date(session.created_at).toLocaleString() }) }}
                      km-btn(flat, :label='m.user_revoke()', size='sm', @click='revokeSession(session.id)')
                    .km-description.text-grey(v-if='!sessions.length') {{ m.user_noActiveSessions() }}
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
