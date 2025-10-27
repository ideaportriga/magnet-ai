<template lang="pug">
q-layout.bg-light.full-height.overflow-hidden(view='hHh lpR fFf')
  q-header
    .row.bg-primary.items-center.no-wrap(style='height: 50px', data-test='header')
      //- div {{$route.query}}
      .col-auto.full-height.bg-white.br-border.km-toolbar.q-px-8.column.nowrap.bb-border(style='width: 200px')
        .row.q-my-auto.no-wrap.q-gap-8.cursor-pointer.items-center
          km-btn(:icon='"fas fa-bars"', @click='drawerLeft = !drawerLeft', iconColor='text-gray', iconSize='16px', flat)
        .row.q-my-auto.no-wrap.q-gap-8.cursor-pointer.items-center.full-height.bl-border.relative-position
          .q-ml-xs
          km-icon(:name='"magnet"', width='20', height='23')
          .row
            .km-heading-6.logo-text(style='font-size: 18px', @click='navigate("/")') Magnet AI
            .absolute(style='bottom: 0px; right: 6px')
              .logo-text {{ environment }}
      //- .col-auto.text-white.km-body.q-mx-md.km-underline(@click='showBackButton ? navigate(parentRoute) : null') 
      //-   .row.items-center.q-gap-8
      //-     q-icon.col-auto.q-pt-2(v-if='showBackButton', name='fas fa-chevron-left', color='text-secondary', size='12px')
      //-     div {{ route.meta?.pageLabel }}:
      template(v-if='showBackButton')
        .col-auto.text-white.km-body.q-mx-md.km-underline(@click='navigate(parentRoute)') 
          .row.items-center.q-gap-8
            q-icon.col-auto.q-pt-2(v-if='showBackButton', name='fas fa-chevron-left', color='text-secondary', size='12px')
            div {{ route.meta?.pageLabel }}:
      template(v-else)
        .col-auto.text-white.km-body.q-mx-md
          .row.items-center.q-gap-8
            div {{ route.meta?.pageLabel }}:
      template(v-if='route.name === "ConfigurationItems"')
        configuration-header
      template(v-if='route.name === "PromptTemplatesItem"')
        prompts-header
      template(v-if='route.name == "CollectionDetail" || route.name == "CollectionItems"')
        collections-header
      template(v-if='route.name === "AIAppDetail" || route.name === "AIAppTabsDetail"')
        ai-apps-header
      template(v-if='route.name === "EvaluationSetDetails"')
        evaluation-sets-header
      template(v-if='route.name === "RetrievalItems"')
        retrieval-header
      template(v-if='route.name === "AssistantItems"')
        assistant-tools-header
      template(v-if='route.name === "ModelItems"')
        model-config-header
      //- template(v-if='route.name === "ApiToolsDetails"')
      //-   api-tools-header
      template(v-if='route.name === "AgentDetail" || route.name == "AgentTopicDetail" || route.name == "AgentTopicActionDetail"')
        agents-header
      template(v-if='route.name === "ObservabilityTracesDetail"')
        observability-traces-header
      template(v-if='route.name === "Conversation"')
        conversation-header
      template(v-if='route.name === "McpDetail"')
        mcp-header
      template(v-if='route.name === "ApiServersDetail" || route.name === "ApiToolsDetails"')
        api-servers-header
      template(v-if='route.name === "ModelProvidersDetails"')
        model-providers-header
      template(v-if='route.name === "KnowledgeProvidersDetails"')
        knowledge-providers-header
  q-drawer.bg-primary.text-white(v-model='drawerLeft', show-if-above, :width='200', :breakpoint='1350')
    toolbar

  q-page-container
    .km-view-height
      router-view(v-if='!loading')
km-popup-confirm(
  :visible='showLeaveConfirm',
  confirmButtonLabel='Save changes',
  confirmButtonLabel2='Don\'t save changes',
  confirmButtonType2='secondary',
  cancelButtonLabel='Cancel',
  notificationIcon='fas fa-triangle-exclamation',
  @confirm='saveChanges',
  @cancel='cancelLeave',
  @confirm2='confirmLeave'
)
  .row.item-center.justify-center.km-heading-7.q-mb-md Unsaved Changes
  .row.text-center.justify-center You have unsaved changes here. Please choose what you would like to do.
