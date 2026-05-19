<template>
  <div :key="locale" class="full-height full-width" :class="{ &quot;stack&quot;: $route.query.viewMode === &quot;panel&quot; || ai_app }" :data-gap="($route.query.viewMode === &quot;panel&quot; || ai_app) ? '0' : undefined">
    <template v-if="initialLoading || authCheckInProgress">
      <div class="flex flex-center full-height">
        <km-loader size="30px" />
      </div>
    </template>
    <template v-else-if="authRequired">
      <auth-signup-page v-if="authPage === &quot;signup&quot;" :auth-client="authClient" @navigate="authPage = $event" />
      <auth-forgot-password v-else-if="authPage === &quot;forgot-password&quot;" :auth-client="authClient" @navigate="authPage = $event" />
      <auth-login-page v-else :auth-client="authClient" :providers="authProviders" :signup-enabled="signupEnabled" @success="onAuthCompleted" @navigate="authPage = $event" />
    </template>
    <template v-else-if="!hasAdminAccess">
      <div class="flex flex-center full-height">
        <div class="stack items-center p-xl" data-gap="0" style="max-inline-size: 480px">
          <km-glyph name="lock" size="48px" tone="muted" />
          <div class="text-h6 mt-md text-center">{{ m.access_restricted() }}</div>
          <div class="text-body2 text-grey mt-sm text-center">
            {{ m.access_noPermissions() }}
            {{ m.access_contactAdmin() }}
          </div>
          <div class="text-caption text-grey mt-md">{{ m.access_loggedInAs({ name: userDisplayName }) }}</div>
          <km-btn class="mt-lg" outline tone="brand" :label="m.auth_logout()" no-caps @click="handleLogout" />
        </div>
      </div>
    </template>
    <template v-else>
      <layout-default />
    </template>
    <km-error-dialog v-if="appStore.errorMessage" />
    <template v-if="isDev">
      <div class="fixed-bottom-right p-sm cluster" :style="{ zIndex: 'var(--ds-z-raised)' }" />
    </template>
    <ds-toast-host />
    <ds-dialog-host />
    <ds-loading-host />
  </div>
</template>

<script>
import { useState } from '@shared'
import { useAuth, usePermissions } from '@shared'
import { getCurrentInstance, computed, ref } from 'vue'
import { useLoading } from '@ds/composables/useLoading'
import { m } from '@/paraglide/messages'
import { useLocale } from '@shared/i18n'
import { useAppStore } from '@/stores/appStore'
import { useSharedAuthStore } from '@shared/stores/authStore'
import { queryClient } from '@/plugins/vueQuery'
import { entityKeys } from '@/queries/queryKeys'
import { getEntityApis, getApiClient } from '@/api/entityApis'
import { initializePlugins } from '@/config/collections/collections'
import { permissionForRoute } from '@/config/routePermissions'
import AuthLoginPage from '@ui/components/auth/AuthLoginPage.vue'
import AuthSignupPage from '@ui/components/auth/AuthSignupPage.vue'
import AuthForgotPassword from '@ui/components/auth/AuthForgotPassword.vue'
import DsToastHost from '@ds/hosts/DsToastHost.vue'
import DsDialogHost from '@ds/hosts/DsDialogHost.vue'
import DsLoadingHost from '@ds/hosts/DsLoadingHost.vue'

export default {
  components: { AuthLoginPage, AuthSignupPage, AuthForgotPassword, DsToastHost, DsDialogHost, DsLoadingHost },
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

    const { hasAnyAccess } = usePermissions()
    const hasAdminAccess = computed(() => {
      // Backward compatible: still allow access for users with the legacy
      // `admin` role slug (in case /me hasn't been refreshed yet), or any
      // user with at least one permission. Once the permission catalog
      // covers every admin surface this can drop the slug check.
      if (hasAnyAccess.value) return true
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
        const ds = useLoading()
        if (val) {
          this._dsLoadingHide = ds.show()
        } else if (this._dsLoadingHide) {
          this._dsLoadingHide()
          this._dsLoadingHide = null
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

    if (!this.authRequired && !this.ensureRouteAccess()) {
      return
    }

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
    ensureRouteAccess() {
      if (!this.authEnabled) return true

      const requiredPermission = permissionForRoute(this.$route)
      if (!requiredPermission) return true

      const userInfo = this.sharedAuth.userInfo
      const isSuperuser = Boolean(userInfo?.is_superuser)
      const permissions = userInfo?.permissions ?? []
      if (isSuperuser || permissions.includes(requiredPermission)) return true

      this.$router.replace('/profile')
      return false
    },
    async onAuthCompleted() {
      await this.getAuthData()
      if (!this.ensureRouteAccess()) return
      if (this.hasAdminAccess) {
        await this.loadData()
      }
      // Honor ?return_to=… set by the MCP OAuth bridge (or any other
      // backend redirect to the login page). Only same-origin relative
      // paths are allowed — refuse absolute URLs to avoid open-redirect.
      const params = new URLSearchParams(window.location.search)
      const returnTo = params.get('return_to')
      if (returnTo && returnTo.startsWith('/') && !returnTo.startsWith('//')) {
        window.location.href = returnTo
      }
    },
  },
}
</script>
