<template lang="pug">
.full-height.full-width(:class='{ "no-wrap column": $store.getters.viewMode === "panel" || ai_app }')
  template(v-if='authRequired')
    template(v-if='authCheckInProgress')
      .flex.flex-center.full-height
        q-spinner(size='30px', color='primary')
    template(v-else)
      oauth-login(@auth-completed='onAuthCompleted')
  template(v-else)
    layout-default
  km-error-dialog(v-if='$store.getters.errorMessage?.technicalError')
  template(v-if='env === "development"')
    .fixed-bottom-right.q-pa-sm.row(:style='{ zIndex: 100 }')
</template>

<script>
import { useState } from '@shared'
import { useChroma } from '@shared'
import { useAuth } from '@shared'
import { getCurrentInstance } from 'vue'

export default {
  setup() {
    const loading = useState('globalLoading')
    const { ...collections } = useChroma('collections')
    const { ...rag_tools } = useChroma('rag_tools')
    const { ...retrieval } = useChroma('retrieval')
    const { ...ai_apps } = useChroma('ai_apps')
    const { ...promptTemplates } = useChroma('promptTemplates')
    const { ...evaluation_sets } = useChroma('evaluation_sets')
    const { ...evaluation_jobs } = useChroma('evaluation_jobs')
    const { ...model } = useChroma('model')
    const { ...provider } = useChroma('provider')
    const { ...api_tools } = useChroma('api_tools')
    const { ...api_tool_providers } = useChroma('api_tool_providers')
    const { ...agents } = useChroma('agents')
    const { ...mcp_servers } = useChroma('mcp_servers')
    // const { ...jobs } = useChroma('jobs')

    const auth = useAuth()
    const { appContext } = getCurrentInstance()
    return {
      loading,
      collections,
      rag_tools,
      promptTemplates,
      ai_apps,
      evaluation_sets,
      evaluation_jobs,
      retrieval,
      model,
      provider,
      appContext,
      api_tools,
      api_tool_providers,
      agents,
      mcp_servers,
      // jobs,
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
    await this.$store.dispatch('loadConfig')

    if (this.authRequired) {
      await this.getAuthData()
    }

    if (!this.authRequired) {
      await this.loadData()
    }
  },

  methods: {
    async loadData() {
      await Promise.all([
        this.collections.get(),
        this.rag_tools.get(),
        this.retrieval.get(),
        this.promptTemplates.get(),
        this.ai_apps.get(),
        this.evaluation_sets.get(),
        this.evaluation_jobs.get(),
        this.model.get(),
        this.provider.get(),
        this.api_tools.get(),
        this.api_tool_providers.get(),
        this.agents.get(),
        this.mcp_servers.get(),
        // this.jobs.get(),
      ])
    },
    async onAuthCompleted() {
      this.$store.commit('set', { authenticated: true })
      await this.loadData()
    },
  },
}
</script>
