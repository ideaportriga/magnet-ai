<template>
  <div
    :key="locale"
    class="full-height full-width stack"
    data-gap="0"
  >
    <template v-if="auth.authCheckInProgress">
      <div class="flex flex-center full-height">
        <km-loader
          size="30px"
        />
      </div>
    </template>
    <template v-else-if="auth.authRequired &amp;&amp; !isPublicRoute">
      <login-page />
    </template>
    <template v-else>
      <template v-if="appType === &quot;agent&quot;">
        <agent-container />
      </template>
      <template v-else>
        <router-view />
      </template>
    </template>
    <km-error-dialog v-if="mainStore.errorMessage?.technicalError" />
    <template v-if="env === &quot;development&quot;">
      <div
        class="fixed-bottom-right p-sm cluster"
        :style="{ zIndex: 100 }"
      />
    </template>
    <ds-toast-host />
    <ds-dialog-host />
    <ds-loading-host />
  </div>
</template>

<script>
import { computed, getCurrentInstance } from 'vue'
import { useLoading } from '@ds/composables/useLoading'
import { storeToRefs } from 'pinia'
import { useRoute } from 'vue-router'
import { useMainStore, useRagTools, useCollections, useRetrieval, useAiApps, usePromptTemplates, useAgents, useAuth, useModel } from '@/pinia'
import { useLocale } from '@shared/i18n'
import LoginPage from '@/pages/LoginPage.vue'
import DsToastHost from '@ds/hosts/DsToastHost.vue'
import DsDialogHost from '@ds/hosts/DsDialogHost.vue'
import DsLoadingHost from '@ds/hosts/DsLoadingHost.vue'

export default {
  components: { LoginPage, DsToastHost, DsDialogHost, DsLoadingHost },
  setup() {
    const mainStore = useMainStore()
    const ragTools = useRagTools()
    const collections = useCollections()
    const retrieval = useRetrieval()
    const aiApps = useAiApps()
    const promptTemplates = usePromptTemplates()
    const agents = useAgents()
    const auth = useAuth()
    const model = useModel()
    const route = useRoute()

    const { authRequired } = storeToRefs(auth)
    const { appContext } = getCurrentInstance()

    const isPublicRoute = computed(() => route.meta?.public === true)

    const { locale } = useLocale()

    return {
      locale,
      appContext,
      authRequired,
      isPublicRoute,
      mainStore,
      ragTools,
      collections,
      retrieval,
      aiApps,
      promptTemplates,
      agents,
      auth,
      model,
    }
  },
  computed: {
    loading() {
      return this.mainStore.globalLoading
    },
    openTest() {
      return true
    },
    appType() {
      if (this.$route.query.agent) return 'agent'
      return 'ai_app'
    },
  },
  watch: {
    loading: {
      immediate: true,
      handler(val) {
        const ds = useLoading()
        // Guard against double-show: if a previous show() is still pending
        // and `val` flips back to true (e.g., HMR re-attach, async race),
        // we'd otherwise leak a counter increment that the overlay store
        // never decrements. Only show when no active hide handle exists.
        if (val && !this._dsLoadingHide) {
          this._dsLoadingHide = ds.show()
        } else if (!val && this._dsLoadingHide) {
          this._dsLoadingHide()
          this._dsLoadingHide = null
        }
      },
    },
    authRequired: {
      handler(val) {
        if (!val) {
          this.loadData()
        }
      },
    },
  },
  beforeUnmount() {
    // Release any pending overlay request when the root unmounts (HMR,
    // tab close). Without this the counter would stay positive forever.
    if (this._dsLoadingHide) {
      this._dsLoadingHide()
      this._dsLoadingHide = null
    }
  },
  async created() {
    // Force-clear any residual overlay state from a prior HMR cycle / failed
    // boot. Without this, a stuck pending counter from a previous mount can
    // keep the global spinner visible even after a clean reload.
    useLoading().clear()

    await this.mainStore.loadConfig()

    if (!this.authRequired) {
      await this.loadData()
    }
  },
  methods: {
    async loadData() {
      await this.$router.isReady()

      if (this.appType === 'ai_app') {
        await this.aiApps.getApp(this.$route.query.ai_app)
      } else if (this.appType === 'agent') {
        await this.aiApps.getAgent(this.$route.query.agent)
      }
    },
  },
}
</script>
