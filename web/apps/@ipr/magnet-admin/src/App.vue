<template lang="pug">
.full-height.full-width(:key='locale', :class='{ "no-wrap column": $route.query.viewMode === "panel" || ai_app }')
  //- Show spinner during initial config load or auth check
  template(v-if='initialLoading || authCheckInProgress')
    .flex.flex-center.full-height
      q-spinner(size='30px', color='primary')
  template(v-else-if='authRequired')
      auth-signup-page(
        v-if='authPage === "signup"',
        :auth-client='authClient',
        @navigate='authPage = $event'
      )
      auth-forgot-password(
        v-else-if='authPage === "forgot-password"',
        :auth-client='authClient',
        @navigate='authPage = $event'
      )
      auth-login-page(
        v-else,
        :auth-client='authClient',
        :providers='authProviders',
        :signup-enabled='signupEnabled',
        @success='onAuthCompleted',
        @navigate='authPage = $event'
      )
  template(v-else-if='!hasAdminAccess')
    .flex.flex-center.full-height
      .column.items-center.q-pa-xl(style='max-width: 480px')
        q-icon(name='fas fa-lock', size='48px', color='grey-5')
        .text-h6.q-mt-md.text-center {{ m.access_restricted() }}
        .text-body2.text-grey.q-mt-sm.text-center
          | {{ m.access_noPermissions() }}
          |  {{ m.access_contactAdmin() }}
        .text-caption.text-grey.q-mt-md {{ m.access_loggedInAs({ name: userDisplayName }) }}
        q-btn.q-mt-lg(
          outline,
          color='primary',
          :label='m.auth_logout()',
          no-caps,
          @click='handleLogout'
        )
  template(v-else)
    layout-default
  km-error-dialog(v-if='appStore.errorMessage')
  //- §D.3 — dev-only debug strip; `env` string was brittle (depends on a
  //- globalProperty). Vite's import.meta.env.DEV is statically tree-shaken.
  template(v-if='isDev')
    .fixed-bottom-right.q-pa-sm.row(:style='{ zIndex: "var(--km-z-base)" }')
</template>

<script>
import { useState } from '@shared'
import { useAuth } from '@shared'
import { getCurrentInstance, computed, ref } from 'vue'
import { m } from '@/paraglide/messages'
import { useLocale } from '@shared/i18n'
import { useAppStore } from '@/stores/appStore'
import { useSharedAuthStore } from '@shared/stores/authStore'
import { queryClient } from '@/plugins/vueQuery'
import { entityKeys } from '@/queries/queryKeys'
import { getEntityApis, getApiClient } from '@/api/entityApis'
import { initializePlugins } from '@/config/collections/collections'
import AuthLoginPage from '@ui/components/auth/AuthLoginPage.vue'
import AuthSignupPage from '@ui/components/auth/AuthSignupPage.vue'
import AuthForgotPassword from '@ui/components/auth/AuthForgotPassword.vue'

export default {
  components: { AuthLoginPage, AuthSignupPage, AuthForgotPassword },
  setup() {
    const loading = useState('globalLoading')
    const auth = useAuth()
    const appStore = useAppStore()
    const { appContext } = getCurrentInstance()

    // useAuth stores userInfo in sharedAuthStore — read from there
    const sharedAuth = useSharedAuthStore()

    const initialLoading = ref(true)
    const authPage = ref('login')

    const authClient = computed(() => auth.client.value)
    const authProviders = ref([])

    async function loadProviders() {
      if (authClient.value) {
        try {
          const list = await authClient.value.getProviders()
          authProviders.value = list
        } catch { /* providers endpoint unavailable — hide SSO buttons */ }
      }
    }

    const hasAdminAccess = computed(() => {
      const userInfo = sharedAuth.userInfo
      if (!userInfo) return false
      const roles = userInfo.roles || []
      return roles.includes('admin')
    })
    const userDisplayName = computed(() => {
      const u = sharedAuth.userInfo
      return u?.name || u?.email || u?.preferred_username || ''
    })

    async function handleLogout() {
      await auth.logout()
    }
    const signupEnabled = computed(() => appStore.config?.auth?.signupEnabled || false)

    const { locale } = useLocale()

    const isDev = import.meta.env.DEV

    return {
      m,
      locale,
      initialLoading,
      authPage,
      authClient,
      loadProviders,
      hasAdminAccess,
      userDisplayName,
      handleLogout,
      authProviders,
      signupEnabled,
      loading,
      appContext,
      appStore,
      sharedAuth,
      isDev,
      ...auth,
    }
  },
  computed: {
    ai_app() {
      return this.$route.query.ai_app || window?.magnetai_ai_app
    },
    openTest() {
      return true
    },
    theme() {
      return this.appContext.config.globalProperties.$theme ?? 'default'
    },
  },
  watch: {
    loading: {
      immediate: true,
      handler(val) {
        if (val) {
          this.$q.loading.show()
        } else {
          this.$q.loading.hide()
        }
      },
    },
  },
  async created() {
    // Config is loaded by initNewStack (Pinia appStore.loadConfig) in main.js

    // Check if user already has a valid session (cookie)
    if (this.authEnabled) {
      await this.getAuthData()
      await this.loadProviders()
    }

    this.initialLoading = false

    if (!this.authRequired && this.hasAdminAccess) {
      await this.loadData()
    }
  },

  methods: {
    async loadData() {
      const apis = getEntityApis()
      const client = getApiClient()

      // Prefetch plugins first (needed for dynamic forms)
      await queryClient.fetchQuery({
        queryKey: entityKeys.plugins.list({}),
        queryFn: () => apis.plugins.list(),
      })

      // Initialize plugins configuration for collections (uses data from cache)
      initializePlugins()

      // Prefetch catalog (lightweight list of all entities for dropdowns, filters, tab names)
      await queryClient.fetchQuery({
        queryKey: ['catalog'],
        queryFn: () => client.get('catalog'),
        staleTime: 5 * 60 * 1000,
      })
    },
    async onAuthCompleted() {
      await this.getAuthData()
      if (this.hasAdminAccess) {
        await this.loadData()
      }
    },
  },
}
</script>
