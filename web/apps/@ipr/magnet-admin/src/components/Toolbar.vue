<template lang="pug">
.bg-white.br-border.column.no-wrap.full-height.km-toolbar(:class="isCollapsed ? 'q-px-4' : 'q-px-8'")
  template(v-if='toolbar == "knowledge"')
    collections-toolbar-menu

  template(v-if='toolbar == "main"')
    .column.q-mt-12.width-100.q-gap-6
      km-nav-section(
        :label='m.nav_configure()',
        icon='fas fa-cogs',
        :items='menu',
        :collapsed='isSectionCollapsed("configure")',
        :sidebarCollapsed='isCollapsed',
        :parentRoute='parentRoute',
        @toggle='toggleSection("configure")',
        @navigate='navigate'
      )
        template(v-for='item in menu')
          km-nav-btn(:icon='item.icon', :label='item.label', :path='item.path', :parentRoute='parentRoute', @navigate='navigate')

    .column.q-mt-16.width-100.q-gap-6
      km-nav-section(
        :label='m.nav_connect()',
        icon='fas fa-plug',
        :items='connectors',
        :collapsed='isSectionCollapsed("connect")',
        :sidebarCollapsed='isCollapsed',
        :parentRoute='parentRoute',
        @toggle='toggleSection("connect")',
        @navigate='navigate'
      )
        template(v-for='item in connectors')
          km-nav-btn(
            :icon='item.icon',
            :label='item.label',
            :path='item.path',
            :alternativePaths='item.alternativePaths',
            :parentRoute='parentRoute',
            @navigate='navigate'
          )

    .column.q-mt-16.q-gap-6
      km-nav-section(
        :label='m.nav_experimental()',
        icon='fas fa-flask',
        :items='experimental',
        :collapsed='isSectionCollapsed("experimental")',
        :sidebarCollapsed='isCollapsed',
        :parentRoute='parentRoute',
        @toggle='toggleSection("experimental")',
        @navigate='navigate'
      )
        template(v-for='item in experimental')
          km-nav-btn(:icon='item.icon', :label='item.label', :path='item.path', :parentRoute='parentRoute', @navigate='navigate')

    .column.q-mt-16.q-gap-6
      km-nav-section(
        :label='m.nav_evaluation()',
        icon='fas fa-chart-column',
        :items='evaluation',
        :collapsed='isSectionCollapsed("evaluation")',
        :sidebarCollapsed='isCollapsed',
        :parentRoute='parentRoute',
        @toggle='toggleSection("evaluation")',
        @navigate='navigate'
      )
        template(v-for='item in evaluation')
          km-nav-btn(:icon='item.icon', :label='item.label', :path='item.path', :parentRoute='parentRoute', @navigate='navigate')

    .column.q-mt-16.q-gap-6
      km-nav-section(
        :label='m.nav_observability()',
        icon='fas fa-eye',
        :items='observabilityItems',
        :collapsed='isSectionCollapsed("observability")',
        :sidebarCollapsed='isCollapsed',
        :parentRoute='parentRoute',
        @toggle='toggleSection("observability")',
        @navigate='navigate'
      )
        template(v-for='item in observabilityItems')
          km-nav-btn(:icon='item.icon', :label='item.label', :path='item.path', :parentRoute='parentRoute', @navigate='navigate')

    .column.q-mt-auto.q-gap-6.q-mb-8
      km-separator
      //- System
      .width-100.relative-position
        km-btn.width-100.border-radius-6(
          v-if='!isCollapsed',
          icon='fas fa-gear',
          iconSize='16px',
          size='sm',
          flat,
          iconColor='icon',
          :label='m.nav_system()',
          hoverColor='primary',
          hoverBg='primary-bg',
          labelClass='km-title',
          :class='isSystemRouteActive ? "text-primary bg-primary-bg" : ""'
        )
        km-btn.width-100.border-radius-6.justify-center(
          v-else,
          icon='fas fa-gear',
          iconSize='18px',
          size='sm',
          flat,
          iconColor='icon',
          hoverColor='primary',
          hoverBg='primary-bg',
          :tooltip='m.nav_system()',
          :class='isSystemRouteActive ? "text-primary bg-primary-bg" : ""'
        )
        q-menu(anchor='top right', self='top left', :offset='[8, 0]')
          q-list(dense, style='min-width: 180px')
            q-item-label.text-secondary.km-button-xs-text.text-uppercase(header) {{ m.nav_system() }}
            q-item.km-nav-popup-item(
              v-for='item in system',
              :key='item.path',
              clickable,
              v-close-popup,
              :active='parentRoute === "/" + item.path',
              active-class='text-primary bg-primary-bg',
              @click='navigate(item.path)'
            )
              q-item-section(avatar, style='min-width: 28px; padding-right: 4px')
                q-icon(:name='item.icon', size='14px', :color='parentRoute === "/" + item.path ? "primary" : "icon"')
              q-item-section
                span(:class='parentRoute === "/" + item.path ? "text-primary" : ""') {{ item.label }}
      //- Help and Profile moved to header (LayoutDefault.vue)
</template>

<script lang="ts">
import { computed } from 'vue'
import { useAuth } from '@shared'
import { useSharedAuthStore } from '@shared/stores/authStore'
import { useSidebarState } from '@/composables/useSidebarState'
import { m } from '@/paraglide/messages'

