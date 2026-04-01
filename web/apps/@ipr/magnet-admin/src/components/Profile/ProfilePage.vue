<template lang="pug">
layouts-details-layout(noHeader)
  template(#content)
    km-tabs(v-model='tab')
      q-tab(name='profile', label='Profile')
      q-tab(name='access', label='Access')
      q-tab(name='security', label='Security')
    .column.no-wrap.q-gap-16.full-height.full-width.overflow-auto.q-mb-md.q-mt-lg(style='min-height: 0')
      .row.q-gap-16.full-height.full-width
        .col.full-height.full-width
          .column.items-center.full-height.full-width.q-gap-16.overflow-auto
            .col-auto.full-width
              template(v-if='tab === "profile"')
                km-section(title='Account', subTitle='Your account information')
                  .row.q-gap-16
                    .col
                      .km-input-label Name
                      km-input(:modelValue='editName', @input='editName = $event', placeholder='Your name')
                    .col
                      .km-input-label Email
                      km-input(:modelValue='displayEmail', readonly)
                  .q-mt-md
                    .km-input-label Last login
                    .km-description.q-mt-xs {{ userInfo?.last_login_at ? new Date(userInfo.last_login_at).toLocaleString() : 'N/A' }}

                q-separator.q-my-lg

                km-section(title='Linked accounts', subTitle='External identity providers connected to your account')
                  template(v-if='oauthAccounts.length')
                    .column.q-gap-sm(style='max-width: 400px')
                      .row.items-center.no-wrap.q-pa-sm.q-pl-md.ba-border.border-radius-8(v-for='account in oauthAccounts', :key='account.provider')
                        q-icon.q-mr-sm(name='fas fa-check-circle', size='16px', color='positive')
                        .km-title.q-mr-md {{ providerLabel(account.provider) }}
                        .km-description.text-grey(v-if='account.email') {{ account.email }}
                  .km-description.text-grey(v-else) No linked accounts

              template(v-if='tab === "access"')
                km-section(title='Roles', subTitle='Your assigned roles determine what you can access')
                  .column.q-gap-sm(style='max-width: 400px')
                    .row.items-center.no-wrap.q-pa-sm.q-pl-md.ba-border.border-radius-8(v-for='role in roles', :key='role')
                      q-icon.q-mr-sm(name='fas fa-shield-alt', size='16px', color='primary')
                      .km-title {{ role }}
                    .km-description.text-grey(v-if='!roles.length') No roles assigned

                q-separator.q-my-lg

                km-section(title='Groups', subTitle='Groups you belong to')
                  .km-description.text-grey No groups assigned
                  .km-description.text-grey.q-mt-sm Group management is available for administrators.

              template(v-if='tab === "security"')
                km-section(title='Two-Factor Authentication', subTitle='Add an extra layer of security to your account')
                  .row.items-center.q-gap-sm
                    .km-description Status:
                    q-chip(
                      :color='userInfo?.is_two_factor_enabled ? "positive" : "grey-4"',
                      :text-color='userInfo?.is_two_factor_enabled ? "white" : "dark"',
                      size='sm'
                    ) {{ userInfo?.is_two_factor_enabled ? 'Enabled' : 'Disabled' }}

                q-separator.q-my-lg

                km-section(title='Active Sessions', subTitle='Devices currently logged into your account')
                  .row.items-center.justify-end.q-mb-sm(v-if='sessions.length > 1')
                    km-btn(flat, label='Revoke all others', size='sm', @click='revokeAllSessions')
                  .column.q-gap-sm
                    .row.items-center.justify-between.q-pa-md.ba-border.border-radius-8(v-for='session in sessions', :key='session.id')
                      .column
                        .km-title {{ session.device_info || 'Unknown device' }}
                        .km-description.text-grey Since {{ new Date(session.created_at).toLocaleString() }}
                      km-btn(flat, label='Revoke', size='sm', @click='revokeSession(session.id)')
                    .km-description.text-grey(v-if='!sessions.length') No active sessions
</template>

<script>
import { computed, ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuth } from '@shared'
import { useSharedAuthStore } from '@shared/stores/authStore'

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

    return { userInfo, tab, editName, displayEmail, oauthAccounts, roles, sessions, auth }
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
