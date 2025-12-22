<template lang="pug">
.bg-white.br-border.q-px-8.column.no-wrap.full-height.km-toolbar
  template(v-if='toolbar == "knowledge"') 
    collections-toolbar-menu

  template(v-if='toolbar == "main"')
    .column.q-mt-12.width-100.q-gap-6.border-radius-6
      .km-button-xs-text.text-secondary.text-uppercase Visualize
        km-separator
      template(v-for='item in assemble')
        km-nav-btn(:icon='item.icon', :label='item.label', :path='item.path', :parentRoute='parentRoute', @navigate='navigate')
    .column.q-mt-24.width-100.q-gap-6.border-radius-6
      .km-button-xs-text.text-secondary.text-uppercase Configure
        km-separator
      template(v-for='item in menu')
        km-nav-btn(:icon='item.icon', :label='item.label', :path='item.path', :parentRoute='parentRoute', @navigate='navigate')
    .column.q-mt-24.width-100.q-gap-6.border-radius-6
      .km-button-xs-text.text-secondary.text-uppercase Connect
        |
        km-separator
      template(v-for='item in connectors')
        km-nav-btn(
          :icon='item.icon',
          :label='item.label',
          :path='item.path',
          :alternativePaths='item.alternativePaths',
          :parentRoute='parentRoute',
          @navigate='navigate'
        )
    .column.q-mt-md.q-gap-6.border-radius-6
      .row
        q-chip.km-button-text.q-mb-xs(text-color='primary', color='primary-light', size='sm') Experimental
      template(v-for='item in experimental')
        km-nav-btn(:icon='item.icon', :label='item.label', :path='item.path', :parentRoute='parentRoute', @navigate='navigate')
    .column.q-mt-24.q-gap-6
      .km-button-xs-text.text-secondary.text-uppercase Test & Monitor
        km-separator
      km-btn-expand-down(:item='{ label: "Evaluations", icon: "fas fa-chart-column", path: "evaluation-sets" }', :subItems='evaluation')
      km-btn-expand-down(:item='{ label: "Usage", icon: "fas fa-chart-column", path: "usage" }', :subItems='dashboard')
      template(v-for='item in observability')
        km-nav-btn(:icon='item.icon', :label='item.label', :path='item.path', :parentRoute='parentRoute', @navigate='navigate')
    .column.q-mt-24.q-gap-6
      .km-button-xs-text.text-secondary.text-uppercase Resources
        km-separator
      km-btn(
        icon='fa-regular fa-circle-question',
        iconSize='16px',
        size='sm',
        flat,
        @click='openHelp',
        iconColor='icon',
        label='Help',
        hoverColor='primary',
        hoverBg='primary-bg',
        labelClass='km-title'
      )
    .column.q-mt-auto.q-gap-6
      km-btn(
        icon='fas fa-sign-out-alt',
        iconSize='16px',
        size='sm',
        flat,
        @click='logout',
        iconColor='icon',
        label='Log out',
        hoverColor='primary',
        hoverBg='primary-bg',
        labelClass='km-title'
      )
</template>

<script lang="ts">
import { useAuth } from '@shared'
import { useStore } from 'vuex'

const assemble = [
  {
    label: 'AI Apps',
    icon: 'fas fa-wand-magic-sparkles',
    path: 'ai-apps',
  },
]

const evaluation = [
  {
    label: 'Test Sets',
    icon: 'fas fa-table-list',
    path: 'evaluation-sets',
  },
  {
    label: 'Evaluations',
    icon: 'fas fa-clipboard-check',
    path: 'evaluation-jobs',
  },
]

const dashboard = [
  {
    label: 'RAG Queries',
    icon: 'fas fa-file-circle-question',
    path: 'usage/rag',
  },
  {
    label: 'Agents',
    icon: 'fa fa-robot',
    path: 'usage/agent',
  },
  {
    label: 'LLM Calls',
    icon: 'fa fa-comment-dots',
    path: 'usage/llm',
  },
]

const menu = [
  {
    label: 'Agents',
    icon: 'fa fa-robot',
    path: 'agents',
  },
  {
    label: 'Prompt templates',
    icon: 'fa fa-comment-dots',
    path: 'prompt-templates',
  },
  {
    label: 'RAG Tools',
    icon: 'fas fa-file-circle-question',
    path: 'rag-tools',
    dev: true,
  },
  {
    label: 'Retrieval Tools',
    icon: 'fas fa-file-circle-question',
    path: 'retrieval',
  },
]

const connectors = [
  {
    label: 'API Tools',
    icon: 'fas fa-arrow-right-arrow-left',
    path: 'api-servers',
  },

  {
    label: 'MCP Tools',
    icon: 'fas fa-server',
    path: 'mcp',
  },
  // {
  //   label: 'Knowledge sources',
  //   icon: 'fas fa-book',
  //   path: 'knowledge-sources',
  // },
  {
    label: 'Knowledge sources',
    icon: 'fas fa-book',
    path: 'knowledge-providers',
    alternativePaths: ['knowledge-sources'],
  },
  // {
  //   label: 'Models',
  //   icon: 'fas fa-circle-nodes',
  //   path: 'model',
  // },
  {
    label: 'Models',
    icon: 'fas fa-circle-nodes',
    // icon: 'fas fa-network-wired',
    path: 'model-providers',
  },
  {
    label: 'API Keys',
    icon: 'fas fa-lock',
    path: 'api-keys',
  },
]

const observability = [
  {
    label: 'Traces',
    icon: 'fas fa-shoe-prints',
    path: 'observability-traces',
  },
  {
    label: 'Jobs',
    icon: 'fas fa-clock-rotate-left',
    path: 'jobs',
  },
]

const experimental = [
  {
    label: 'Knowledge graph',
    icon: 'o_hub',
    path: 'knowledge-graph',
  },
  {
    label: 'Deep Research',
    icon: 'fas fa-magnifying-glass-chart',
    path: 'deep-research/configs',
  },
  {
    label: 'Deep Research Runs',
    icon: 'fas fa-play',
    path: 'deep-research/runs',
  },
]

const dev = [
  {
    label: 'Template groups',
    icon: 'fas fa-stamp',
    path: 'prompt-template-groups',
    dev: true,
  },
  {
    label: 'Create',
    icon: 'far fa-plus-square',
    path: 'create',
    dev: true,
  },
]

export default {
  setup() {
    const { logout } = useAuth()
    const store = useStore()
    return {
      menu,
      dev,
      logout,
      assemble,
      connectors,
      evaluation,
      dashboard,
      observability,
      experimental,
      store,
    }
  },
  computed: {
    routerMetaName() {
      return this.$route.name || ''
    },
    toolbar() {
      return 'main'
    },
    parentRoute() {
      const segments = this.$route?.path?.split('/')
      return `/${segments?.[1]}`
    },
    isAdmin() {
      return this.$route.meta?.admin
    },
  },
  watch: {},
  created() {},
  mounted() {},
  methods: {
    openHelp() {
      window.open('/help/docs/en/', '_blank')
    },
    navigate(path = '') {
      if (this.$route?.path !== `/${path}`) {
        this.$router?.push(`/${path}`)
      }
    },
  },
}
</script>
<style lang="stylus" scoped>

.km-toolbar {
  overflow: scroll;
  width: 100%;
  box-sizing: border-box;
}

.km-toolbar::-webkit-scrollbar {
    width: 4px;
}
</style>
