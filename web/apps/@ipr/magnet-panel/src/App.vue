<template lang="pug">
.full-height.full-width.no-wrap.column
  template(v-if='auth.authCheckInProgress')
    .flex.flex-center.full-height
      q-spinner(size='30px', color='primary')
  template(v-else-if='auth.authRequired && !isPublicRoute')
    login-page
  template(v-else)
    template(v-if='appType === "agent"')
      agent-container
    template(v-else)
      router-view
  km-error-dialog(v-if='mainStore.errorMessage?.technicalError')
  template(v-if='env === "development"')
    .fixed-bottom-right.q-pa-sm.row(:style='{ zIndex: 100 }')
</template>

<script>
import { computed, getCurrentInstance } from 'vue'
import { storeToRefs } from 'pinia'
import { useRoute } from 'vue-router'
import { useMainStore, useRagTools, useCollections, useRetrieval, useAiApps, usePromptTemplates, useAgents, useAuth, useModel } from '@/pinia'
import LoginPage from '@/pages/LoginPage.vue'

export default {
  components: { LoginPage },
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

    return {
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
        if (val) {
          this.$q.loading.show()
        } else {
          this.$q.loading.hide()
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
  async created() {
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
