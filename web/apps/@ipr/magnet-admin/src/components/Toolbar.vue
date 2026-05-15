<template>
  <div class="stack bg-white br-border full-height km-toolbar" :class="isCollapsed ? 'px-xs' : 'px-sm'" data-gap="0" data-test="sidebar-toolbar">
    <template v-if="toolbar == &quot;knowledge&quot;">
      <collections-toolbar-menu />
    </template>
    <template v-if="toolbar == &quot;main&quot;">
      <div class="stack mt-md width-100" data-gap="xs">
        <km-nav-section :label="m.nav_configure()" icon="settings" :items="menu" :collapsed="isSectionCollapsed(&quot;configure&quot;)" :sidebar-collapsed="isCollapsed" :parent-route="parentRoute" @toggle="toggleSection(&quot;configure&quot;)" @navigate="navigate">
          <template v-for="item in menu" :key="item">
            <km-nav-btn :icon="item.icon" :label="item.label" :path="item.path" :parent-route="parentRoute" @navigate="navigate" />
          </template>
        </km-nav-section>
      </div>
      <div class="stack mt-md width-100" data-gap="xs">
        <km-nav-section :label="m.nav_connect()" icon="plug" :items="connectors" :collapsed="isSectionCollapsed(&quot;connect&quot;)" :sidebar-collapsed="isCollapsed" :parent-route="parentRoute" @toggle="toggleSection(&quot;connect&quot;)" @navigate="navigate">
          <template v-for="item in connectors" :key="item">
            <km-nav-btn :icon="item.icon" :label="item.label" :path="item.path" :alternative-paths="item.alternativePaths" :parent-route="parentRoute" @navigate="navigate" />
          </template>
        </km-nav-section>
      </div>
      <div class="stack mt-md" data-gap="xs">
        <km-nav-section :label="m.nav_experimental()" icon="flask" :items="experimental" :collapsed="isSectionCollapsed(&quot;experimental&quot;)" :sidebar-collapsed="isCollapsed" :parent-route="parentRoute" @toggle="toggleSection(&quot;experimental&quot;)" @navigate="navigate">
          <template v-for="item in experimental" :key="item">
            <km-nav-btn :icon="item.icon" :label="item.label" :path="item.path" :parent-route="parentRoute" @navigate="navigate" />
          </template>
        </km-nav-section>
      </div>
      <div class="stack mt-md" data-gap="xs">
        <km-nav-section :label="m.nav_evaluation()" icon="chart" :items="evaluation" :collapsed="isSectionCollapsed(&quot;evaluation&quot;)" :sidebar-collapsed="isCollapsed" :parent-route="parentRoute" @toggle="toggleSection(&quot;evaluation&quot;)" @navigate="navigate">
          <template v-for="item in evaluation" :key="item">
            <km-nav-btn :icon="item.icon" :label="item.label" :path="item.path" :parent-route="parentRoute" @navigate="navigate" />
          </template>
        </km-nav-section>
      </div>
      <div class="stack mt-md" data-gap="xs">
        <km-nav-section :label="m.nav_observability()" icon="eye" :items="observabilityItems" :collapsed="isSectionCollapsed(&quot;observability&quot;)" :sidebar-collapsed="isCollapsed" :parent-route="parentRoute" @toggle="toggleSection(&quot;observability&quot;)" @navigate="navigate">
          <template v-for="item in observabilityItems" :key="item">
            <km-nav-btn :icon="item.icon" :label="item.label" :path="item.path" :parent-route="parentRoute" @navigate="navigate" />
          </template>
        </km-nav-section>
      </div>
      <div class="stack mt-auto mb-sm" data-gap="xs">
        <km-separator />
        <ds-dropdown-menu-root>
          <ds-dropdown-menu-trigger as-child>
            <div class="cluster width-100" data-justify="center" data-wrap="no">
              <km-btn v-if="!isCollapsed" class="width-100 border-radius-6" icon="settings" icon-size="16px" size="sm" flat :label="m.nav_system()" interaction-tone="brand" label-class="km-title" :class="isSystemRouteActive ? &quot;text-primary bg-primary-bg&quot; : &quot;&quot;" />
              <km-btn v-else icon="settings" icon-size="18px" flat interaction-tone="brand" :tooltip="m.nav_system()" :class="isSystemRouteActive ? &quot;text-primary bg-primary-bg&quot; : &quot;&quot;" />
            </div>
          </ds-dropdown-menu-trigger>
          <ds-dropdown-menu-content side="right" align="end" :side-offset="8" data-test="system-menu">
            <ds-dropdown-menu-label>{{ m.nav_system() }}</ds-dropdown-menu-label>
            <ds-dropdown-menu-item v-for="item in system" :key="item.path" :class="matchesPath(item.path) ? 'text-primary bg-primary-bg' : ''" @select="navigate(item.path)">
              <km-glyph :name="item.icon" size="14px" :tone="matchesPath(item.path) ? 'brand' : undefined" />
              <span :class="matchesPath(item.path) ? 'text-primary' : ''">{{ item.label }}</span>
            </ds-dropdown-menu-item>
          </ds-dropdown-menu-content>
        </ds-dropdown-menu-root>
      </div>
    </template>
  </div>
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
        icon: 'magic',
        path: 'ai-apps',
      },
    ]

    const evaluation = [
      {
        label: m.nav_testSets(),
        icon: 'table-list',
        path: 'evaluation-sets',
      },
      {
        label: m.nav_evaluations(),
        icon: 'clipboard-check',
        path: 'evaluation-jobs',
      },
    ]

    const menu = [
      {
        label: m.nav_agents(),
        icon: 'robot',
        path: 'agents',
      },
      {
        label: m.nav_promptTemplates(),
        icon: 'chat',
        path: 'prompt-templates',
      },
      {
        label: m.nav_ragTools(),
        icon: 'file-question',
        path: 'rag-tools',
        dev: true,
      },
      {
        label: m.nav_retrievalTools(),
        icon: 'file-question',
        path: 'retrieval',
      },
    ]

    const connectors = [
      {
        label: m.nav_apiTools(),
        icon: 'swap',
        path: 'api-servers',
      },
      {
        label: m.nav_mcpTools(),
        icon: 'server',
        path: 'mcp',
      },
      {
        label: m.nav_knowledgeSources(),
        icon: 'book',
        path: 'knowledge-providers',
        alternativePaths: ['knowledge-sources'],
      },
      {
        label: m.nav_models(),
        icon: 'graph',
        path: 'model-providers',
      },
      {
        label: m.nav_apiKeys(),
        icon: 'lock',
        path: 'api-keys',
      },
    ]

    const observabilityItems = [
      {
        label: m.nav_ragQueries(),
        icon: 'file-question',
        path: 'usage/rag',
      },
      {
        label: m.nav_agents(),
        icon: 'robot',
        path: 'usage/agent',
      },
      {
        label: m.nav_llmCalls(),
        icon: 'chat',
        path: 'usage/llm',
      },
      {
        label: m.nav_traces(),
        icon: 'steps',
        path: 'observability-traces',
      },
    ]

    const system = [
      {
        label: m.nav_jobs(),
        icon: 'history',
        path: 'jobs',
      },
      {
        label: m.nav_fileStorage(),
        icon: 'storage',
        path: 'files',
      },
      {
        label: m.nav_importExport(),
        icon: 'settings',
        path: 'settings',
      },
    ]

    const experimental = [
      {
        label: m.nav_aiApps(),
        icon: 'magic',
        path: 'ai-apps',
      },
      {
        label: m.nav_knowledgeGraph(),
        icon: 'graph',
        path: 'knowledge-graph',
      },
      {
        label: m.nav_deepResearch(),
        icon: 'search-chart',
        path: 'deep-research/configs',
      },
      {
        label: m.nav_deepResearchRuns(),
        icon: 'play',
        path: 'deep-research/runs',
      },
      {
        label: m.nav_noteTaker(),
        icon: 'clipboard-list',
        path: 'note-taker',
      },
      {
        label: m.nav_promptQueue(),
        icon: 'list',
        path: 'prompt-queue',
      },
      {
        label: 'OAuth Clients (MCP)',
        icon: 'fas fa-key',
        path: 'oauth-clients',
      }
    ]

    const dev = [
      {
        label: m.nav_templateGroups(),
        icon: 'stamp',
        path: 'prompt-template-groups',
        dev: true,
      },
      {
        label: m.common_create(),
        icon: 'add-square',
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
      // Full current pathname. Downstream nav components match via
      // `parentRoute === '/' + item.path` OR
      // `parentRoute.startsWith('/' + item.path + '/')`, so multi-segment
      // slugs (`deep-research/runs`, `usage/rag`) light up on detail routes.
      return this.$route?.path ?? ''
    },
    isAdmin() {
      return this.$route.meta?.admin
    },
    isSystemRouteActive() {
      return this.system.some((item) => this.matchesPath(item.path))
    },
  },
  watch: {},
  created() {},
  mounted() {},
  methods: {
    matchesPath(itemPath) {
      if (!this.parentRoute || !itemPath) return false
      const target = `/${itemPath}`
      return this.parentRoute === target || this.parentRoute.startsWith(`${target}/`)
    },
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
<style scoped>
.km-toolbar {
  overflow-block: auto;
  inline-size: 100%;
  box-sizing: border-box;
}
</style>