export default {
  setup() {
    const { logout } = useAuth()
    const { isCollapsed, toggleSection, isSectionCollapsed } = useSidebarState()

    const authStore = useSharedAuthStore()
    const userInfo = computed(() => authStore.userInfo)
    const userDisplayName = computed(() => {
      const u = userInfo.value
      if (!u) return ''
      return u.name || u.email || u.preferred_username || ''
    })
    const userDisplayEmail = computed(() => {
      const u = userInfo.value
      if (!u) return ''
      return u.email || u.preferred_username || ''
    })

    const assemble = [
      {
        label: m.nav_aiApps(),
        icon: 'fas fa-wand-magic-sparkles',
        path: 'ai-apps',
      },
    ]

    const evaluation = [
      {
        label: m.nav_testSets(),
        icon: 'fas fa-table-list',
        path: 'evaluation-sets',
      },
      {
        label: m.nav_evaluations(),
        icon: 'fas fa-clipboard-check',
        path: 'evaluation-jobs',
      },
    ]

    const menu = [
      {
        label: m.nav_agents(),
        icon: 'fa fa-robot',
        path: 'agents',
      },
      {
        label: m.nav_promptTemplates(),
        icon: 'fa fa-comment-dots',
        path: 'prompt-templates',
      },
      {
        label: m.nav_ragTools(),
        icon: 'fas fa-file-circle-question',
        path: 'rag-tools',
        dev: true,
      },
      {
        label: m.nav_retrievalTools(),
        icon: 'fas fa-file-circle-question',
        path: 'retrieval',
      },
    ]

    const connectors = [
      {
        label: m.nav_apiTools(),
        icon: 'fas fa-arrow-right-arrow-left',
        path: 'api-servers',
      },
      {
        label: m.nav_mcpTools(),
        icon: 'fas fa-server',
        path: 'mcp',
      },
      {
        label: m.nav_knowledgeSources(),
        icon: 'fas fa-book',
        path: 'knowledge-providers',
        alternativePaths: ['knowledge-sources'],
      },
      {
        label: m.nav_models(),
        icon: 'fas fa-circle-nodes',
        path: 'model-providers',
      },
      {
        label: m.nav_apiKeys(),
        icon: 'fas fa-lock',
        path: 'api-keys',
      },
    ]

    const observabilityItems = [
      {
        label: m.nav_ragQueries(),
        icon: 'fas fa-file-circle-question',
        path: 'usage/rag',
      },
      {
        label: m.nav_agents(),
        icon: 'fa fa-robot',
        path: 'usage/agent',
      },
      {
        label: m.nav_llmCalls(),
        icon: 'fa fa-comment-dots',
        path: 'usage/llm',
      },
      {
        label: m.nav_traces(),
        icon: 'fas fa-shoe-prints',
        path: 'observability-traces',
      },
    ]

    const system = [
      {
        label: m.nav_jobs(),
        icon: 'fas fa-clock-rotate-left',
        path: 'jobs',
      },
      {
        label: m.nav_fileStorage(),
        icon: 'fas fa-hard-drive',
        path: 'files',
      },
      {
        label: m.nav_importExport(),
        icon: 'fas fa-sliders',
        path: 'settings',
      },
    ]

    const experimental = [
      {
        label: m.nav_aiApps(),
        icon: 'fas fa-wand-magic-sparkles',
        path: 'ai-apps',
      },
      {
        label: m.nav_knowledgeGraph(),
        icon: 'o_hub',
        path: 'knowledge-graph',
      },
      {
        label: m.nav_deepResearch(),
        icon: 'fas fa-magnifying-glass-chart',
        path: 'deep-research/configs',
      },
      {
        label: m.nav_deepResearchRuns(),
        icon: 'fas fa-play',
        path: 'deep-research/runs',
      },
      {
        label: m.nav_noteTaker(),
        icon: 'fas fa-clipboard-list',
        path: 'note-taker',
      },
      {
        label: m.nav_promptQueue(),
        icon: 'fas fa-list-ul',
        path: 'prompt-queue',
      }
    ]

    const dev = [
      {
        label: m.nav_templateGroups(),
        icon: 'fas fa-stamp',
        path: 'prompt-template-groups',
        dev: true,
      },
      {
        label: m.common_create(),
        icon: 'far fa-plus-square',
        path: 'create',
        dev: true,
      },
    ]

    return {
      m,
      menu,
      dev,
      logout,
      assemble,
      connectors,
      evaluation,
      observabilityItems,
      system,
      experimental,
      isCollapsed,
      toggleSection,
      isSectionCollapsed,
      userInfo,
      userDisplayName,
      userDisplayEmail,
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
    isSystemRouteActive() {
      return this.system.some((item) => this.parentRoute === '/' + item.path)
    },
  },
  watch: {},
  created() {},
  mounted() {},
  methods: {
    navigateToProfile(path) {
      this.$router?.push(path)
    },
    openHelp() {
      window.open('/help/docs/en/', '_blank')
    },
    navigate(path = '') {
      if (path === '__help__') {
        this.openHelp()
        return
      }
      if (this.$route?.path !== `/${path}`) {
        this.$router?.push(`/${path}`)
      }
    },
  },
}
</script>
<style lang="stylus" scoped>

.km-toolbar {
  overflow-y: auto;
  width: 100%;
  box-sizing: border-box;
}

.km-toolbar::-webkit-scrollbar {
    width: 4px;
}
</style>