</template>

<script>
import { useState } from '@shared'
import { ref } from 'vue'
import { useStore } from 'vuex'

export default {
  setup() {
    const loading = useState('globalLoading')
    const store = useStore()
    const environment = store.getters.config.environment

    return {
      loading,
      drawerLeft: ref(true),
      environment,
    }
  },
  computed: {
    showBackButton() {
      if (this.route.name === 'Conversation') return false
      if (this.route.name === 'McpToolsDetail') return false
      if (this.route.name === 'EvaluationCompare') return true
      if (this.route.params.id) return true
      return false
    },
    showLeaveConfirm() {
      return this.$store.getters.showLeaveConfirm
    },
    nextRoute() {
      return this.$store.getters.nextRoute
    },
    parentRoute() {
      const segments = this.route.path.split('/')
      if (segments[1] === 'observability') {
        //return `/${segments[1]}`
        return `/${segments[1]}/${segments[2]}`
      }
      if (segments[1] === 'evaluation') {
        return `/evaluation-jobs`
      }
      if (segments[1] === 'knowledge-sources') {
        const providerSystemName = this.$store.getters.knowledge?.provider_system_name
        return providerSystemName ? `/knowledge-providers/${providerSystemName}` : `/${segments[1]}`
      }
      return `/${segments[1]}`
    },
    route() {
      return this.$route
    },
    routeChromaEntity() {
      return this.route.meta?.entity
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
  created() {},
  methods: {
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`${path}`)
      }
    },
    confirmLeave() {
      if (this.nextRoute) {
        if (this.routeChromaEntity === 'rag_tools') {
          this.$store.commit('revertRagChanges')
        }

        if (this.routeChromaEntity === 'retrieval') {
          this.$store.commit('revertRetrievalChanges')
        }

        if (this.routeChromaEntity === 'ai_apps') {
          this.$store.commit('revertAIAppChanges')
        }

        if (this.routeChromaEntity === 'evaluation_sets') {
          this.$store.commit('revertEvaluationSetChanges')
        }

        if (this.routeChromaEntity === 'promptTemplates') {
          this.$store.commit('revertPromptTemplateChanges')
        }

        if (this.routeChromaEntity === 'agents') {
          this.$store.commit('revertAgentDetailChanges')
        }

        if (this.routeChromaEntity === 'model') {
          this.$store.commit('modelConfig/revertEntity')
        }

        if (this.routeChromaEntity === 'provider') {
          this.$store.commit('revertProviderChanges')
        }

        this.$router.push(this.nextRoute)
      }
    },
    async saveChanges() {
      if (this.routeChromaEntity === 'rag_tools') {
        await this.$store.dispatch('saveRag')
      }

      if (this.routeChromaEntity === 'retrieval') {
        await this.$store.dispatch('saveRetrieval')
      }

      if (this.routeChromaEntity === 'ai_apps') {
        await this.$store.dispatch('saveAIApp')
      }

      if (this.routeChromaEntity === 'evaluation_sets') {
        await this.$store.dispatch('saveEvaluationSet')
      }

      if (this.routeChromaEntity === 'promptTemplates') {
        await this.$store.dispatch('savePromptTemplate')
      }

      if (this.routeChromaEntity === 'agents') {
        this.$store.dispatch('saveAgentDetail')
      }

      if (this.routeChromaEntity === 'model') {
        this.$store.dispatch('modelConfig/saveEntity')
      }

      if (this.routeChromaEntity === 'mcp_servers') {
        this.$store.dispatch('saveMcpServer')
      }

      if (this.routeChromaEntity === 'api_servers') {
        this.$store.dispatch('saveApiServer')
      }

      if (this.routeChromaEntity === 'provider') {
        this.$store.dispatch('saveProvider')
      }

      if (this.nextRoute) {
        this.$router.push(this.nextRoute)
      }
      // this.confirmLeave()
    },
    cancelLeave() {
      this.$store.commit('hidePopup')
    },
  },
}
</script>

<style lang="stylus">
.km-underline:hover {
  text-decoration: underline;
  cursor: pointer;
}

.km-view-height {
    max-height: calc(100vh - 50px) !important;
    height: calc(100vh - 50px) !important;
}
</style>
